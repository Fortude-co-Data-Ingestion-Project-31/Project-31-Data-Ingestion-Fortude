"""Verify HTTP, mock Infor, real mapping/rules/adapter, and an in-memory Mongo test double."""
from copy import deepcopy
from types import SimpleNamespace
from pymongo.errors import ConnectionFailure
from contextlib import asynccontextmanager
import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.services.infor_mongo_demo import router
from app.outputs import infor_mongo


@pytest.fixture
def demo(monkeypatch, tmp_path):
    """Mock external HTTP and MongoDB; retain the connector, mapper, rules and adapter."""
    db = FakeDB()
    monkeypatch.setattr(infor_mongo, 'get_db', lambda: db)
    from app.outputs.MongoDB import mongo_db_common_func
    monkeypatch.setattr(mongo_db_common_func, 'get_db', lambda: db)
    for name in ('TENANT','CLIENT_ID','CLIENT_SECRET','USERNAME','PASSWORD'):
        monkeypatch.setenv('INFOR_' + name, 'TEST')
    monkeypatch.setenv('INFOR_TOKEN_URL', 'https://infor.test/token')
    monkeypatch.setenv('INFOR_BASE_URL', 'https://infor.test/execute')
    state = {'payload': None, 'fail': False, 'calls': [], 'db': db}
    def upstream(request):
        """Check authentication and explicit company before returning test records."""
        state['calls'].append(request)
        if request.url.path == '/token':
            return httpx.Response(200, json={'access_token':'test-token'})
        assert request.url.params['cono'] == '780'
        assert request.headers['Authorization'] == 'Bearer test-token'
        return httpx.Response(500) if state['fail'] else httpx.Response(200, json=state['payload'])
    @asynccontextmanager
    async def lifespan(app):
        """Supply the shared client expected by the actual connector."""
        async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
            app.state.client = client
            yield
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    with TestClient(app) as client:
        yield client, state


def payload(kind, missing=False):
    """Return clearly synthetic order lines including a valid zero quantity."""
    line, suffix, qty = ('PNLI','PNLS','ORQA') if kind == 'purchase' else ('PONR','POSX','ORQT')
    return {'nrOfFailedTransactions':0, 'wasTerminated':False, 'results':[{'records':[
        {line:'1', suffix:'0', qty:'0', 'ITNO':'DEMO_ITEM'},
        {line:'2', suffix:'0', qty:'10', 'ITNO':'' if missing else 'DEMO_ITEM_2'}]}]}


@pytest.mark.parametrize('kind', ['purchase','customer'])
def test_full_flow_and_replay(demo, kind):
    """Keep failed completeness records, all lines, and historical results on replay."""
    client, state = demo
    state['payload'] = payload(kind, True)
    body = {'order_type':kind, 'order_number':'0017', 'company':'780'}
    response = client.post('/api/infor/mongo/ingest', json=body)
    assert response.status_code == 200, response.text
    output = response.json()
    assert output['records_processed'] == 2 and output['records_with_findings'] == 1
    assert output['documents'][0]['rule_results']['E-01']['status'] == 'pass'
    assert output['documents'][1]['rule_results']['E-01']['missing_fields'] == ['item_code']
    assert output['documents'][1]['rule_results']['E-02']['status'] == 'not_evaluated'
    saved = client.get('/api/infor/mongo/runs/' + output['run_id']).json()
    assert len(saved['documents']) == 2
    state['payload'] = payload(kind)
    assert client.post('/api/infor/mongo/ingest', json=body).status_code == 200
    assert len(state['db']['infor_demo_records'].rows) == 2
    assert len(state['db']['infor_demo_runs'].rows) == 2
    assert len(state['db']['infor_demo_results'].rows) == 4
    assert client.get('/api/infor/mongo/runs/' + output['run_id']).json()['records_with_findings'] == 1


@pytest.mark.parametrize('problem', ['upstream','terminated','mismatch','invalid_quantity'])
def test_failed_input_writes_nothing(demo, problem):
    """Unusable upstream results cannot create a successful MongoDB run."""
    client, state = demo
    state['payload'] = payload('purchase')
    if problem == 'upstream': state['fail'] = True
    if problem == 'terminated': state['payload']['wasTerminated'] = True
    if problem == 'mismatch': state['payload']['results'][0]['records'][0]['CONO'] = '999'
    if problem == 'invalid_quantity': state['payload']['results'][0]['records'][0]['ORQA'] = 'nan'
    response = client.post('/api/infor/mongo/ingest', json={'order_type':'purchase','order_number':'0017','company':'780'})
    assert response.status_code == 502
    assert not state['db']['infor_demo_runs'].rows


def test_database_failure(demo, monkeypatch):
    """MongoDB errors return 503 instead of falsely reporting completed storage."""
    client, state = demo
    state['payload'] = payload('purchase')
    def fail():
        """Simulate an unavailable database."""
        raise ConnectionFailure('unavailable')
    monkeypatch.setattr(infor_mongo, 'get_db', fail)
    response = client.post('/api/infor/mongo/ingest', json={'order_type':'purchase','order_number':'0017','company':'780'})
    assert response.status_code == 503


def test_invalid_request(demo):
    """Request validation happens before Infor calls; absent runs return 404."""
    client, state = demo
    assert client.post('/api/infor/mongo/ingest', json={'order_type':'other'}).status_code == 422
    assert not state['calls']
    assert client.get('/api/infor/mongo/runs/unknown').status_code == 404


class FakeCursor:
    """Small test double for the Mongo cursor used by history reads."""
    def __init__(self, rows):
        """Keep independent copies, like database reads."""
        self.rows = deepcopy(rows)

    async def to_list(self, length=None):
        """Return the matching snapshots."""
        return self.rows


class FakeCollection:
    """Implement only the Motor operations exercised by this integration test."""
    def __init__(self):
        """Start an empty collection."""
        self.rows = {}

    async def insert_one(self, row):
        """Store a new document and reject duplicate IDs."""
        assert row['_id'] not in self.rows
        self.rows[row['_id']] = deepcopy(row)

    def find(self, query, projection=None):
        """Filter records and support exclusion of the Mongo ID."""
        rows = [deepcopy(r) for r in self.rows.values()
                if all(r.get(k) == v for k, v in query.items())]
        if projection and projection.get('_id') == 0:
            for row in rows:
                row.pop('_id', None)
        return FakeCursor(rows)

    async def find_one(self, query, projection=None):
        """Return the first matching document or None."""
        rows = self.find(query, projection).rows
        return rows[0] if rows else None

    async def replace_one(self, query, row, upsert=False):
        """Model the insert/update counts returned by the common adapter."""
        old = await self.find_one(query)
        self.rows[row['_id']] = deepcopy(row)
        return SimpleNamespace(upserted_id=None if old else row['_id'],
                               modified_count=int(old is not None and old != row),
                               matched_count=int(old is not None))

    async def update_one(self, query, update):
        """Apply the status fields used for run tracking."""
        row = await self.find_one(query)
        self.rows[row['_id']].update(deepcopy(update['$set']))


class FakeDB(dict):
    """Create in-memory collections when the adapter asks for them."""
    def __missing__(self, key):
        """Cache a new collection."""
        self[key] = FakeCollection()
        return self[key]
