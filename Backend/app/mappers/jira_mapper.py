def get_nested_value(data, keys, default=None):
    current = data
    for key in keys:
        if type(current) != dict:
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


# ---------------------------------------------------------------------------
# Ticket level fields
# ---------------------------------------------------------------------------

def map_jira_issue_to_canonical(issue):
    fields = issue.get("fields", {})
    labels = fields.get("labels", [])
    issue_type = (fields.get("issuetype") or {}).get("name")

    customer_tier = "Standard"
    for label in labels:
        if label.lower() == "enterprise":
            customer_tier = "Enterprise"

    reporter = get_nested_value(fields, ["reporter", "displayName"])
    reporter_role = get_nested_value(fields, ["reporter", "accountType"])

    canonical_ticket = {
        "source": "jira",
        "ticket_id": issue.get("id"),
        "ticket_key": issue.get("key"),
        "title": fields.get("summary"),
        "issue_type": issue_type,
        "description": str(fields.get("description") or ""),
        "status": get_nested_value(fields, ["status", "name"]),
        "priority": get_nested_value(fields, ["priority", "name"]),
        "assignee": get_nested_value(fields, ["assignee", "displayName"]),
        "reporter": reporter,
        "reporter_role": reporter_role,
        "created_at": fields.get("created"),
        "updated_at": fields.get("updated"),
        "resolution": get_nested_value(fields, ["resolution", "name"]),
        "resolution_date": fields.get("resolutiondate"),
        "labels": labels,
        "is_L3": "L3" in (issue_type or ""),
        "customer_tier": customer_tier,
        "assigned_team": get_nested_value(fields, ["project", "name"]),
        "project_key": get_nested_value(fields, ["project", "key"]),
        "project_name": get_nested_value(fields, ["project", "name"]),
        "components": [c.get("name") for c in fields.get("components", [])],
        "environment": fields.get("environment"),
        # placeholders until custom fields are configured in Jira
        "client_id": None,
        "contract_id": None,
        "m3_program_code": None,
        "function_area": None,
        "risk_level": None,
        "sensitive_system": None,
        "change_type": None,
        "emergency_change": None,
        "approver_list": None,
        "deployment_timestamp": None,
        "rollback_plan": None,
        "testing_evidence": None,
        "parent_project": None,
        # nested collections filled by the bundle mapper
        "status_history": [],
        "comments": [],
        "worklogs": [],
        "approvals": [],
        "attachments": [],
        # external data injected before rule set B / F
        "contract": None,
        "rate_table": None,
        "client_baseline": None,
        # rule output
        "derived": {},
    }

    return canonical_ticket


# ---------------------------------------------------------------------------
# Changelog -> status history
# ---------------------------------------------------------------------------

def _parse_ts(value):
    from datetime import datetime

    if not value:
        return None

    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            continue
    return None


def _seconds_between(start_iso, end_iso):
    start = _parse_ts(start_iso)
    end = _parse_ts(end_iso)

    if not start or not end:
        return 0
    return int((end - start).total_seconds())


def map_status_history(changelog):
    """
    Accepts either the list your connector returns
    or a raw dict with a "values" key.
    """
    if isinstance(changelog, dict):
        changelog = changelog.get("values", [])

    history = []

    for h in changelog or []:
        author = get_nested_value(h, ["author", "displayName"])
        created = h.get("created")

        for item in h.get("items", []):
            if item.get("field") == "status":
                history.append({
                    "history_id": h.get("id"),
                    "author": author,
                    "created": created,
                    "from": item.get("fromString"),
                    "to": item.get("toString"),
                })

    history.sort(key=lambda x: x.get("created") or "")
    return history


