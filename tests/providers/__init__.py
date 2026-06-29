"""
Provider conformance tests.

Each module in this package validates that a concrete provider implementation
satisfies the interface contract defined in mil.kernel.providers.

A provider implementation must pass its conformance test suite before being
registered as a production provider in the DI container.

Conformance test modules added here as implementations are created (Sprint 2+):
  test_ocr_conformance.py        — OCRProvider contract
  test_extraction_conformance.py — ExtractionProvider contract
  test_inference_conformance.py  — InferenceProvider contract
  test_storage_conformance.py    — StorageProvider contract
  test_los_conformance.py        — LOSAdapter contract
"""
