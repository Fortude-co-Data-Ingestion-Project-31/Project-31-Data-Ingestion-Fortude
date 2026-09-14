from fastapi import FastAPI, HTTPException, Query
from contextlib import asynccontextmanager
import httpx
import base64
from connector_config import JIRA_BASE_URL,JIRA_EMAIL,JIRA_API_TOKEN
from pydantic import BaseModel

class JiraSearch(BaseModel):
    jql: str
    max_results: int = 50

def auth_header():
    return httpx.BasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)

async def get_my_issues():
    """
    Fetch issues assigned to the authenticated user from Jira.
    """
    
    url=f"{JIRA_BASE_URL}rest/api/3/search/jql"
    jql="updated >= -10m ORDER BY updated ASC",
    params = {
        "jql": jql,
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
        
async def get_jira_fields():
    """
    Fetch all Jira field metadata including custom fields.
    """

    url = f"{JIRA_BASE_URL}rest/api/3/field"

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
        
async def get_issue_changelog(issue_key: str):
    url = f"{JIRA_BASE_URL}rest/api/3/issue/{issue_key}/changelog"
    values = []
    start_at = 0

    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(
                url,
                params={"startAt": start_at, "maxResults": 100},
                auth=auth_header(),
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            batch = data.get("values", [])
            values.extend(batch)

            if start_at + len(batch) >= data.get("total", 0):
                break
            start_at += len(batch)

    return values


async def get_issue_comments(issue_key: str):
    url = f"{JIRA_BASE_URL}rest/api/3/issue/{issue_key}/comment"
    values = []
    start_at = 0

    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(
                url,
                params={"startAt": start_at, "maxResults": 100},
                auth=auth_header(),
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            batch = data.get("comments", [])
            values.extend(batch)

            if start_at + len(batch) >= data.get("total", 0):
                break
            start_at += len(batch)

    return values


async def get_issue_worklogs(issue_key: str):
    url = f"{JIRA_BASE_URL}rest/api/3/issue/{issue_key}/worklog"
    values = []
    start_at = 0

    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(
                url,
                params={"startAt": start_at, "maxResults": 100},
                auth=auth_header(),
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            batch = data.get("worklogs", [])
            values.extend(batch)

            if start_at + len(batch) >= data.get("total", 0):
                break
            start_at += len(batch)

    return values

# ---------------------------------------------------------------------------
# optional approvals endpoint (JSM only)
# ---------------------------------------------------------------------------

async def get_issue_approvals(issue_key: str):
    """
    Returns approvals for Jira Service Management change tickets.
    Returns an empty list if the issue is not a JSM request or the
    endpoint is not available on this instance.
    """
    url = f"{JIRA_BASE_URL}rest/servicedeskapi/request/{issue_key}/approval"
    values = []
    start_at = 0

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            while True:
                response = await client.get(
                    url,
                    params={"startAt": start_at, "limit": 100},
                    auth=auth_header(),
                    headers={"Accept": "application/json"},
                )

                if response.status_code in (400, 403, 404):
                    return []

                response.raise_for_status()
                data = response.json()
                batch = data.get("values", [])
                values.extend(batch)

                if data.get("isLastPage", True) or not batch:
                    break
                start_at += len(batch)

        except Exception:
            return []

    return values

# ---------------------------------------------------------------------------
# paginated full search
# ---------------------------------------------------------------------------

async def search_all_issues():
    """
    Fetch every issue the API user can see for the given JQL.
    Uses cursor pagination on Jira Cloud's new search endpoint.
    """
    url = f"{JIRA_BASE_URL}rest/api/3/search/jql"
    jql = "project IS NOT EMPTY ORDER BY updated ASC"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    issues = []
    next_token = None
    page = 0

    async with httpx.AsyncClient(timeout=120) as client:
        while True:
            body = {
                "jql": jql,
                "maxResults": 100,
                "fields":["*all"],
            }
            if next_token:
                body["nextPageToken"] = next_token

            response = await client.post(
                url,
                json=body,
                auth=auth_header(),
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            batch = data.get("issues", [])
            issues.extend(batch)
            page += 1

            print(f"  search page {page}: +{len(batch)} issues (total {len(issues)})")

            next_token = data.get("nextPageToken")
            if not next_token:
                break

    return issues


# ---------------------------------------------------------------------------
# one call to fetch everything for one issue
# ---------------------------------------------------------------------------

async def fetch_full_bundle(issue):
    """
    Given one search result, fetch changelog, comments, worklogs,
    and approvals. Returns a bundle the mapper can consume.
    """
    key = issue["key"]

    return {
        "issue": issue,
        "changelog": await get_issue_changelog(key),
        "comments": await get_issue_comments(key),
        "worklogs": await get_issue_worklogs(key),
        "approvals": await get_issue_approvals(key),
    }