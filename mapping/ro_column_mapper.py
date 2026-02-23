def map_to_ro_table(extracted):
    return {
        "RO_NUMBER": extracted.get("RO_NUMBER", {}).get("value"),
        "RO_DATE": extracted.get("RO_DATE", {}).get("value"),
        "CLIENT_NAME": extracted.get("CLIENT_NAME", {}).get("value"),
        "AGENCY_NAME": extracted.get("AGENCY_NAME", {}).get("value"),
        "RO_AMOUNT": extracted.get("RO_AMOUNT", {}).get("value"),
        "RO_REMARKS": extracted.get("RO_REMARKS", {}).get("value")
    }
