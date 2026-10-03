import asyncio
import json

import httpx
import pytest
from fastapi import BackgroundTasks, HTTPException, Request, FastAPI
from pydantic import ValidationError

from backend.app import main
from connectors import Infor_API_connector as infor
from mappers.infor_mapper import map_infor_response_to_canonical


@pytest.mark.parametrize('order_type,line_field', [('purchase', 'PNLI'), ('customer', 'PONR')])
def test_ingests_order_and_records_actual_output(monkeypatch, tmp_path, order_type, line_field):
    async def fetch(kind, number, request):
        assert (kind, number) == (order_type, '123')
        return {'results': [{'records': [{line_field: '1', 'ITNO': 'ITEM'}]}]}
    history = []
    monkeypatch.setattr(main, 'fetch_order_lines', fetch)
    monkeypatch.setattr(main, 'OUTPUT_FOLDER', tmp_path)
    monkeypatch.setattr(main, 'add_history_entry', lambda **entry: history.append(entry))
    result = asyncio.run(main.ingest_local_folder(main.IngestionRequest(
        connector='Infor Sales', order_type=order_type, order_number=' 123 ',
        rule='Infor Sales Rules', outputs='PostgreSQL', mapper='Sales Schema Mapper',
    ), BackgroundTasks(), Request({"type": "http", "app": main.app})))
    assert result['processed'] == 1
    documents = json.loads((tmp_path / f'infor_{order_type}_123.json').read_text())
    assert documents[0]['content']['ITNO'] == 'ITEM'
    assert documents[0]['tags'] == ['sales']
    assert history[0]['outputs'] == 'Local JSON'
    assert history[0]['status'] == 'completed'


@pytest.mark.parametrize('fields', [{}, {'order_type': 'customer', 'order_number': '../bad'},
                                   {'order_type': 'invalid', 'order_number': '123'}])
def test_invalid_infor_input(fields):
    with pytest.raises(ValidationError):
        main.IngestionRequest(connector='Infor Sales', **fields)


@pytest.mark.parametrize('payload', [{'results': [{'errorMessage': 'invalid order'}]},
                                    {'results': [{'records': None}]}, {}])
def test_rejects_failed_or_malformed_response(payload):
    with pytest.raises(HTTPException) as error:
        map_infor_response_to_canonical(payload, 'customer', '123')
    assert error.value.status_code == 502


def test_empty_order_is_valid():
    assert map_infor_response_to_canonical({'results': [{'records': []}]}, 'purchase', '123') == []


@pytest.mark.parametrize('kind,transaction,param', [('customer', 'OIS100MI', 'ORNO'),
                                                  ('purchase', 'PPS200MI', 'PUNO')])
def test_infor_authentication_and_transaction(monkeypatch, kind, transaction, param):
    for name in ['CLIENT_ID', 'CLIENT_SECRET', 'USERNAME', 'PASSWORD']:
        monkeypatch.setenv('INFOR_' + name, 'test-value')
    monkeypatch.setenv('INFOR_TOKEN_URL', 'https://infor.test/token')
    monkeypatch.setenv('INFOR_BASE_URL', 'https://infor.test/m3')
    def handler(request):
        if request.url.path == '/token':
            assert request.method == 'POST'
            return httpx.Response(200, json={'access_token': 'test-token'})
        assert request.url.path == f'/m3/{transaction}/LstLine'
        assert request.url.params[param] == '123'
        assert request.headers['Authorization'] == 'Bearer test-token'
        return httpx.Response(200, json={'results': [{'records': []}]})
    real_client = httpx.AsyncClient
    monkeypatch.setattr(infor.httpx, 'AsyncClient', lambda **kwargs: real_client(
        transport=httpx.MockTransport(handler), **kwargs))
    async def run():
        app = FastAPI()
        async with infor.httpx.AsyncClient() as client:
            app.state.client = client
            return await infor.fetch_order_lines(kind, '123', Request({'type': 'http', 'app': app}))
    assert asyncio.run(run()) == {'results': [{'records': []}]}


def test_upstream_failure_does_not_write_output_or_history(monkeypatch, tmp_path):
    async def fail(*args):
        raise HTTPException(502, 'Infor request failed.')
    monkeypatch.setattr(main, 'fetch_order_lines', fail)
    monkeypatch.setattr(main, 'OUTPUT_FOLDER', tmp_path)
    monkeypatch.setattr(main, 'add_history_entry', lambda **kwargs: pytest.fail('Unexpected history'))
    with pytest.raises(HTTPException):
        asyncio.run(main.ingest_local_folder(main.IngestionRequest(
            connector='Infor Sales', order_type='purchase', order_number='123',
        ), BackgroundTasks(), Request({"type": "http", "app": main.app})))
    assert list(tmp_path.iterdir()) == []


def test_http_validation_and_registered_raw_route(monkeypatch):
    from fastapi.testclient import TestClient
    async def token(client):
        return 'test-token'
    class Client:
        async def get(self, url, **kwargs):
            return httpx.Response(200, json={'records': [{'ORNO': kwargs['params']['ORNO']}]},
                                  request=httpx.Request('GET', url))
    monkeypatch.setenv('INFOR_BASE_URL', 'https://infor.test/m3')
    monkeypatch.setattr(infor, 'get_infor_token', token)
    monkeypatch.setattr(main.app.state, 'client', Client(), raising=False)
    client = TestClient(main.app)
    response = client.post('/api/ingest/local-folder', json={'connector': 'Infor Sales'})
    assert response.status_code == 422
    response = client.get('/infor/customer-orders/123/lines')
    assert response.status_code == 200
    assert response.json()['records'][0]['ORNO'] == '123'


def test_missing_credentials_report_configuration_error(monkeypatch):
    from unittest.mock import AsyncMock
    for name in ['CLIENT_ID', 'CLIENT_SECRET', 'USERNAME', 'PASSWORD']:
        monkeypatch.setenv('INFOR_' + name, 'test-value')
    monkeypatch.delenv('INFOR_TOKEN_URL', raising=False)
    monkeypatch.delattr(infor.connector_config, 'INFOR_TOKEN_URL', raising=False)
    with pytest.raises(HTTPException) as error:
        asyncio.run(infor.get_infor_token(AsyncMock()))
    assert error.value.status_code == 503
    assert 'INFOR_TOKEN_URL' in error.value.detail
