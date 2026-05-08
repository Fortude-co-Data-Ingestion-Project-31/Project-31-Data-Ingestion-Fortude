from fastapi import FastAPI, Request, HTTPException, Depends
from contextlib import asynccontextmanager
import httpx
import base64
from typing import Optional, Dict, Any

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create a single client for the whole app life to improve performance
    app.state.client = httpx.AsyncClient(timeout=30.0)
    yield
    await app.state.client.aclose()

app = FastAPI(lifespan=lifespan)

def extract_auth_header(request: Request) -> tuple[str, str]:
    """
    Extract Basic Auth credentials from the request header
    Returns (email, token) tuple
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    try:
        # Decode base64 credentials
        encoded_credentials = auth_header.split(" ")[1]
        decoded_bytes = base64.b64decode(encoded_credentials)
        decoded_string = decoded_bytes.decode("utf-8")
        email, token = decoded_string.split(":", 1)
        return email, token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Authorization format: {str(e)}")

def jira_headers(email: str, token: str) -> Dict[str, str]:
    """Generate JIRA API headers with Basic Auth"""
    auth_bytes = f"{email}:{token}".encode("ascii")
    auth_base64 = base64.b64encode(auth_bytes).decode("ascii")
    
    return {
        "Authorization": f"Basic {auth_base64}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

async def fetch_user_accessible_projects(client: httpx.AsyncClient, base_url: str, headers: Dict[str, str]) -> list:
    """Fetch all projects accessible to the authenticated user"""
    response = await client.get(f"{base_url}/project", headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, 
            detail=f"Failed to fetch projects: {response.text}"
        )
    
    return response.json()

async def fetch_user_issues(client: httpx.AsyncClient, base_url: str, headers: Dict[str, str]) -> list:
    """Fetch all issues assigned to the current user"""
    # You can modify the JQL to get different issue sets
    jql = "assignee = currentUser() ORDER BY updated DESC"
    
    all_issues = []
    start_at = 0
    max_results = 100
    
    while True:
        response = await client.get(
            f"{base_url}/search",
            headers=headers,
            params={
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "*all"  # Get all fields for each issue
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch issues: {response.text}"
            )
        
        data = response.json()
        issues = data.get("issues", [])
        all_issues.extend(issues)
        
        # Check if we've fetched all issues
        if len(issues) < max_results or start_at + max_results >= data.get("total", 0):
            break
        
        start_at += max_results
    
    return all_issues

def extract_project_details(projects_data: list) -> list:
    """Extract relevant project details"""
    return [
        {
            "id": p.get("id"),
            "key": p.get("key"),
            "name": p.get("name"),
            "project_type": p.get("projectTypeKey"),
            "lead": p.get("lead", {}).get("displayName"),
            "url": p.get("self"),
            "description": p.get("description", "No description")
        }
        for p in projects_data
    ]

def extract_issue_details(issues_data: list) -> list:
    """Extract comprehensive issue details"""
    extracted_issues = []
    
    for issue in issues_data:
        fields = issue.get("fields", {})
        
        # Extract issue details
        issue_info = {
            "id": issue.get("id"),
            "key": issue.get("key"),
            "url": issue.get("self"),
            "summary": fields.get("summary", "No summary"),
            "status": fields.get("status", {}).get("name"),
            "status_category": fields.get("status", {}).get("statusCategory", {}).get("name"),
            "priority": fields.get("priority", {}).get("name"),
            "issue_type": fields.get("issuetype", {}).get("name"),
            "project": {
                "id": fields.get("project", {}).get("id"),
                "key": fields.get("project", {}).get("key"),
                "name": fields.get("project", {}).get("name")
            },
            "assignee": {
                "email": fields.get("assignee", {}).get("emailAddress"),
                "display_name": fields.get("assignee", {}).get("displayName"),
                "account_id": fields.get("assignee", {}).get("accountId")
            } if fields.get("assignee") else None,
            "reporter": {
                "email": fields.get("reporter", {}).get("emailAddress"),
                "display_name": fields.get("reporter", {}).get("displayName"),
                "account_id": fields.get("reporter", {}).get("accountId")
            } if fields.get("reporter") else None,
            "created": fields.get("created"),
            "updated": fields.get("updated"),
            "resolution": fields.get("resolution", {}).get("name") if fields.get("resolution") else None,
            "labels": fields.get("labels", []),
            "description": fields.get("description", "No description"),
            "environment": fields.get("environment", "No environment specified"),
            "due_date": fields.get("duedate"),
            "watches": fields.get("watches", {}).get("watchCount", 0),
            "time_estimate": fields.get("timeestimate"),
            "time_spent": fields.get("timespent"),
            "aggregate_progress": fields.get("aggregateprogress", {}),
            "work_ratio": fields.get("workratio", 0)
        }
        
        extracted_issues.append(issue_info)
    
    return extracted_issues

@app.get("/my-jira-data")
async def get_user_data(request: Request):
    """
    Get all JIRA projects and issues assigned to the authenticated user
    Uses Basic Auth from the request header
    """
    try:
        # Extract credentials from request
        email, token = extract_auth_header(request)
        
        # Use the shared client from lifespan
        client = request.app.state.client
        
        # Construct JIRA API base URL
        # You might want to get this from a config or allow the user to provide it
        from connector_config import JIRA_BASE_URL
        base_url = f"{JIRA_BASE_URL}/rest/api/3"
        
        # Generate headers for JIRA API
        headers = jira_headers(email, token)
        
        # Fetch data in parallel for better performance
        import asyncio
        projects_task = fetch_user_accessible_projects(client, base_url, headers)
        issues_task = fetch_user_issues(client, base_url, headers)
        
        projects_data, issues_data = await asyncio.gather(projects_task, issues_task)
        
        # Extract and structure the response
        return {
            "authenticated_user": email,
            "statistics": {
                "total_projects": len(projects_data),
                "total_assigned_issues": len(issues_data),
                "active_issues": sum(1 for i in issues_data 
                                   if i.get("fields", {}).get("status", {}).get("statusCategory", {}).get("name") != "Done")
            },
            "projects": extract_project_details(projects_data),
            "assigned_issues": extract_issue_details(issues_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/my-projects")
async def get_user_projects(request: Request):
    """Get only projects accessible to the authenticated user"""
    try:
        email, token = extract_auth_header(request)
        client = request.app.state.client
        
        from connector_config import JIRA_BASE_URL
        base_url = f"{JIRA_BASE_URL}/rest/api/3"
        headers = jira_headers(email, token)
        
        projects_data = await fetch_user_accessible_projects(client, base_url, headers)
        
        return {
            "user": email,
            "total_projects": len(projects_data),
            "projects": extract_project_details(projects_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/my-issues")
async def get_user_issues(request: Request, status: Optional[str] = None):
    """Get issues assigned to the authenticated user with optional status filter"""
    try:
        email, token = extract_auth_header(request)
        client = request.app.state.client
        
        from connector_config import JIRA_BASE_URL
        base_url = f"{JIRA_BASE_URL}/rest/api/3"
        headers = jira_headers(email, token)
        
        # Modify JQL based on status filter
        jql = "assignee = currentUser()"
        if status:
            jql += f" AND status = '{status}'"
        jql += " ORDER BY updated DESC"
        
        all_issues = []
        start_at = 0
        max_results = 100
        
        while True:
            response = await client.get(
                f"{base_url}/search",
                headers=headers,
                params={
                    "jql": jql,
                    "startAt": start_at,
                    "maxResults": max_results,
                    "fields": "*all"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch issues")
            
            data = response.json()
            issues = data.get("issues", [])
            all_issues.extend(issues)
            
            if len(issues) < max_results or start_at + max_results >= data.get("total", 0):
                break
            
            start_at += max_results
        
        return {
            "user": email,
            "jql_query": jql,
            "total_issues": len(all_issues),
            "issues": extract_issue_details(all_issues)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))