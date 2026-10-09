"""Infor -> canonical records -> demo E-01 -> MongoDB, exposed through Swagger."""
from pymongo.errors import PyMongoError
from math import isfinite
from urllib.parse import quote
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.connectors.Infor_API_connector import fetch_order_lines, setting
from app.mappers.infor_mapper import map_infor_response
from app.rules.infor_rules.demo_completeness import load_demo_policy, apply_demo_completeness
from app.outputs.infor_mongo import save_run, read_run

router = APIRouter(prefix='/api/infor/mongo', tags=['Infor MongoDB Demo'])


class InforMongoRequest(BaseModel):
    """Require an explicit company so orders from different companies cannot collide."""
    order_type: Literal['purchase', 'customer']
    order_number: str = Field(min_length=1, max_length=50, pattern=r'^[A-Za-z0-9_-]+$')
    company: str = Field(min_length=1, max_length=10, pattern=r'^[0-9]+$')


def map_and_check(payload, order_type, tenant, company, order_number):
    """Validate the complete response, map every line, and run the demo policy."""
    if not isinstance(payload, dict) or payload.get('wasTerminated'):
        raise ValueError('Infor returned an invalid or terminated response.')
    documents = map_infor_response(payload, order_type, tenant, order_number)
    policy = load_demo_policy()
    seen = set()
    for document in documents:
        raw = document['content']
        # Do not silently store a record under a different company or order.
        for field, expected in [('CONO', company),
                                ('PUNO' if order_type == 'purchase' else 'ORNO', order_number)]:
            if raw.get(field) not in (None, '') and str(raw[field]).strip() != expected:
                raise ValueError(f'Infor {field} does not match the requested value.')
        document['company'] = company
        parts = [tenant, company, policy['client_id'], order_type, order_number,
                 str(document['line_number']).strip(), str(document['line_suffix']).strip()]
        document['document_id'] = 'infor_m3:' + ':'.join(quote(p, safe='') for p in parts)
        if document['document_id'] in seen:
            raise ValueError('Infor returned the same line identity more than once.')
        seen.add(document['document_id'])
        for field in ('ordered_quantity', 'received_quantity', 'delivered_quantity', 'invoiced_quantity'):
            value = document.get(field)
            if value is not None and not isfinite(value):
                raise ValueError(f'Invalid numeric value for {field}.')
        apply_demo_completeness(document, policy)
    return documents, policy


@router.post('/ingest')
async def ingest_infor_mongo(body: InforMongoRequest, request: Request):
    """Fetch a real Infor order, evaluate demo completeness, and persist it to MongoDB.

    Failed completeness checks are saved for review. API or malformed-data errors
    stop the run before MongoDB writes. Missing credentials never fall back to fake data.
    """
    tenant = setting('INFOR_TENANT')
    payload = await fetch_order_lines(body.order_type, body.order_number, request, body.company)
    try:
        documents, policy = map_and_check(payload, body.order_type, tenant, body.company, body.order_number)
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(502, str(exc)) from exc
    try:
        summary = await save_run(documents, tenant, body.company,
                                 body.order_type, body.order_number, policy)
    except PyMongoError as exc:
        raise HTTPException(503, 'Could not save the Infor run to MongoDB.') from exc
    return {'status': 'completed', **summary, 'documents': documents}


@router.get('/runs/{run_id}')
async def get_infor_mongo_run(run_id: str):
    """Read persisted results back from MongoDB, rather than echoing an ingestion response."""
    try:
        result = await read_run(run_id)
    except PyMongoError as exc:
        raise HTTPException(503, 'Could not read the Infor run from MongoDB.') from exc
    if result is None:
        raise HTTPException(404, 'Infor MongoDB run not found.')
    return result