def enrich_status_history(ticket):
    """
    Adds duration and reopen flags to each status change.
    """
    history = ticket.get("status_history", [])
    created_at = ticket.get("created_at")

    reopen_statuses = {"Resolved", "Closed", "Done"}

    if not history:
        ticket["derived"]["reopen_count"] = 0
        return ticket

    reopen_count = 0

    for index, entry in enumerate(history):
        previous_time = created_at if index == 0 else history[index - 1]["created"]
        entry["duration_in_previous_status_seconds"] = _seconds_between(
            previous_time, entry["created"]
        )

        if index > 0:
            is_reopen = (
                history[index - 1].get("to") in reopen_statuses
                and entry.get("to") not in reopen_statuses
            )
        else:
            is_reopen = False

        entry["is_reopen"] = is_reopen
        if is_reopen:
            reopen_count += 1

    ticket["derived"]["reopen_count"] = reopen_count
    return ticket


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

def map_comments(comments):
    if isinstance(comments, dict):
        comments = comments.get("comments", [])

    mapped = []

    for c in comments or []:
        mapped.append({
            "comment_id": c.get("id"),
            "author": get_nested_value(c, ["author", "displayName"]),
            "body": str(c.get("body") or ""),
            "created": c.get("created"),
            "updated": c.get("updated"),
            "is_internal": _is_internal_comment(c),
        })

    return mapped


def _is_internal_comment(comment):
    if "jsdPublic" in comment:
        return not comment.get("jsdPublic", True)
    if comment.get("visibility"):
        return True
    return False


# ---------------------------------------------------------------------------
# Worklogs
# ---------------------------------------------------------------------------

def map_worklogs(worklogs):
    if isinstance(worklogs, dict):
        worklogs = worklogs.get("worklogs", [])

    mapped = []

    for w in worklogs or []:
        mapped.append({
            "worklog_id": w.get("id"),
            "author": get_nested_value(w, ["author", "displayName"]),
            "author_role": get_nested_value(w, ["author", "accountType"]),
            "time_spent_seconds": w.get("timeSpentSeconds"),
            "started": w.get("started"),
            "comment": str(w.get("comment") or ""),
        })

    return mapped


# ---------------------------------------------------------------------------
# Approvals (optional - only if you add the JSM endpoint later)
# ---------------------------------------------------------------------------

def map_approvals(approvals):
    if not approvals:
        return []

    if isinstance(approvals, dict):
        approvals = approvals.get("values", [])

    mapped = []

    for a in approvals or []:
        mapped.append({
            "approval_id": a.get("id"),
            "approver": get_nested_value(a, ["approver", "displayName"]),
            "status": a.get("status"),
            "created": a.get("createdDate"),
            "decision": a.get("decision"),
        })

    return mapped


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------

def map_attachments(issue):
    fields = issue.get("fields", {})
    attachments = fields.get("attachment") or []

    mapped = []

    for a in attachments:
        mapped.append({
            "attachment_id": a.get("id"),
            "filename": a.get("filename"),
            "created": a.get("created"),
            "author": get_nested_value(a, ["author", "displayName"]),
            "size": a.get("size"),
        })

    return mapped


# ---------------------------------------------------------------------------
# Bundle mapper
# ---------------------------------------------------------------------------

def map_jira_bundle_to_canonical(bundle):
    """
    bundle = {
        "issue": <one item from get_my_issues()["issues"]>,
        "changelog": <list from get_issue_changelog(key)>,
        "comments": <list from get_issue_comments(key)>,
        "worklogs": <list from get_issue_worklogs(key)>,
        "approvals": <optional list>,
    }
    """
    issue = bundle.get("issue", {})

    ticket = map_jira_issue_to_canonical(issue)
    ticket["status_history"] = map_status_history(bundle.get("changelog", []))
    ticket["comments"] = map_comments(bundle.get("comments", []))
    ticket["worklogs"] = map_worklogs(bundle.get("worklogs", []))
    ticket["approvals"] = map_approvals(bundle.get("approvals", []))
    ticket["attachments"] = map_attachments(issue)

    enrich_status_history(ticket)

    return ticket


def map_jira_bundles_to_canonical(bundles):
    return [map_jira_bundle_to_canonical(b) for b in bundles]


# ---------------------------------------------------------------------------
# Backwards compatible search-only mapper
# ---------------------------------------------------------------------------

def map_jira_response_to_canonical(response):
    issues = response.get("issues", [])
    return [map_jira_issue_to_canonical(issue) for issue in issues]