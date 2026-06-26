from typing import Dict, Any, Tuple


def compare_extracted_with_db(extracted: Dict[str, Any], db_record: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Compare extracted values with a DB record. Returns (match, details)."""
    details = {}
    match = True

    # PAN
    if extracted.get("pan") and db_record.get("pan"):
        pan_match = extracted.get("pan").upper() == db_record.get("pan").upper()
        details["pan_match"] = pan_match
        if not pan_match:
            match = False

    # Aadhaar
    if extracted.get("aadhaar") and db_record.get("aadhaar"):
        aad_match = extracted.get("aadhaar") == db_record.get("aadhaar")
        details["aadhaar_match"] = aad_match
        if not aad_match:
            match = False

    # Salary (allow 20% tolerance)
    if extracted.get("salary") and db_record.get("salary") is not None:
        try:
            db_sal = float(db_record.get("salary"))
            ext_sal = float(extracted.get("salary"))
            diff = abs(db_sal - ext_sal)
            details["salary_db"] = db_sal
            details["salary_extracted"] = ext_sal
            details["salary_diff_pct"] = diff / max(db_sal, 1)
            if details["salary_diff_pct"] > 0.2:
                match = False
        except Exception:
            details["salary_error"] = "parse_error"

    # Name
    if extracted.get("name") and db_record.get("full_name"):
        name_match = extracted.get("name").strip().lower() in db_record.get("full_name").strip().lower() or db_record.get("full_name").strip().lower() in extracted.get("name").strip().lower()
        details["name_match"] = name_match
        if not name_match:
            match = False

    if not any(extracted.get(field) for field in ["name", "pan", "aadhaar", "salary", "address"]):
        details["no_extracted_data"] = True
        match = False

    return match, details
