import pytesseract
from PIL import Image
from io import BytesIO


def ocr_image_bytes(image_bytes: bytes, lang: str = "eng") -> str:
    buf = BytesIO(image_bytes)
    img = Image.open(buf).convert("RGB")
    text = pytesseract.image_to_string(img, lang=lang)
    return text
