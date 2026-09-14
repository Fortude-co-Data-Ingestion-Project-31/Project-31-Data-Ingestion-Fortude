import hashlib
import json
from datetime import datetime


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
# G-01 Check completeness
# ---------------------------------------------------------------------------

def rule_g_01_check_completeness(ticket):
    missing = []

    if not ticket.get("risk_level"):
        missing.append("risk_level")
    if not ticket.get("rollback_plan"):
        missing.append("rollback_plan")
    if not ticket.get("testing_evidence"):
        missing.append("testing_evidence")
    if not ticket.get("description"):
        missing.append("reason_for_change")

    ticket["derived"]["g01_missing"] = missing
    ticket["derived"]["g01_complete"] = len(missing) == 0
    return ticket


# ---------------------------------------------------------------------------
# G-02 Check the approval is real
# ---------------------------------------------------------------------------
# Confirms somebody on the approver list actually approved, not just
# that the ticket reached an approved status.
# ---------------------------------------------------------------------------

def rule_g_02_check_real_approval(ticket):
    approvers = [a.lower() for a in (ticket.get("approver_list") or [])]
    approvals = ticket.get("approvals", [])

    approved_by = [
        (a.get("approver") or "").lower()
        for a in approvals
        if (a.get("status") or "").lower() == "approved"
    ]

    real = any(a in approvers for a in approved_by)

    ticket["derived"]["g02_real_approval"] = real
    ticket["derived"]["g02_approved_by"] = approved_by
    return ticket


# ---------------------------------------------------------------------------
# G-03 Check the order of events
# ---------------------------------------------------------------------------
# Approval timestamp must precede deployment timestamp. This is one of
# the most common real audit failures.
# ---------------------------------------------------------------------------

def rule_g_03_check_order_of_events(ticket):
    approvals = ticket.get("approvals", [])
    deployment = _parse_ts(ticket.get("deployment_timestamp"))

    approval_ts = None
    for a in approvals:
        ts = _parse_ts(a.get("created"))
        if ts and (approval_ts is None or ts < approval_ts):
            approval_ts = ts

    if approval_ts and deployment:
        ok = approval_ts < deployment
    else:
        ok = False

    ticket["derived"]["g03_approval_before_deployment"] = ok
    return ticket


# ---------------------------------------------------------------------------
# G-04 Check separation of duties
# ---------------------------------------------------------------------------

def rule_g_04_check_separation_of_duties(ticket):
    requester = (ticket.get("reporter") or "").lower()
    approvers = [a.lower() for a in (ticket.get("approver_list") or [])]
    deployer = (ticket.get("assignee") or "").lower()

    requester_is_approver = requester in approvers
    requester_is_deployer = requester == deployer

    ticket["derived"]["g04_separation_ok"] = not (
        requester_is_approver or requester_is_deployer
    )
    return ticket


# ---------------------------------------------------------------------------
# G-05 Handle emergency changes properly
# ---------------------------------------------------------------------------

def rule_g_05_handle_emergency_change(ticket):
    emergency = bool(ticket.get("emergency_change"))

    ticket["derived"]["g05_is_emergency"] = emergency
    ticket["derived"]["g05_requires_retro_approval"] = emergency
    return ticket


# ---------------------------------------------------------------------------
# G-06 Catch mislabelled changes
# ---------------------------------------------------------------------------

def rule_g_06_catch_mislabelled_change(ticket):
    change_type = (ticket.get("change_type") or "").lower()
    sensitive = bool(ticket.get("sensitive_system"))

    ticket["derived"]["g06_mislabelled"] = (
        change_type == "routine" and sensitive
    )
    return ticket


# ---------------------------------------------------------------------------
# G-07 Find orphan deployments
# ---------------------------------------------------------------------------

def rule_g_07_find_orphan_deployments(ticket):
    has_deployment = bool(ticket.get("deployment_timestamp"))
    has_change = bool(ticket.get("ticket_key"))

    ticket["derived"]["g07_orphan"] = has_deployment and not has_change
    return ticket


# ---------------------------------------------------------------------------
# G-08 Protect the evidence
# ---------------------------------------------------------------------------
# Hashes the evidence record so later tampering is detectable.
# ---------------------------------------------------------------------------

def rule_g_08_protect_evidence(ticket):
    evidence = {
        "ticket_key": ticket.get("ticket_key"),
        "approvals": ticket.get("approvals", []),
        "deployment_timestamp": ticket.get("deployment_timestamp"),
        "attachments": ticket.get("attachments", []),
        "risk_level": ticket.get("risk_level"),
        "emergency_change": ticket.get("emergency_change"),
    }

    payload = json.dumps(evidence, sort_keys=True, default=str).encode("utf-8")
    ticket["derived"]["g08_evidence_hash"] = hashlib.sha256(payload).hexdigest()
    return ticket


RULES = [
    rule_g_01_check_completeness,
    rule_g_02_check_real_approval,
    rule_g_03_check_order_of_events,
    rule_g_04_check_separation_of_duties,
    rule_g_05_handle_emergency_change,
    rule_g_06_catch_mislabelled_change,
    rule_g_07_find_orphan_deployments,
    rule_g_08_protect_evidence,
]