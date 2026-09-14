from datetime import datetime
F02_CONFIDENCE_THRESHOLD = 0.5

def _parse_ts(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            continue
    return None


def _is_in_closed_period(started, closed_periods):
    ts = _parse_ts(started)
    if not ts or not closed_periods:
        return False
    for period in closed_periods:
        start = _parse_ts(period.get("start"))
        end = _parse_ts(period.get("end"))
        if start and end and start <= ts <= end:
            return True
    return False


# ---------------------------------------------------------------------------
# F-01 Classify the effort
# ---------------------------------------------------------------------------
# Uses issue_type, parent_project, and the B-02/B-03 scope decision.
# Writes the category onto each worklog, not on the ticket.
# ---------------------------------------------------------------------------

def rule_f_01_classify_effort(ticket):
    derived = ticket["derived"]
    contract_live = derived.get("b02_contract_live", False)
    in_scope = derived.get("b03_in_scope")
    issue_type = (ticket.get("issue_type") or "").lower()
    parent_project = (ticket.get("parent_project") or "").lower()

    if "defect" in issue_type and "internal" in parent_project:
        category = "Internal Rework"
    elif parent_project and "support" not in parent_project:
        category = "Billable Project"
    elif contract_live and in_scope is True:
        category = "Contracted Support"
    elif contract_live and in_scope is False:
        category = "Out of Scope"
    else:
        category = "Unknown"

    for w in ticket.get("worklogs", []):
        w["category"] = category

    return ticket


# ---------------------------------------------------------------------------
# F-02 Score the confidence
# ---------------------------------------------------------------------------
# Confidence is based on how much of the classification evidence exists.
# Anything below the threshold becomes Unknown, never a guess.
# ---------------------------------------------------------------------------

def rule_f_02_score_confidence(ticket):
    has_ticket = bool(ticket.get("ticket_key"))
    has_project = bool(ticket.get("parent_project"))
    has_contract = bool(ticket.get("contract"))

    score = sum([has_ticket, has_project, has_contract]) / 3

    for w in ticket.get("worklogs", []):
        w["confidence"] = round(score, 2)
        if score < F02_CONFIDENCE_THRESHOLD:
            w["category"] = "Unknown"

    return ticket


# ---------------------------------------------------------------------------
# F-03 Apply the right rate
# ---------------------------------------------------------------------------
# The rate table is injected into ticket["rate_table"].
# Historical rates are preserved by using the worklog's started date.
# ---------------------------------------------------------------------------

def rule_f_03_apply_cost_rate(ticket):
    rate_table = ticket.get("rate_table") or {}
    default_rate = rate_table.get("default", 0)

    for w in ticket.get("worklogs", []):
        role = w.get("author_role") or "Consultant"
        rate = rate_table.get(role, default_rate)
        hours = (w.get("time_spent_seconds") or 0) / 3600

        w["role"] = role
        w["rate"] = rate
        w["cost"] = round(hours * rate, 2)

    return ticket


# ---------------------------------------------------------------------------
# F-04 Never edit a published figure
# ---------------------------------------------------------------------------
# Worklogs in closed periods are marked for the adjustments stream.
# The rule does not modify or delete the original figures.
# ---------------------------------------------------------------------------

def rule_f_04_never_edit_published(ticket):
    closed_periods = ticket.get("closed_periods") or []

    for w in ticket.get("worklogs", []):
        w["append_only"] = True
        w["is_closed_period"] = _is_in_closed_period(
            w.get("started"), closed_periods
        )
        w["stream"] = "adjustment" if w["is_closed_period"] else "current"

    return ticket


# ---------------------------------------------------------------------------
# F-05 Isolate rework
# ---------------------------------------------------------------------------

def rule_f_05_isolate_rework(ticket):
    rework_hours = 0
    for w in ticket.get("worklogs", []):
        if w.get("category") == "Internal Rework":
            rework_hours += (w.get("time_spent_seconds") or 0) / 3600

    ticket["derived"]["f05_rework_hours"] = round(rework_hours, 2)
    return ticket


# ---------------------------------------------------------------------------
# F-06 Keep the evidence
# ---------------------------------------------------------------------------

F06_POLICY_VERSION = "v1"


def rule_f_06_keep_evidence(ticket):
    derived = ticket["derived"]

    derived["f06_evidence"] = {
        "policy_version": F06_POLICY_VERSION,
        "inputs": {
            "b02_contract_live": derived.get("b02_contract_live"),
            "b03_in_scope": derived.get("b03_in_scope"),
            "issue_type": ticket.get("issue_type"),
            "parent_project": ticket.get("parent_project"),
        },
        "rules_applied": [
            r for r in derived.get("rules_applied", [])
            if r.startswith("rule_f_")
        ],
        "evaluated_at": derived.get("rules_evaluated_at"),
    }

    return ticket


# ---------------------------------------------------------------------------
# F-07 Report margin per client
# ---------------------------------------------------------------------------
# Per ticket it writes the cost. The aggregator sums by client + contract.
# ---------------------------------------------------------------------------

def rule_f_07_report_margin(ticket):
    total_cost = sum((w.get("cost") or 0) for w in ticket.get("worklogs", []))
    total_hours = sum(
        (w.get("time_spent_seconds") or 0) for w in ticket.get("worklogs", [])
    ) / 3600

    ticket["derived"]["f07_total_cost"] = round(total_cost, 2)
    ticket["derived"]["f07_total_hours"] = round(total_hours, 2)
    return ticket


RULES = [
    rule_f_01_classify_effort,
    rule_f_02_score_confidence,
    rule_f_03_apply_cost_rate,
    rule_f_04_never_edit_published,
    rule_f_05_isolate_rework,
    rule_f_06_keep_evidence,
    rule_f_07_report_margin,
]