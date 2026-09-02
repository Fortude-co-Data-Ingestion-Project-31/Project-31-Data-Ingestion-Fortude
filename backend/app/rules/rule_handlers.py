def apply_selected_rules(document, rule_name):
    if rule_name == "Infor Sales Rules":
        document.setdefault("tags", []).append("sales")
        document["metadata"] = {
            "category": "sales",
            "source": "sales-rule",
        }
    elif rule_name == "L3 Ticket Rules":
        document.setdefault("tags", []).append("support")
        document["metadata"] = {
            "priority": "high",
            "source": "support-rule",
        }
    elif rule_name == "Knowledge Base Rules":
        document.setdefault("tags", []).append("knowledge")
        document["metadata"] = {
            "summary": "knowledge-base-entry",
            "source": "knowledge-rule",
        }
    else:
        document["metadata"] = {"source": "default-rule"}

    document["rule_applied"] = rule_name
    return document
