def get_nested_value(data, keys, default=None):
    current = data
    for key in keys:
        if type(current) != dict:
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


def map_jira_issue_to_canonical(issue):
    fields = issue.get("fields", {})
    labels = fields.get("labels", [])
    issue_type = (fields.get("issuetype") or {}).get("name")

    customer_tier = "Standard"
    for label in labels:
        if label.lower() == "enterprise":
            customer_tier = "Enterprise"

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
        "created_at": fields.get("created"),
        "labels": labels,
        "is_L3": "L3" in (issue_type or ""),
        # placeholders until proper JIRA L3 custom fields are configured
        "customer_tier": customer_tier,
        "error_code": None,
        "assigned_team": get_nested_value(fields, ["project", "name"]),
    }

    return canonical_ticket


def map_jira_response_to_canonical(response):
    issues = response.get("issues", [])
    canonical_tickets = []
    for issue in issues:
        canonical_ticket = map_jira_issue_to_canonical(issue)
        canonical_tickets.append(canonical_ticket)

    return canonical_tickets