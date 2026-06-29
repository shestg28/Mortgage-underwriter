"""
InferenceProvider interface for the MIL Platform.

Executes prompted inference against a scoped evidence context and returns
structured results carrying model version and prompt version attribution
as required by Engineering Constitution Principle XII (Deterministic Intelligence).

The interface is intentionally domain-agnostic.  Evidence is represented as
structured ``EvidenceEntry`` objects rather than domain ``EvidenceItem`` entities
so that inference providers have no dependency on any bounded context.

This module defines only the abstract interface and its data types.
Concrete implementations live in ``src/providers/inference/`` and are
registered via ``ProviderRegistry.register_inference()``.

Dependency rule: this module imports from the Python standard library only.
No bounded context code should be imported here.
"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod

# ---------------------------------------------------------------------------
# Inference context and result data types
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class EvidenceEntry:
    """
    A single evidence item formatted for use in an inference context.

    Represents the minimum information needed to ground an inference query
    in a specific piece of evidence.  The Copilot service constructs these
    from domain ``EvidenceItem`` objects before passing to ``InferenceProvider``.

    Principle V (Least-data): only the attributes required for the specific
    query should be populated.  Surplus personal data MUST NOT be included.
    """

    evidence_ref: str
    field_name: str
    field_value: str
    confidence: float
    source_ref: str
    page_number: int = 0


@dataclasses.dataclass(frozen=True)
class InferenceContext:
    """
    Scoped context for a single inference call.

    The ``evidence_items`` tuple contains only the evidence items relevant to
    the specific ``query``, scoped strictly to the ``application_id``.  The
    Copilot grounding layer is responsible for enforcing scope before this
    context is constructed.

    Principle V requirement: ``evidence_items`` MUST contain only data
    attributes necessary for the requested query.  Prompts MUST NOT carry
    surplus personal data.

    Attributes:
        application_id:  The MIL application ID (for scope enforcement).
        evidence_items:  Scoped, minimal evidence entries.
        query:           The natural-language query to answer.
        prompt_version:  The version identifier of the prompt template used.
                         Required for Principle XII attribution.
        max_tokens:      Maximum token budget for the response.
    """

    application_id: str
    evidence_items: tuple[EvidenceEntry, ...]
    query: str
    prompt_version: str
    max_tokens: int = 1024

    def __post_init__(self) -> None:
        if not self.application_id:
            raise ValueError("application_id cannot be empty")
        if not self.query:
            raise ValueError("query cannot be empty")
        if not self.prompt_version:
            raise ValueError("prompt_version cannot be empty")
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be >= 1")


@dataclasses.dataclass(frozen=True)
class InferenceResult:
    """
    Structured result from a single inference call.

    Both ``model_version`` and ``prompt_version`` are required to satisfy
    Engineering Constitution Principle XII (Deterministic Intelligence).
    Every AI-generated finding derived from this result MUST record both
    versions in its attribution fields.

    Attributes:
        content:             The natural-language response from the model.
        model_version:       The identifier of the AI model used (e.g. version
                             hash, tag, or release name).  MUST be non-empty.
        prompt_version:      The version of the prompt template applied (echoed
                             from ``InferenceContext.prompt_version``).
        evidence_citations:  Tuple of ``evidence_ref`` values cited in the
                             response.  Each value must match an
                             ``EvidenceEntry.evidence_ref`` from the context.
        inference_latency_ms: Wall-clock time for the inference call in milliseconds.
                             Used for operational monitoring.
    """

    content: str
    model_version: str
    prompt_version: str
    evidence_citations: tuple[str, ...]
    inference_latency_ms: float = 0.0

    def __post_init__(self) -> None:
        if not self.model_version:
            raise ValueError("model_version cannot be empty")
        if not self.prompt_version:
            raise ValueError("prompt_version cannot be empty")
        if self.inference_latency_ms < 0.0:
            raise ValueError("inference_latency_ms cannot be negative")


# ---------------------------------------------------------------------------
# Abstract InferenceProvider interface
# ---------------------------------------------------------------------------


class InferenceProvider(ABC):
    """
    Abstract interface for prompted AI inference.

    Executes a prompt against a scoped evidence context and returns a
    structured result.  The interface is engine-agnostic: concrete
    implementations may call on-premises models, managed cloud endpoints,
    or in-process libraries.

    Security requirement (Principle V): the provider MUST enforce that data
    passed to the model is scoped to the evidence items in the context.
    Evidence from one ``application_id`` MUST NOT appear in inference
    results for a different ``application_id``.

    Version contract: every ``InferenceResult`` MUST include non-empty
    ``model_version`` and ``prompt_version`` strings.  Providers that cannot
    determine their own model version MUST raise ``ProviderVersionMissingError``.
    """

    @abstractmethod
    def infer(self, context: InferenceContext) -> InferenceResult:
        """
        Execute prompted inference against the provided evidence context.

        Args:
            context: A scoped ``InferenceContext`` containing evidence items
                     and the query to answer.

        Returns:
            ``InferenceResult`` with model version, prompt version, and citations.

        Raises:
            ProviderError:               If inference fails.
            ProviderVersionMissingError: If the model version cannot be determined.
        """

    @abstractmethod
    def version(self) -> str:
        """
        Return the model version identifier for this inference provider.

        Used by ``ProviderRegistry`` to validate provider registration and
        to pre-populate ``InferenceResult.model_version`` before a call.
        """
