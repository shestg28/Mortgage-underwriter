"""
Document Processing bounded context.

Manages document ingestion, ingestion status lifecycle, and delegation to the
OCRProvider and ExtractionProvider via the Intelligence Orchestrator pipeline.
Source document files are immutable after upload.

Public interface: document.service.DocumentService
"""
