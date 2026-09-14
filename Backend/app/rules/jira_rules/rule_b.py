from datetime import datetime


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# B-02 Check the contract is live
# ---------------------------------------------------------------------------

def rule_b_02_check_contract_is_live(ticket):
    contract = ticket.get("contract") or {}
    ticket_date = _parse_date(ticket.get("created_at"))

    start = _parse_date(contract.get("start_date"))
    end = _parse_date(contract.get("end_date"))

    is_live = (
        bool(contract)
        and ticket_date is not None
        and (start is None or start <= ticket_date)
        and (end is None or end >= ticket_date)
    )

    ticket["derived"]["b02_contract_live"] = is_live
    ticket["derived"]["b02_contract_id"] = contract.get("contract_id")
    return ticket


# ---------------------------------------------------------------------------
# B-03 Check module coverage
# ---------------------------------------------------------------------------
# Uses the function_area produced by A-02. If A-02 was low confidence,
# coverage cannot be trusted, so it is marked unknown.
# ---------------------------------------------------------------------------

def rule_b_03_check_module_coverage(ticket):
    contract = ticket.get("contract") or {}
    covered = [m.lower() for m in (contract.get("covered_modules") or [])]
    function_area = ticket.get("function_area")
    a02_confidence = ticket["derived"].get("a02_confidence", 0)

    if not function_area or a02_confidence < 0.6:
        in_scope = None
    else:
        in_scope = function_area.lower() in covered

    ticket["derived"]["b03_in_scope"] = in_scope
    ticket["derived"]["b03_covered_modules"] = contract.get("covered_modules") or []
    return ticket


# ---------------------------------------------------------------------------
# B-04 Route rather than reject
# ---------------------------------------------------------------------------
# Out-of-scope work goes to a billable path with an estimate requirement.
# It is never silently absorbed and never refused.
# ---------------------------------------------------------------------------

def rule_b_04_route_out_of_scope(ticket):
    derived = ticket["derived"]
    live = derived.get("b02_contract_live")
    in_scope = derived.get("b03_in_scope")

    if not live:
        route = "billable_path"
        reason = "no_live_contract"
    elif in_scope is False:
        route = "billable_path"
        reason = "module_not_covered"
    elif in_scope is None:
        route = "commercial_review"
        reason = "coverage_unknown"
    else:
        route = "support_queue"
        reason = "in_scope"

    derived["b04_route"] = route
    derived["b04_route_reason"] = reason
    derived["b04_requires_estimate"] = route == "billable_path"
    return ticket


# ---------------------------------------------------------------------------
# B-05 Watch the balance
# ---------------------------------------------------------------------------

B05_THRESHOLD = 0.8


def rule_b_05_watch_entitlement_balance(ticket):
    contract = ticket.get("contract") or {}
    entitled = contract.get("entitled_hours") or 0
    consumed = contract.get("consumed_hours") or 0

    ratio = (consumed / entitled) if entitled else 0

    ticket["derived"]["b05_remaining_hours"] = round(entitled - consumed, 2)
    ticket["derived"]["b05_consumption_ratio"] = round(ratio, 2)
    ticket["derived"]["b05_threshold_breached"] = ratio >= B05_THRESHOLD
    return ticket


# ---------------------------------------------------------------------------
# B-06 Track expiry
# ---------------------------------------------------------------------------

B06_WINDOW_DAYS = 60


def rule_b_06_track_contract_expiry(ticket):
    contract = ticket.get("contract") or {}
    end = _parse_date(contract.get("end_date"))
    ticket_date = _parse_date(ticket.get("created_at"))

    if not end or not ticket_date:
        ticket["derived"]["b06_days_to_expiry"] = None
        ticket["derived"]["b06_expiring_soon"] = False
        return ticket

    days = (end - ticket_date).days
    ticket["derived"]["b06_days_to_expiry"] = days
    ticket["derived"]["b06_expiring_soon"] = 0 <= days <= B06_WINDOW_DAYS
    return ticket


# ---------------------------------------------------------------------------
# B-07 Report the leakage
# ---------------------------------------------------------------------------
# Per ticket it records how many worklog hours were delivered outside scope.
# The rule engine's aggregate step sums these by client and by function.
# ---------------------------------------------------------------------------

def rule_b_07_report_leakage(ticket):
    route = ticket["derived"].get("b04_route")

    hours = sum(
        (w.get("time_spent_seconds") or 0) for w in ticket.get("worklogs", [])
    ) / 3600

    ticket["derived"]["b07_leakage_hours"] = (
        round(hours, 2) if route == "billable_path" else 0
    )
    return ticket


RULES = [
    rule_b_02_check_contract_is_live,
    rule_b_03_check_module_coverage,
    rule_b_04_route_out_of_scope,
    rule_b_05_watch_entitlement_balance,
    rule_b_06_track_contract_expiry,
    rule_b_07_report_leakage,
]