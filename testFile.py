import httpx
import asyncio 

async def call_my_api():
    async with httpx.AsyncClient() as client:
        # Make sure your FastAPI server is actually running on port 8000!
        response = await client.get("http://127.0.0.1:8000/my-jira-data")
        data = response.json()
        
        print(f"Projects found: {len(data['projects'])}")
        for issue in data.get('my_assigned_issues', []):
            print(f"Task: {issue['key']} - {issue['summary']}")

# 2. Use asyncio.run to execute the coroutine
if __name__ == "__main__":
    try:
        asyncio.run(call_my_api())
    except Exception as e:
        print(f"Connection failed: {e}.")