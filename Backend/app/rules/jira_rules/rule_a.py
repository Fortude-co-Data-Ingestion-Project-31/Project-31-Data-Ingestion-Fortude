from datetime import datetime, timezone


SEVERITY_LEVELS = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
#keywords for function classification. Priority order is M3 program code, then keywords, then reporter department.
FUNCTION_KEYWORDS = {
    "Finance": ["invoice", "finance", "gl ", "ledger", "payment", "accounting"],
    "Warehouse": ["warehouse", "inventory", "stock", "pick", "putaway"],
    "Order": ["order", "purchase", "sales order", "delivery", "shipment"],
    "Production": ["production", "manufacturing", "work order", "assembly", "quality"],
    "HR": ["employee", "payroll", "hr ", "absence"],
}


def _parse_ts(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            continue
    return None


# ---------------------------------------------------------------------------
# A-01 Validate on arrival
# ---------------------------------------------------------------------------
# Reads the mandatory fields the mapper produced. It does not delete the
# ticket from the pipeline - it only marks it as incomplete so a downstream
# writer can route it to the clarification queue.
# ---------------------------------------------------------------------------

def rule_a_01_validate_on_arrival(ticket):
    missing = []

    if not ticket.get("ticket_key"):
        missing.append("ticket_key")
    if not ticket.get("description"):
        missing.append("description")
    if not ticket.get("created_at"):
        missing.append("created_at")
    if not ticket.get("client_id"):
        missing.append("client_id")
    if not ticket.get("environment"):
        missing.append("environment")

    ticket["derived"]["a01_missing_fields"] = missing
    ticket["derived"]["a01_valid"] = len(missing) == 0
    return ticket


# ---------------------------------------------------------------------------
# A-02 Classify the function
# ---------------------------------------------------------------------------
# Priority order matches the doc: M3 program code, then keywords,
# then the raiser's department. Confidence reflects which source was used.
# ---------------------------------------------------------------------------



def rule_a_02_classify_function(ticket):
    function_area = None
    confidence = 0.0
    source = None

    if ticket.get("m3_program_code"):
        function_area = ticket["m3_program_code"]
        confidence = 0.95
        source = "m3_program_code"
    else:
        text = (
            (ticket.get("title") or "") + " " + (ticket.get("description") or "")
        ).lower()

        for area, keywords in FUNCTION_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                function_area = area
                confidence = 0.7
                source = "keywords"
                break

        if not function_area:
            reporter_dept = ticket.get("reporter_department")
            if reporter_dept:
                function_area = reporter_dept
                confidence = 0.5
                source = "reporter_department"

    ticket["function_area"] = function_area
    ticket["derived"]["a02_confidence"] = confidence
    ticket["derived"]["a02_source"] = source
    return ticket


# ---------------------------------------------------------------------------
# A-03 Send low confidence to a human
# ---------------------------------------------------------------------------
# The rule does not clear function_area, it only flags that a human
# must confirm it. This preserves the classification for analytics.
# ---------------------------------------------------------------------------

A02_CONFIDENCE_THRESHOLD = 0.6


def rule_a_03_send_low_confidence_to_human(ticket):
    confidence = ticket["derived"].get("a02_confidence", 0)
    needs_triage = confidence < A02_CONFIDENCE_THRESHOLD

    ticket["derived"]["a03_needs_triage"] = needs_triage
    ticket["derived"]["a03_confidence_threshold"] = A02_CONFIDENCE_THRESHOLD
    return ticket


# ---------------------------------------------------------------------------
# A-04 Derive severity
# ---------------------------------------------------------------------------
# Scores business impact, user impact, and workaround availability.
# Claimed severity is recorded but never used for the derived value.
# ---------------------------------------------------------------------------

def rule_a_04_derive_severity(ticket):
    text = (
        (ticket.get("title") or "") + " " + (ticket.get("description") or "")
    ).lower()

    score = 0

    if any(kw in text for kw in ("outage", "production down", "system down")):
        score += 2
    if any(kw in text for kw in ("data loss", "breach", "security")):
        score += 3
    if any(kw in text for kw in ("all users", "everyone", "company wide")):
        score += 2
    if any(kw in text for kw in ("cannot work", "blocked", "no workaround")):
        score += 1
    if "workaround" in text:
        score -= 1

    if score >= 4:
        derived = "Critical"
    elif score >= 2:
        derived = "High"
    elif score >= 1:
        derived = "Medium"
    else:
        derived = "Low"

    ticket["derived"]["a04_derived_severity"] = derived
    ticket["derived"]["a04_claimed_severity"] = ticket.get("priority")
    ticket["derived"]["a04_score"] = score
    return ticket


# ---------------------------------------------------------------------------
# A-05 Apply context modifiers
# ---------------------------------------------------------------------------
# Caps non-production severity unless a go-live is imminent, and raises
# Finance tickets during the client's period close window.
# Both flags are injected by the pipeline, not derived from Jira.
# ---------------------------------------------------------------------------

def rule_a_05_apply_context_modifiers(ticket):
    derived = ticket["derived"]
    severity = derived.get("a04_derived_severity")
    environment = (ticket.get("environment") or "").lower()
    go_live_imminent = bool(ticket.get("go_live_imminent"))
    period_close = bool(ticket.get("client_period_close"))
    function_area = ticket.get("function_area")

    modified = False

    if "production" not in environment and not go_live_imminent:
        if severity in ("Critical", "High"):
            derived["a04_derived_severity"] = "Medium"
            modified = True
            derived["a05_cap_reason"] = "non_production"

    if function_area == "Finance" and period_close:
        current = derived.get("a04_derived_severity")
        order = ["Low", "Medium", "High", "Critical"]
        if current in order and current != "Critical":
            derived["a04_derived_severity"] = order[order.index(current) + 1]
            modified = True
            derived["a05_raise_reason"] = "period_close"

    derived["a05_modified"] = modified
    return ticket


# ---------------------------------------------------------------------------
# A-06 Record the disagreement
# ---------------------------------------------------------------------------
# Where derived and claimed differ by more than one level, keep both
# and flag. The flag is a relationship signal, not a rule failure.
# ---------------------------------------------------------------------------

def rule_a_06_record_disagreement(ticket):
    claimed = ticket["derived"].get("a04_claimed_severity")
    derived = ticket["derived"].get("a04_derived_severity")

    if claimed not in SEVERITY_LEVELS or derived not in SEVERITY_LEVELS:
        ticket["derived"]["a06_severity_disagreement"] = False
        ticket["derived"]["a06_severity_gap"] = None
        return ticket

    gap = abs(SEVERITY_LEVELS[claimed] - SEVERITY_LEVELS[derived])

    ticket["derived"]["a06_severity_disagreement"] = gap > 1
    ticket["derived"]["a06_severity_gap"] = gap
    return ticket


# ---------------------------------------------------------------------------
# A-07 Run an honest clock
# ---------------------------------------------------------------------------
# Measures elapsed hours against the client's SLA and computes breach risk.
# If a client_timezone is injected, the created_at is converted before
# computing elapsed time. Otherwise it falls back to UTC.
# ---------------------------------------------------------------------------

def rule_a_07_run_sla_clock(ticket):
    tier = str(ticket.get("customer_tier") or "").lower()
    sla_hours = 4 if tier == "enterprise" else 24

    created = _parse_ts(ticket.get("created_at"))
    now = datetime.now(timezone.utc)

    hours_since_created = 0.0
    if created:
        hours_since_created = round((now - created).total_seconds() / 3600, 2)

    breach_risk = 0.0
    if sla_hours > 0:
        breach_risk = round(min(hours_since_created / sla_hours, 1.0), 2)

    ticket["derived"]["a07_sla_hours"] = sla_hours
    ticket["derived"]["a07_hours_since_created"] = hours_since_created
    ticket["derived"]["a07_breach_risk_score"] = breach_risk
    ticket["derived"]["a07_breached"] = hours_since_created > sla_hours
    return ticket


# ---------------------------------------------------------------------------
# A-08 Route and escalate
# ---------------------------------------------------------------------------
# Assigns a skill pool from the function area, then decides whether the
# duty manager gets paged. Only genuine top severity or high breach risk
# triggers a page.
# ---------------------------------------------------------------------------

SKILL_POOL_BY_FUNCTION = {
    "Finance": "finance_support",
    "Warehouse": "warehouse_support",
    "Order": "order_support",
    "Production": "production_support",
    "HR": "hr_support",
}


def rule_a_08_route_and_escalate(ticket):
    derived = ticket["derived"]
    severity = derived.get("a04_derived_severity")
    breach = derived.get("a07_breach_risk_score", 0)
    function_area = ticket.get("function_area")

    skill_pool = SKILL_POOL_BY_FUNCTION.get(function_area, "general_support")

    escalation = "NORMAL"
    page = False

    if severity == "Critical":
        escalation = "IMMEDIATE"
        page = True
    elif severity == "High" and breach >= 0.75:
        escalation = "HIGH"
        page = True
    elif breach >= 0.75:
        escalation = "HIGH"

    derived["a08_skill_pool"] = skill_pool
    derived["a08_escalation_level"] = escalation
    derived["a08_page_on_call"] = page
    return ticket


RULES = [
    rule_a_01_validate_on_arrival,
    rule_a_02_classify_function,
    rule_a_03_send_low_confidence_to_human,
    rule_a_04_derive_severity,
    rule_a_05_apply_context_modifiers,
    rule_a_06_record_disagreement,
    rule_a_07_run_sla_clock,
    rule_a_08_route_and_escalate,
]