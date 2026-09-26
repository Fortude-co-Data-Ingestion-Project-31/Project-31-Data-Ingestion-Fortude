"""
The Connector already receives the raw purchase-order and customer-order lines. 
The Mapper should receive that response and convert it into a consisten structure.

The mapper’s responsibilities are to:
- Extract the order records from the API response.
- Rename source fields into clear, consistent names.
- Convert quantities and dates into agreed formats.
- Preserve identifiers as strings, including leading zeros.
- Keep missing values visible and retain the original record.
- Build stable IDs using enough context to distinguish clients, companies, orders, and lines.
"""

# Check Infor Errors and extracts records from results
def extract_infor_records(payload:dict):
    # Infor API connector passes the response to this function 'payload'

    if type(payload) is dict:

        results = payload.get("results")
        if type(results) is list:
            # Check for errors from Infor response and return a list of raw order line records
            if payload["nrOfFailedTransactions"] > 0:
                raise ValueError ("Record does not exist")

        else:
            raise ValueError ("Infor Results must be a list")    

    else:
        raise ValueError ("Infor Response must be a dictionary")

    records = []

    # Looping through the infor results and collecting each one
    for result in results:
        if not isinstance(result, dict):
            raise ValueError("Each transaction result must be a dictionary.")

        # Use the actual error message returned by Infor.
        if result.get("errorMessage"):
            raise ValueError(result["errorMessage"])

        batch = result.get("records")
        if not isinstance(batch, list):
            raise ValueError("Transaction records must be a list.")

        for record in batch:
            if not isinstance(record, dict):
                raise ValueError("Each record must be a dictionary.")

        records.extend(batch)


    return records

# transforms purchase order line into a standard format.
def map_purchase_order_line(record, tenant, company, order_number):

     line_number = record.get("PNLI")
     line_suffix = record.get("PNLS")

     # All parts are needed to reliably identify this order line.
     id_parts = [
        "infor_m3",
        tenant,
        company,
        "purchase",
        order_number,
        line_number,
        line_suffix,
     ]

     if any(part is None or str(part).strip() == "" for part in id_parts):
          raise ValueError("Cannot create document ID: missing order identifiers.")

     document_id = ":".join(str(part).strip() for part in id_parts)
     # Copy values into clearly named fields without changing the raw record.
     quantities = {}

     for field in ("ORQA", "RVQA", "IVQA"):
        value = record.get(field)

        if value is None or (isinstance(value, str) and not value.strip()):
            quantities[field] = None
        else:
            try:
                quantities[field] = float(value)
            except (TypeError, ValueError):
                raise ValueError(f"Invalid quantity for {field}: {value!r}")
            
     mapped_record = {
     "source": "infor_m3",
     "tenant": tenant,
     "company": company,
     "order_type": "purchase",
     "order_number": order_number,
     "line_number": record.get("PNLI"),
     "line_suffix": record.get("PNLS"),
     "item_code": record.get("ITNO"),
     "ordered_quantity": quantities["ORQA"],
     "received_quantity": quantities["RVQA"],
     "invoiced_quantity": quantities["IVQA"],
     "content": record.copy(),
     "document_id" : document_id # adding document id, for later recognition if needed
}

     return mapped_record

# transfomrs customer order line into standard format.
def map_customer_order_line(record, tenant, company, order_number):
         line_number = record.get("PONR")
         line_suffix = record.get("POSX")
    
         # All parts are needed to reliably identify this order line.
         id_parts = [
            "infor_m3",
            tenant,
            company,
            "customer",
            order_number,
            line_number,
            line_suffix,
         ]
    
         if any(part is None or str(part).strip() == "" for part in id_parts):
              raise ValueError("Cannot create document ID: missing order identifiers.")
    
         document_id = ":".join(str(part).strip() for part in id_parts)
         # Copy values into clearly named fields without changing the raw record.
         quantities = {}
    
         for field in ("ORQT", "DLQT", "IVQT"):
            value = record.get(field)
    
            if value is None or (isinstance(value, str) and not value.strip()):
                quantities[field] = None
            else:
                try:
                    quantities[field] = float(value)
                except (TypeError, ValueError):
                    raise ValueError(f"Invalid quantity for {field}: {value!r}")
                
         mapped_record = {
        "source": "infor_m3",
        "tenant": tenant,
        "company": company,
        "order_type": "customer",
        "order_number": order_number,
        "line_number": line_number,
        "line_suffix": line_suffix,
        "item_code": record.get("ITNO"),
        "ordered_quantity": quantities["ORQT"],
        "delivered_quantity": quantities["DLQT"],
        "invoiced_quantity": quantities["IVQT"],
        "content": record.copy(),
        "document_id": document_id,
    }

    
         return mapped_record

# extracts records and call the correct mapper for each line.
def map_infor_response(payload, order_type, tenant, company, order_number):
    pass
