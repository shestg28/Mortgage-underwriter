from typing import Dict, Any


def score_application(customer: Dict[str, Any], fraud_severity: int = 0, match_details: Dict[str, Any] = None) -> Dict[str, Any]:
    """Rule-based scorer returning risk_score (0-100) and breakdown."""
    if match_details is None:
        match_details = {}

    score = 0
    breakdown = {}

    # Salary-based base risk (lower salary = higher risk)
    salary = 0
    try:
        salary = float(customer.get("salary") or 0)
    except Exception:
        salary = 0

    if salary <= 30000:
        score += 40
        breakdown["salary_band"] = "<=30k"
    elif salary <= 60000:
        score += 20
        breakdown["salary_band"] = "30-60k"
    elif salary <= 100000:
        score += 10
        breakdown["salary_band"] = "60-100k"
    else:
        breakdown["salary_band"] = ">100k"

    # Fraud severity contribution
    score += min(fraud_severity * 5, 50)
    breakdown["fraud_severity"] = fraud_severity

    # Verification mismatches
    if match_details.get("aadhaar_match") is False:
        score += 25
        breakdown["aadhaar_mismatch"] = True
    if match_details.get("pan_match") is False:
        score += 20
        breakdown["pan_mismatch"] = True
    if match_details.get("name_match") is False:
        score += 10
        breakdown["name_mismatch"] = True
    sd = match_details.get("salary_diff_pct")
    if sd is not None and sd > 0.2:
        score += 15
        breakdown["salary_diff_pct"] = sd

    risk_score = max(0, min(100, int(score)))
    return {"risk_score": risk_score, "breakdown": breakdown}
