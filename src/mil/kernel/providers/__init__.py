"""
Provider interface definitions — architectural extension points.

These abstract interfaces are the only mechanism through which the platform
core interacts with external capabilities (OCR, extraction, inference, storage,
LOS platforms). Concrete implementations live in `src/providers/` and are
registered in the DI container at startup. The platform core has no compile-time
dependency on any specific implementation.

Defined interfaces:
  ocr.py         — OCRProvider: document → structured text + layout
  extraction.py  — ExtractionProvider: text → typed evidence attributes
  inference.py   — InferenceProvider: evidence context → structured response
  storage.py     — StorageProvider: content-addressed document storage
  los_adapter.py — LOSAdapter: LOS platform data translation
"""
