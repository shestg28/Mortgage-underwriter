from typing import Dict, List, Any
from uuid import uuid4


def detect_fraud_rules(match_details: Dict, extracted: Dict[str, Any] | None = None) -> List[Dict]:
    """Apply fraud rules based on comparison details and extracted document fields."""
    flags = []

    if extracted is not None:
        required_fields = ["name", "pan", "aadhaar", "salary", "address"]
        for field in required_fields:
            if not extracted.get(field):
                flags.append({
                    "id": str(uuid4()),
                    "flag_type": f"{field}_missing",
                    "severity": 7,
                    "details": {"missing_field": field, "extracted": extracted},
                })

    # Aadhaar mismatch -> high severity
    if match_details.get("aadhaar_match") is False:
        flags.append({"id": str(uuid4()), "flag_type": "aadhaar_mismatch", "severity": 8, "details": match_details})

    # PAN mismatch -> high severity
    if match_details.get("pan_match") is False:
        flags.append({"id": str(uuid4()), "flag_type": "pan_mismatch", "severity": 7, "details": match_details})

    # Salary deviation -> medium
    sd = match_details.get("salary_diff_pct")
    if sd is not None and sd > 0.2:
        flags.append({"id": str(uuid4()), "flag_type": "salary_mismatch", "severity": 5, "details": match_details})

    # Name mismatch -> low
    if match_details.get("name_match") is False:
        flags.append({"id": str(uuid4()), "flag_type": "name_mismatch", "severity": 3, "details": match_details})

    return flags
