from fastapi import FastAPI, Request, APIRouter, HTTPException
import os
import httpx
from dotenv import load_dotenv
import connector_config

load_dotenv()

router = APIRouter(prefix="/infor", tags=["INFOR M3"])


def setting(name):
    value = os.getenv(name) or getattr(connector_config, name, None)
    if not value:
        raise HTTPException(503, f"Infor configuration missing: {name}")
    return value


# function to get the api token

async def get_infor_token(client):
    payload = {
        "grant_type": "password",
        "client_id": setting("INFOR_CLIENT_ID"),
        "client_secret": setting("INFOR_CLIENT_SECRET"),
        "username": setting("INFOR_USERNAME"),
        "password": setting("INFOR_PASSWORD"),
    }

    # sends login details to Infor and waits and gets response
    response = await client.post(
        setting("INFOR_TOKEN_URL"),
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    # checks if the http request has errors
    response.raise_for_status()
    return response.json()["access_token"] # Infor returns Json


@router.get("/purchase-orders/{puno}/lines")
async def get_purchase_order_lines(puno: str, request: Request):
    client = request.app.state.client
    token = await get_infor_token(client)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    
    }

    url = f"{setting('INFOR_BASE_URL').rstrip('/')}/PPS200MI/LstLine"

    response = await client.get(
        url,
        headers=headers, 
        params={"PUNO": puno}

    )

    response.raise_for_status()
    return response.json()


# now second infor endpoints customer order lines
# each endpoint should have one responsibility

@router.get("/customer-orders/{orno}/lines") 
async def get_customer_order_lines(orno:str, request:Request):
    client = request.app.state.client
    token = await get_infor_token(client)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    
    }

    url = f"{setting('INFOR_BASE_URL').rstrip('/')}/OIS100MI/LstLine"
    
    response = await client.get( 
        url,
        headers=headers, 
        params={"ORNO": orno}

    )

    response.raise_for_status()
    return response.json()


# Allow the ingestion endpoint to reuse the existing order routes.
async def fetch_order_lines(order_type: str, order_number: str, request: Request):
    try:
        if order_type == "purchase":
            return await get_purchase_order_lines(order_number, request)
        if order_type == "customer":
            return await get_customer_order_lines(order_number, request)
        raise HTTPException(422, "Order type must be purchase or customer.")
    except httpx.TimeoutException as exc:
        raise HTTPException(504, "Infor request timed out. Please retry.") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(502, f"Infor request failed (HTTP {exc.response.status_code}).") from exc
    except httpx.RequestError as exc:
        raise HTTPException(502, "Unable to connect to Infor.") from exc
    except (ValueError, KeyError, AttributeError) as exc:
        raise HTTPException(502, "Infor returned an invalid response.") from exc
