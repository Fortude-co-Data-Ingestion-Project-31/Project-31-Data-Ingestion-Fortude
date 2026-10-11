"""Save demo records using the team's MongoDB adapter, plus run history."""
from datetime import datetime, timezone
from uuid import uuid4
from pymongo.errors import PyMongoError

from app.outputs.MongoDB.mongo_db_common_func import persist
from app.outputs.MongoDB.mongo_db_output import get_db


async def save_run(documents, tenant, company, order_type, order_number, policy):
    """Save current records and separate snapshots; only then mark the run complete."""
    db = get_db()
    run_id = str(uuid4())
    summary = {
        'run_id': run_id, 'tenant': tenant, 'company': company,
        'order_type': order_type, 'order_number': order_number,
        'client_id': policy['client_id'], 'is_demo': True,
        'policy_version': policy['policy_version'],
        'records_processed': len(documents),
        'records_with_findings': sum(
            doc['rule_results']['E-01']['status'] == 'fail' for doc in documents),
    }
    await db['infor_demo_runs'].insert_one({
        '_id': run_id, **summary, 'status': 'running',
        'created_at': datetime.now(timezone.utc),
    })
    try:
        # Mongo's built-in unique _id prevents duplicate current records on replay.
        stored = [{**doc, '_id': doc['document_id']} for doc in documents]
        counts = await persist('infor_demo', stored)
        # Store each snapshot separately to avoid putting a whole order in one document.
        for doc in documents:
            await db['infor_demo_results'].insert_one({
                '_id': run_id + ':' + doc['document_id'],
                'run_id': run_id, **doc,
            })
        await db['infor_demo_runs'].update_one(
            {'_id': run_id}, {'$set': {'status': 'completed', 'storage': counts}})
    except PyMongoError:
        # Standalone MongoDB writes are not one transaction: preserve failure evidence.
        try:
            await db['infor_demo_runs'].update_one(
                {'_id': run_id}, {'$set': {'status': 'failed'}})
        except PyMongoError:
            pass  # If Mongo is offline, the original run remains marked running.
        raise
    return {**summary, 'storage': counts}


async def read_run(run_id):
    """Read the stored run and its original record snapshots for the demo."""
    db = get_db()
    run = await db['infor_demo_runs'].find_one({'_id': run_id}, {'_id': 0})
    if run is None:
        return None
    run['documents'] = await db['infor_demo_results'].find(
        {'run_id': run_id}, {'_id': 0}).to_list(length=None)
    return run
