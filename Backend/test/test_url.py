import asyncio
import httpx

async def main():
    url = "https://sairamishetty58.atlassian.net/rest/api/3/search/jql"
    print(f"Testing url: {url}")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            print(resp.status_code)
        except Exception as e:
            print("Error:", repr(e))

asyncio.run(main())
