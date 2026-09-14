# app/mappers/jira_full_sync.py

import asyncio
import json
from pathlib import Path

from fastapi import HTTPException

from connectors.Jira_API_connector import search_all_issues, fetch_full_bundle
from mappers.jira_mapper import map_jira_bundles_to_canonical
from mappers.jira_rule_engine import transform_canonical_tickets_full


# ---------------------------------------------------------------------------
# Output location
# ---------------------------------------------------------------------------
# Full sync writes to its own file so it never races the incremental poller.
# Adjust parents[N] to match your repo layout.
# ---------------------------------------------------------------------------

FULL_SYNC_OUTPUT_FOLDER = Path(__file__).resolve().parents[3] / "local_data" / "output"
FULL_SYNC_OUTPUT_FILE = FULL_SYNC_OUTPUT_FOLDER / "jira_issues.json"

# Set to True only if your Jira instance is Jira Service Management.
# Otherwise fetch_full_bundle returns an empty approvals list.
FETCH_APPROVALS = True


# ---------------------------------------------------------------------------
# Concurrency guard
# ---------------------------------------------------------------------------
# Prevents two full syncs from running at the same time, whether triggered
# by the endpoint, the nightly poller, or manual invocation.
# ---------------------------------------------------------------------------

_full_sync_lock = asyncio.Lock()


# ---------------------------------------------------------------------------
# External data injection
# ---------------------------------------------------------------------------
# Rules B and F expect contract data and a rate table on each ticket.
# Rules D expect a client baseline. None of that comes from Jira.
# Replace the stubs below with your real lookups when ready.
# ---------------------------------------------------------------------------

def inject_external_data(tickets):
    for t in tickets:
        t.setdefault("contract", None)
        t.setdefault("rate_table", None)
        t.setdefault("client_baseline", None)
        t.setdefault("closed_periods", [])
    return tickets


# ---------------------------------------------------------------------------
# Merge helpers
# ---------------------------------------------------------------------------

def _load_existing(output_file: Path) -> list:
    if not output_file.exists():
        return []
    try:
        data = json.loads(output_file.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _merge_by_ticket_key(existing: list, incoming: list) -> list:
    ticket_dict = {
        t.get("ticket_key"): t
        for t in existing
        if isinstance(t, dict) and t.get("ticket_key")
    }
    for t in incoming:
        key = t.get("ticket_key")
        if key:
            ticket_dict[key] = t
    return list(ticket_dict.values())


# ---------------------------------------------------------------------------
# Full sync
# ---------------------------------------------------------------------------

async def full_sync_jira(
    rule: str | None = None,
    output_file: Path | None = None,
):
    """
    Fetch every issue the API user can see, fetch full history for each,
    run the rule engine, and save the result to a dedicated JSON file.

    Do NOT run this every 5 minutes. Run it manually, nightly, or on demand.
    """
    if _full_sync_lock.locked():
        raise HTTPException(status_code=409, detail="Full sync already running")

    async with _full_sync_lock:
        target = Path(output_file) if output_file else FULL_SYNC_OUTPUT_FILE
        target.parent.mkdir(parents=True, exist_ok=True)

        print(f"[full sync] starting. Output: {target.resolve()}")

        try:
            # 1. Fetch every issue the API user can see
            issues = await search_all_issues()
            print(f"[full sync] search returned {len(issues)} issues")

            # 2. Fetch full history per issue
            bundles = []
            for index, issue in enumerate(issues, start=1):
                bundle = await fetch_full_bundle(issue)
                if not FETCH_APPROVALS:
                    bundle["approvals"] = []
                bundles.append(bundle)

                if index % 50 == 0:
                    print(f"[full sync] fetched history for {index}/{len(issues)}")

            # 3. Map to canonical tickets
            canonical_tickets = map_jira_bundles_to_canonical(bundles)
            print(f"[full sync] mapped {len(canonical_tickets)} canonical tickets")

            # 4. Inject external data before rules run
            canonical_tickets = inject_external_data(canonical_tickets)

            # 5. Run rule engine (None -> "ALL" -> A, B, C, D, F, G in order)
            final_tickets = transform_canonical_tickets_full(
                canonical_tickets,
                rule,
            )
            print(f"[full sync] rules applied to {len(final_tickets)} tickets")

            # 6. Merge with existing file (append-only by ticket_key)
            existing_tickets = _load_existing(target)
            merged_tickets = _merge_by_ticket_key(existing_tickets, final_tickets)

            # 7. Write
            target.write_text(
                json.dumps(merged_tickets, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

            print(
                f"[full sync] wrote {len(merged_tickets)} tickets to {target.resolve()}"
            )
            return final_tickets

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Jira full sync failed: {str(e)}",
            )


# ---------------------------------------------------------------------------
# Full sync poller
# ---------------------------------------------------------------------------
# Use this if you want the full sync on a slow schedule (e.g. nightly).
# Do not use this for the 5-minute incremental poll.
# ---------------------------------------------------------------------------

async def jira_full_sync_poller(
    interval_hours: int = 24,
    initial_delay_seconds: int = 0,
):
    if initial_delay_seconds > 0:
        print(f"[full sync] first run delayed by {initial_delay_seconds}s")
        await asyncio.sleep(initial_delay_seconds)

    while True:
        try:
            await full_sync_jira()
        except Exception as e:
            print(f"[full sync] error: {e}")

        print(f"[full sync] sleeping for {interval_hours}h")
        await asyncio.sleep(interval_hours * 3600)


# ---------------------------------------------------------------------------
# Manual entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(full_sync_jira())