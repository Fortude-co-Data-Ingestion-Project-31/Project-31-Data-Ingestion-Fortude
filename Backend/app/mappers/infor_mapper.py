"""Normalize M3 MI records while retaining all source fields."""
from fastapi import HTTPException


def map_infor_response_to_canonical(payload, order_type, order_number):
    if not isinstance(payload, dict):
        raise HTTPException(502, "Infor returned an invalid order response.")
    if payload.get("errorMessage") or payload.get("nrOfFailedTransactions") not in (None, 0, "0"):
        raise HTTPException(502, "Infor could not retrieve the requested order lines.")
    results = payload.get("results", [payload])
    if not isinstance(results, list):
        raise HTTPException(502, "Infor returned invalid transaction results.")
    records = []
    for result in results:
        if not isinstance(result, dict) or result.get("errorMessage"):
            raise HTTPException(502, "Infor could not retrieve the requested order lines.")
        batch = result.get("records")
        if not isinstance(batch, list) or any(not isinstance(row, dict) for row in batch):
            raise HTTPException(502, "Infor returned invalid order-line records.")
        records.extend(batch)
    documents = []
    for index, record in enumerate(records, start=1):
        line = record.get("PNLI" if order_type == "purchase" else "PONR", str(index))
        suffix = record.get("PNLS" if order_type == "purchase" else "POSX", "0")
        documents.append({
            "source": "infor_m3",
            "document_id": f"infor:{order_type}:{order_number}:{line}:{suffix}",
            "title": f"{order_type.title()} order {order_number}, line {line}",
            "order_type": order_type,
            "order_number": order_number,
            "line_number": line,
            "line_suffix": suffix,
            "tags": [],
            "content": record,
        })
    return documents
