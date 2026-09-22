# app/db/source_registration_table.py

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ArraySpec:
    """Nested array to merge by a stable key."""
    field: str              # e.g. "status_history"
    key: str                # e.g. "history_id"
    sort: str | None = None # optional field to sort merged items by


@dataclass
class EventSpec:
    """Nested array to flatten into event rows."""
    array_field: str        # e.g. "comments"
    event_type: str         # e.g. "comment"
    id_field: str           # e.g. "comment_id"
    occurred_at: str        # e.g. "created"


@dataclass
class SourceSpec:
    source: str
    collection: str
    events_collection: str = "document_events"
    identity: str | Callable[[dict], str | None] = "id"
    merge_arrays: list[ArraySpec] = field(default_factory=list)
    events: list[EventSpec] = field(default_factory=list)
    indexes: list[str] = field(default_factory=list)


def _identity(doc, spec):
    if callable(spec.identity):
        return spec.identity(doc)
    return doc.get(spec.identity)


# ---------------------------------------------------------------------------
# The registry
# ---------------------------------------------------------------------------
# Add one entry per connector. No new Python code is needed to support a
# new source beyond this entry.
# ---------------------------------------------------------------------------

SOURCES: dict[str, SourceSpec] = {
    "jira": SourceSpec(
        source="jira",
        collection="jira_tickets",
        identity="ticket_key",
        merge_arrays=[
            ArraySpec("status_history", "history_id", sort="created"),
            ArraySpec("comments", "comment_id", sort="created"),
            ArraySpec("worklogs", "worklog_id", sort="started"),
            ArraySpec("attachments", "attachment_id", sort="created"),
            ArraySpec("approvals", "approval_id", sort="created"),
        ],
        events=[
            EventSpec("status_history", "status_change", "history_id", "created"),
            EventSpec("comments", "comment", "comment_id", "created"),
            EventSpec("worklogs", "worklog", "worklog_id", "started"),
            EventSpec("attachments", "attachment", "attachment_id", "created"),
            EventSpec("approvals", "approval", "approval_id", "created"),
        ],
        indexes=[
            "client_id",
            "function_area",
            "created_at",
            "updated_at",
            "rule_results.a04_severity",
            "rule_results.b04_route",
            "rule_results.d07_client_health_score",
        ],
    ),
}