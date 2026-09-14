WAITING_STATUSES = {
    "Waiting for Customer",
    "Waiting for Support",
    "Blocked",
    "On Hold",
}

WORKING_STATUSES = {
    "In Progress",
    "In Review",
    "In Development",
    "In Testing",
}


# ---------------------------------------------------------------------------
# D-01 Build the history
# ---------------------------------------------------------------------------
# The mapper already built status_history. This rule only reports the count
# so a downstream writer can spot tickets with no movement.
# ---------------------------------------------------------------------------

def rule_d_01_build_history(ticket):
    history = ticket.get("status_history", [])
    ticket["derived"]["d01_change_count"] = len(history)
    ticket["derived"]["d01_has_movement"] = len(history) > 0
    return ticket


# ---------------------------------------------------------------------------
# D-02 Separate waiting from working
# ---------------------------------------------------------------------------
# Iterates the status_history durations and buckets them into
# waiting vs working. Duration is attributed to the previous status.
# ---------------------------------------------------------------------------

def rule_d_02_separate_waiting_from_working(ticket):
    waiting = 0
    working = 0

    for entry in ticket.get("status_history", []):
        duration = entry.get("duration_in_previous_status_seconds") or 0
        previous_status = entry.get("from")

        if previous_status in WAITING_STATUSES:
            waiting += duration
        elif previous_status in WORKING_STATUSES:
            working += duration

    total = waiting + working

    ticket["derived"]["d02_waiting_seconds"] = waiting
    ticket["derived"]["d02_working_seconds"] = working
    ticket["derived"]["d02_waiting_share"] = (
        round(waiting / total, 2) if total else 0
    )
    return ticket


# ---------------------------------------------------------------------------
# D-03 Count reopens
# ---------------------------------------------------------------------------
# The mapper already flagged each reopen in status_history.is_reopen.
# ---------------------------------------------------------------------------

def rule_d_03_count_reopens(ticket):
    reopens = sum(
        1 for e in ticket.get("status_history", []) if e.get("is_reopen")
    )

    ticket["derived"]["d03_reopen_count"] = reopens
    ticket["derived"]["d03_has_reopen"] = reopens > 0
    return ticket


# ---------------------------------------------------------------------------
# D-04 Detect recurrence
# ---------------------------------------------------------------------------
# Per ticket it builds a stable error signature. The aggregator
# groups by client + function + signature over 90 days.
# ---------------------------------------------------------------------------

def rule_d_04_detect_recurrence(ticket):
    text = (
        (ticket.get("title") or "") + " " + (ticket.get("description") or "")
    ).lower()

    tokens = sorted(set(t for t in text.split() if len(t) > 3))
    signature = " ".join(tokens)[:160]

    ticket["derived"]["d04_error_signature"] = signature
    return ticket


# ---------------------------------------------------------------------------
# D-05 Watch who is raising
# ---------------------------------------------------------------------------

SENIOR_ROLES = {"manager", "admin", "executive", "director","senior"}


def rule_d_05_watch_who_is_raising(ticket):
    role = (ticket.get("reporter_role") or "").lower()
    is_senior = role in SENIOR_ROLES or any(r in role for r in SENIOR_ROLES)

    ticket["derived"]["d05_senior_raiser"] = is_senior
    return ticket


# ---------------------------------------------------------------------------
# D-06 Compare against the client's own baseline
# ---------------------------------------------------------------------------
# The baseline is injected into ticket["client_baseline"].
# The rule does not compute it - it only records the comparison.
# ---------------------------------------------------------------------------

def rule_d_06_compare_against_baseline(ticket):
    baseline = ticket.get("client_baseline") or {}

    ticket["derived"]["d06_baseline"] = baseline
    ticket["derived"]["d06_has_baseline"] = bool(baseline)
    return ticket


# ---------------------------------------------------------------------------
# D-07 Score and alert
# ---------------------------------------------------------------------------
# Produces the per-ticket contribution. The aggregator in rule_engine.py
# sums these per client and produces the weekly health score.
# ---------------------------------------------------------------------------

def rule_d_07_score_and_alert(ticket):
    derived = ticket["derived"]
    score = 0

    if derived.get("d03_has_reopen"):
        score += 1
    if derived.get("d05_senior_raiser"):
        score += 1

    waiting = derived.get("d02_waiting_seconds") or 0
    working = derived.get("d02_working_seconds") or 0

    if working > 0 and waiting > working:
        score += 1

    derived["d07_health_contribution"] = score
    return ticket


RULES = [
    rule_d_01_build_history,
    rule_d_02_separate_waiting_from_working,
    rule_d_03_count_reopens,
    rule_d_04_detect_recurrence,
    rule_d_05_watch_who_is_raising,
    rule_d_06_compare_against_baseline,
    rule_d_07_score_and_alert,
]