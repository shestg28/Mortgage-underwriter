from io import BytesIO
from typing import Union, List
from pdf2image import convert_from_bytes, convert_from_path
from app.services.ocr_service import ocr_image_bytes


def convert_pdf_to_images(source: Union[str, bytes]) -> List[bytes]:
    """Convert PDF pages into PNG image bytes using pdf2image."""
    try:
        if isinstance(source, str):
            pages = convert_from_path(source, dpi=300, fmt="png")
        else:
            pages = convert_from_bytes(bytes(source), dpi=300, fmt="png")
    except Exception as exc:
        raise RuntimeError(f"PDF conversion to images failed: {exc}")

    images = []
    for page in pages:
        buf = BytesIO()
        page.save(buf, format="PNG")
        buf.seek(0)
        images.append(buf.getvalue())
    return images


def extract_text_from_pdf(data: Union[str, bytes]) -> List[str]:
    """Generate PNGs from a PDF and OCR each page separately."""
    images = convert_pdf_to_images(data)
    return [ocr_image_bytes(img) for img in images]
