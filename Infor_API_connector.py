from fastapi import FastAPI, Request, APIRouter
import connector_config

router = APIRouter(prefix="/infor", tags=["INFOR M3"])


# function to get the api token

async def get_infor_token(client):
    payload = {
        "grant_type": "password",
        "client_id": connector_config.INFOR_CLIENT_ID,
        "client_secret": connector_config.INFOR_CLIENT_SECRET,
        "username": connector_config.INFOR_USERNAME,
        "password": connector_config.INFOR_PASSWORD,
    }

    # sends login details to Infor and waits and gets response
    response = await client.post(
        connector_config.INFOR_TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    # checks if the http request has errors
    response.raise_for_status()
    return response.json()["access_token"] # Infor returns Json






