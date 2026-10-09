# Infor → mapping → completeness rule → MongoDB demo

This demo supports purchase and customer order lines. It uses the existing MongoDB
connection (`MONGO_URI`, `MONGO_DB_NAME`) and Infor environment settings. It does
not demonstrate SQL storage, inventory ingestion, or all Case E business rules.
Every new Python function has an explanatory docstring or comment.

## Run the demo

1. Start MongoDB or use the team's configured MongoDB server. Ensure your backend
   environment loads the existing connection settings before application startup.
2. From `backend`, start `python -m uvicorn app.main:app --reload` using your project
   Python environment.
3. Open http://127.0.0.1:8000/docs and expand **Infor MongoDB Demo**.
4. Execute **POST /api/infor/mongo/ingest** with a valid order, for example the order
   previously retrieved from the training environment:

```json
{"order_type":"purchase","order_number":"11","company":"780"}
```

For the previously retrieved customer order, use:

```json
{"order_type":"customer","order_number":"0010000017","company":"780"}
```

These examples still require valid credentials, permission, and orders present in
that tenant. Order numbers are strings to preserve leading zeroes.

5. Show `documents`, `records_processed`, `records_with_findings`, and the saved
   `run_id`. A completed response means database writes finished, not that every
   business rule passed.
6. Use **GET /api/infor/mongo/runs/{run_id}** with that ID. This reads the stored
   snapshot back from MongoDB, demonstrating persistence.
7. In MongoDB Compass, open the configured database and inspect:
   - `infor_demo_records`: latest canonical order lines, raw `content`, rule results.
   - `infor_demo_runs`: timestamps, counts, policy version, and run status.
   - `infor_demo_results`: record and rule snapshots from each run.
8. Execute the same request again: current records update using stable IDs, while
   a new run and snapshots preserve history.

## Rules and limits

`backend/app/rules/infor_rules/demo_policy.json` holds example mandatory fields:
order number, line number, item code, ordered quantity. Missing/blank values fail
E-01; zero quantity is valid. Incomplete records are stored so findings can be
reviewed. Unusable identifiers or invalid quantities stop ingestion before writes.
E-02 through E-07 are explicitly `not_evaluated`. This policy is a student demo,
not client-approved business requirements. The demo route applies this check
directly; it does not change existing pipeline rule-handler behavior.

Each run keeps a snapshot, but this is not a reporting dashboard. MongoDB writes
across collections are not transactional: a database failure can leave partial
records and a failed/running run. Only completed runs represent successful
persistence of all snapshots. Retry the request after fixing the database.

## Verification

From `backend`:

```sh
python -m pytest tests/test_infor_mongo_demo.py tests/test_infor_optional_config.py tests/test_rule_handlers.py -q
```

Tests use simulated Infor HTTP and an in-memory MongoDB test double while running
the real connector, mapper, completeness rule, and common persistence adapter.
They check both order types, missing-field findings, zero quantities, repeat runs,
read-back history, malformed responses, database failure, and request validation.
A live Swagger run is still needed to verify credentials and MongoDB connectivity.
