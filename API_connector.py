from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import httpx
import base64
import connector_config
from pydantic import BaseModel

class JiraSearch(BaseModel):
    jql: str
    max_results: int = 50

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = httpx.AsyncClient(timeout=30.0)
    yield
    await app.state.client.aclose()

app = FastAPI(lifespan=lifespan)

def jira_headers():
    email = connector_config.JIRA_EMAIL
    token = connector_config.JIRA_API_TOKEN
    auth = base64.b64encode(f"{email}:{token}".encode()).decode()

    return {
        "Authorization": f"Basic {auth}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

@app.get("/jira/issues/{issue_key}")
async def get_issue(issue_key: str, request: Request):
    client = request.state.client
    url = f"{connector_config.JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"

    resp = await client.get(url, headers=jira_headers())
    resp.raise_for_status()
    return resp.json()

@app.post("/jira/search")
async def search_jira(data: JiraSearch, request: Request):
    client = request.state.client
    url = f"{connector_config.JIRA_BASE_URL}/rest/api/3/search"

    payload = {
        "jql": data.jql,
        "maxResults": data.max_results
    }

    resp = await client.post(url, json=payload, headers=jira_headers())
    resp.raise_for_status()
    return resp.json()