"""
Concrete provider implementations.

This package contains implementations of the provider interfaces defined in
mil.kernel.providers. Each sub-package targets one provider category. Multiple
implementations per category are permitted (e.g., different OCR backends for
different deployment environments).

Implementations are registered in the DI container at startup via
mil.kernel.container. The platform core has no compile-time dependency on
any module in this package.

Every implementation must pass the corresponding conformance test suite in
tests/providers/ before being registered as a production provider.

Provider categories:
  ocr/        — OCRProvider implementations
  extraction/ — ExtractionProvider implementations
  inference/  — InferenceProvider implementations
  storage/    — StorageProvider implementations
  los/        — LOSAdapter implementations (one per LOS platform)
"""
