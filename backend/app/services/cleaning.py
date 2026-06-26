import re
from typing import Dict


def clean_text(raw_text: str) -> str:
    """Normalize OCR-generated text for extraction."""
    text = raw_text.replace("\r", "\n")
    text = re.sub(r"[\t\u00A0]+", " ", text)
    text = re.sub(r"[-]{2,}", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = text.strip()
    return text


def normalize_fields(extracted: Dict[str, str]) -> Dict[str, str]:
    normalized = {}
    for key, value in extracted.items():
        if value is None:
            normalized[key] = None
            continue
        if isinstance(value, str):
            normalized[key] = value.strip()
        else:
            normalized[key] = value
    return normalized
