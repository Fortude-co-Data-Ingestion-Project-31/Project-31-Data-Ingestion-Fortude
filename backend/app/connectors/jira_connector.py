import os

import httpx


class JiraConnectorError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


def read_jira_issues():
    base_url = os.getenv("JIRA_BASE_URL")
    email = os.getenv("JIRA_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")

    if not base_url or not email or not api_token:
        missing = [
            name
            for name, value in (
                ("JIRA_BASE_URL", base_url),
                ("JIRA_EMAIL", email),
                ("JIRA_API_TOKEN", api_token),
            )
            if not value
        ]
        raise JiraConnectorError(
            f"Missing Jira configuration: {', '.join(missing)}."
        )

    url = f"{base_url.rstrip('/')}/rest/api/3/search/jql"
    response = httpx.get(
        url,
        params={
            "jql": "project = KAN order by created DESC",
            "maxResults": 100,
            "fields": "*all",
        },
        auth=(email, api_token),
        headers={"Accept": "application/json"},
        timeout=30.0,
    )
    if response.is_error:
        raise JiraConnectorError(
            f"Jira returned HTTP {response.status_code}: {response.text}",
            status_code=response.status_code,
        )
    return response.json().get("issues", [])