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

def auth_header():
    return httpx.BasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)

@app.get("/jira/authentication_check")
async def jira_me():

    url = JIRA_BASE_URL.rstrip("/") + "/rest/api/3/myself"

    client = app.state.client

    response = await client.get(
        url,
        auth=auth_header(),
        headers={"Accept": "application/json"}
    )
    response.raise_for_status()

    return response.json()

@app.get("/jira/my_issues")
async def get_my_issues():
    """
    Fetch issues assigned to the authenticated user from Jira.
    """
    
    url = JIRA_BASE_URL.rstrip("/") + "/rest/api/3/search/jql"
    
    params = {
        "jql": "project = KAN order by created DESC",
        "maxResults": 5000,
        "fields": "*all"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                params = params,
                auth = auth_header(),
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
        
@app.get("/jira/get_fields")
async def get_jira_fields():
    """
    Fetch all Jira field metadata including custom fields.
    """

    url = JIRA_BASE_URL.rstrip("/") + "/rest/api/3/field"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                auth=auth_header(),
                headers={"Accept": "application/json"}
            )

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