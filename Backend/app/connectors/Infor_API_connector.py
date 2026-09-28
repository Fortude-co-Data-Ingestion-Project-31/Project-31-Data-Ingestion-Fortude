from fastapi import FastAPI, Request, APIRouter, Query
from app import connector_config

router = APIRouter(prefix="/infor", tags=["INFOR M3"])


@router.get("/inventory/by-order/{order_number}")
async def get_inventory_by_order(
    order_number: str,
    company: str,
    request: Request,
    warehouse: str,
    item_code: str,
    line_number: str | None = None,
    line_suffix: str | None = None,
    transaction_type: str | None = None,
    maxrecs: int = Query(default=20, ge=1, le=1000),
):
    """Return raw balance records for an order, item, and warehouse.

    Optional line and stock transaction type fields narrow the request.
    This endpoint is not a complete inventory export.
    """
    client = request.app.state.client
    token = await get_infor_token(client)

    # cono selects the company; the uppercase fields are transaction inputs.
    params = {
        "cono": company,
        "RIDN": order_number,
        "WHLO": warehouse,
        "ITNO": item_code,
        "maxrecs": maxrecs,
    }
    for field, value in (("RIDL", line_number), ("RIDX", line_suffix),
                         ("TTYP", transaction_type)):
        if value is not None:
            params[field] = value

    response = await client.get(
        f"{connector_config.INFOR_BASE_URL.rstrip('/')}/MMS060MI/LstBalIDByOrd",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        params=params,
    )
    response.raise_for_status()
    return response.json()


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


@router.get("/purchase-orders/{puno}/lines")
async def get_purchase_order_lines(puno: str, request: Request):
    client = request.app.state.client
    token = await get_infor_token(client)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    
    }

    url = f"{connector_config.INFOR_BASE_URL}/PPS200MI/LstLine"

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

    url = f"{connector_config.INFOR_BASE_URL}/OIS100MI/LstLine"
    
    response = await client.get( 
        url,
        headers=headers, 
        params={"ORNO": orno}

    )

    response.raise_for_status()
    return response.json()

@router.get("/items/{itno}")
async def get_item_master_data(itno: str, company: str, request: Request):
    """Fetch one item's master data from Infor and return its raw JSON response.

    itno is the item number. company identifies the M3 company to search.
    """
    # Reuse the app's HTTP client and get a token for this request.
    client = request.app.state.client
    token = await get_infor_token(client)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    url = f"{connector_config.INFOR_BASE_URL.rstrip('/')}/MMS200MI/Get"

    # Send the item number and company as Infor's input fields.
    response = await client.get(
        url,
        headers=headers,
        params={"ITNO": itno, "CONO": company},
    )

    # Stop on HTTP errors, otherwise return the response for inspection or mapping.
    response.raise_for_status()
    return response.json()




