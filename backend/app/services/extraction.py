import re
from typing import Dict, Optional


PAN_RE = re.compile(r"\b([A-Za-z]{5}[0-9]{4}[A-Za-z])\b")
AADHAAR_RE = re.compile(r"\b(\d{4}\s*\d{4}\s*\d{4})\b")
SALARY_RE = re.compile(r"(?:salary|income|annual|gross)[^0-9\n\r]{0,15}([\d,]+(?:\.\d{1,2})?)", re.I)
NAME_RE = re.compile(r"\bname[:\-]?\s*(.+)", re.I)
ADDRESS_RE = re.compile(r"\baddress[:\-]?\s*(.+)", re.I)


def is_valid_pan(candidate: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", candidate.upper()))


def is_signature_line(text: str) -> bool:
    return bool(re.search(r"\b(sign|signature|signed|auth|authorised|initial)\b", text, re.I))


def find_pan(text: str) -> Optional[str]:
    """Find PAN: exactly 5 letters + 4 digits + 1 letter, normalized to uppercase."""
    if not text:
        return None

    text_upper = text.upper()
    for match in PAN_RE.finditer(text_upper):
        candidate = match.group(1)
        if is_valid_pan(candidate):
            return candidate

    for token in re.findall(r"[A-Z0-9]+", text_upper):
        if len(token) >= 10:
            for i in range(len(token) - 9):
                candidate = token[i : i + 10]
                if is_valid_pan(candidate):
                    return candidate

    compact = re.sub(r"[^A-Z0-9]+", "", text_upper)
    for i in range(len(compact) - 9):
        candidate = compact[i : i + 10]
        if is_valid_pan(candidate):
            return candidate

    return None


def find_aadhaar(text: str) -> Optional[str]:
    match = AADHAAR_RE.search(text)
    if match:
        return match.group(1).replace(" ", "")
    fallback = re.search(r"\b(\d{12})\b", text)
    if fallback:
        return fallback.group(1)
    return None


def find_salary(text: str) -> Optional[float]:
    # First try explicit salary labels
    match = SALARY_RE.search(text)
    if match:
        salary_raw = match.group(1).replace(",", "")
        try:
            val = float(salary_raw)
            if val > 10000:  # realistic salary threshold
                return val
        except Exception:
            return None
    # if the line looks like a signature, do not treat the numbers as salary
    if is_signature_line(text):
        return None
    # fallback: find 5+ digit numbers, but only if > 10000 and not part of a PAN-like token
    fallback = re.search(r"\b([0-9]{5,}(?:\.[0-9]{1,2})?)\b", text)
    if fallback:
        try:
            val = float(fallback.group(1).replace(",", ""))
            if val > 10000:
                return val
        except Exception:
            return None
    return None


def extract_fields_from_text(text: str) -> Dict[str, Optional[str]]:
    fields = {
        "name": None,
        "pan": None,
        "aadhaar": None,
        "salary": None,
        "address": None,
    }

    if not text:
        return fields

    fields["pan"] = find_pan(text)
    fields["aadhaar"] = find_aadhaar(text)
    fields["salary"] = find_salary(text)

    name_m = NAME_RE.search(text)
    if name_m:
        fields["name"] = name_m.group(1).strip()

    addr_m = ADDRESS_RE.search(text)
    if addr_m:
        fields["address"] = addr_m.group(1).strip()

    for line in text.splitlines():
        normalized = line.strip()
        if not normalized:
            continue
        lower = normalized.lower()

        if not fields["name"] and "name" in lower:
            parts = re.split(r"[:\-]", normalized, maxsplit=1)
            if len(parts) > 1 and parts[1].strip():
                fields["name"] = parts[1].strip()
                continue

        if not fields["pan"] and "pan" in lower:
            pan_value = find_pan(normalized)
            if pan_value:
                fields["pan"] = pan_value
                continue

        if not fields["aadhaar"] and ("aadhaar" in lower or "aadhar" in lower):
            aad_value = find_aadhaar(normalized)
            if aad_value:
                fields["aadhaar"] = aad_value
                continue

        if not fields["salary"] and any(token in lower for token in ("salary", "income", "annual", "gross")):
            salary_value = find_salary(normalized)
            if salary_value is not None:
                fields["salary"] = salary_value
                continue

        if not fields["address"] and "address" in lower:
            parts = re.split(r"[:\-]", normalized, maxsplit=1)
            if len(parts) > 1 and parts[1].strip():
                fields["address"] = parts[1].strip()
                continue

    if not fields["name"]:
        for line in text.splitlines():
            candidate = line.strip()
            if candidate and len(candidate) > 3 and not any(label in candidate.lower() for label in ["pan", "aadhaar", "salary", "address"]):
                fields["name"] = candidate
                break

    return fields
