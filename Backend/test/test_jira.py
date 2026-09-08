import asyncio
import sys
sys.path.append('.')
from Backend.app.connectors.Jira_API_connector import get_my_issues

async def main():
    try:
        data = await get_my_issues()
        issues = data.get("issues", [])
        print(f"Found {len(issues)} issues")
        for i in issues:
            print("-", i.get("key"), i.get("fields", {}).get("issuetype", {}).get("name"))
    except Exception as e:
        print("Error:", e)

asyncio.run(main())
