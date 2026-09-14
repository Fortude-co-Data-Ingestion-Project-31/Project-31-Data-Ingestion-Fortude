from datetime import datetime, timezone, timedelta

from rules.jira_rules import RULE_SETS, DEFAULT_RULE_SET, ALL_RULE_ORDER


class RuleEngineError(Exception):
    pass


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


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
# Per-ticket rule application
# ---------------------------------------------------------------------------

def apply_rule_set(ticket, rule_set_name, stop_on_error=False):
    rules = _resolve_rule_set(rule_set_name)
    if rules is None:
        raise RuleEngineError(f"Unknown rule set: {rule_set_name}")

    ticket.setdefault("derived", {})
    ticket["derived"].setdefault("rules_applied", [])
    ticket["derived"].setdefault("rule_errors", [])

    for rule in rules:
        rule_name = getattr(rule, "__name__", str(rule))
        try:
            ticket = rule(ticket)
            ticket["derived"]["rules_applied"].append(rule_name)
        except Exception as e:
            ticket["derived"]["rule_errors"].append({
                "rule": rule_name,
                "error": str(e),
            })
            if stop_on_error:
                raise

    ticket["derived"]["rule_set"] = rule_set_name
    ticket["derived"]["rules_evaluated_at"] = _now_iso()
    return ticket


def transform_tickets(tickets, rule_set_name, stop_on_error=False):
    return [
        apply_rule_set(t, rule_set_name, stop_on_error=stop_on_error)
        for t in tickets
    ]


def _resolve_rule_set(rule_set_name):
    if not rule_set_name:
        return DEFAULT_RULE_SET
    if rule_set_name == "L3 Ticket Rules":
        return "A"
    return rule_set_name


def transform_canonical_tickets(tickets, rule_set_name=None):
    """
    Per-ticket rules. Use "A", "B", "C", "D", "F", "G", "ALL".
    "L3" is kept as an alias for "A".
    Defaults to "ALL" when rule_set_name is empty or None.
    """
    rule_set_name = _resolve_rule_set(rule_set_name)

    if rule_set_name == "ALL":
        for name in ALL_RULE_ORDER:
            tickets = transform_tickets(tickets, name)
        return tickets

    if rule_set_name not in RULE_SETS:
        raise RuleEngineError(f"Unknown rule set: {rule_set_name}")

    return transform_tickets(tickets, rule_set_name)


# ---------------------------------------------------------------------------
# Cross-ticket aggregations
# ---------------------------------------------------------------------------

def _group_by(tickets, key_fn):
    groups = {}
    for t in tickets:
        key = key_fn(t)
        if key is None:
            continue
        groups.setdefault(key, []).append(t)
    return groups


# --------------------------- D: client health -----------------------------

def aggregate_recurrence(tickets):
    """
    D-04 across tickets: same client + function + error signature
    raised 3+ times in 90 days is a pattern.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)

    grouped = _group_by(
        tickets,
        lambda t: (
            t.get("client_id"),
            t.get("function_area"),
            t.get("derived", {}).get("d04_error_signature"),
        ),
    )

    for _, group in grouped.items():
        recent = [
            t for t in group
            if (_parse_ts(t.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc)) >= cutoff
        ]

        is_pattern = len(recent) >= 3
        for t in group:
            t.setdefault("derived", {})
            t["derived"]["d04_recurrence_pattern"] = is_pattern
            t["derived"]["d04_recurrence_count_90d"] = len(recent)

    return tickets


def aggregate_client_health(tickets):
    """
    D-06 and D-07 across tickets: score per client.
    """
    grouped = _group_by(tickets, lambda t: t.get("client_id"))

    for _, group in grouped.items():
        total = sum(
            t.get("derived", {}).get("d07_health_contribution", 0) for t in group
        )
        score = total / len(group) if group else 0

        for t in group:
            t.setdefault("derived", {})
            t["derived"]["d07_client_health_score"] = round(score, 2)
            t["derived"]["d07_client_alert"] = score >= 2

    return tickets


# --------------------------- B: leakage -----------------------------------

def aggregate_leakage(tickets):
    """
    B-07 across tickets: total out-of-scope hours by client + function.
    """
    grouped = _group_by(
        tickets,
        lambda t: (t.get("client_id"), t.get("function_area")),
    )

    for _, group in grouped.items():
        total_hours = sum(
            t.get("derived", {}).get("b07_leakage_hours", 0) for t in group
        )
        for t in group:
            t.setdefault("derived", {})
            t["derived"]["b07_client_function_leakage_hours"] = round(total_hours, 2)

    return tickets


# --------------------------- F: margin ------------------------------------

def aggregate_margin(tickets):
    """
    F-07 across tickets: total cost by client + contract.
    """
    grouped = _group_by(
        tickets,
        lambda t: (t.get("client_id"), t.get("contract_id")),
    )

    for _, group in grouped.items():
        total_cost = sum(
            t.get("derived", {}).get("f07_total_cost", 0) for t in group
        )
        for t in group:
            t.setdefault("derived", {})
            t["derived"]["f07_client_contract_cost"] = round(total_cost, 2)

    return tickets


AGGREGATORS = {
    "D": [aggregate_recurrence, aggregate_client_health],
    "B": [aggregate_leakage],
    "F": [aggregate_margin],
}


def run_aggregators(tickets, rule_set_name=None):
    rule_set_name = _resolve_rule_set(rule_set_name)

    if rule_set_name == "ALL":
        for name in ALL_RULE_ORDER:
            for aggregator in AGGREGATORS.get(name, []):
                tickets = aggregator(tickets)
        return tickets

    for aggregator in AGGREGATORS.get(rule_set_name, []):
        tickets = aggregator(tickets)
    return tickets


# ---------------------------------------------------------------------------
# Combined entry points
# ---------------------------------------------------------------------------

def transform_canonical_tickets_full(tickets, rule_set_name=None):
    """
    Per-ticket rules + cross-ticket aggregators.
    Defaults to "ALL" when rule_set_name is empty or None.
    """
    rule_set_name = _resolve_rule_set(rule_set_name)
    tickets = transform_canonical_tickets(tickets, rule_set_name)
    tickets = run_aggregators(tickets, rule_set_name)
    return tickets