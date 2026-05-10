from fastapi import FastAPI, HTTPException, Query
from contextlib import asynccontextmanager
import httpx
import base64
from connector_config import JIRA_BASE_URL,JIRA_EMAIL,JIRA_API_TOKEN
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

@app.get("/jira/my_issues")
async def get_my_issues():
    """
    Fetch issues assigned to the authenticated user from Jira.
    """
    JIRA_AUTH = httpx.BasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    url=JIRA_BASE_URL+"rest/api/3/search/jql"
    
    params = {
        "jql": "assignee = currentUser()",
        "maxResults": 5000,
        "fields": "*all"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                params=params,
                auth=JIRA_AUTH,
                headers={"Accept": "application/json"}
            )
            
            # If Jira returns an error (401, 404, etc), raise it for FastAPI to handle
            response.raise_for_status()
            
            return response.json()

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, 
                detail=f"Jira API error: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Internal Server Error: {str(e)}"
            )