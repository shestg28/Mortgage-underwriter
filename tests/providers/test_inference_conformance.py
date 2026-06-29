"""
InferenceProvider conformance tests.

Verifies that any concrete ``InferenceProvider`` satisfies the interface
contract defined in ``mil.kernel.providers.inference``, including mandatory
presence of model version and prompt version in every result.

Engineering Constitution Principle XII (Deterministic Intelligence): every
AI-generated finding must be attributable to a specific model version and
prompt version.  The inference provider is the source of both.
"""

from __future__ import annotations

import pytest

from mil.kernel.providers.inference import (
    EvidenceEntry,
    InferenceContext,
    InferenceProvider,
    InferenceResult,
)

# ---------------------------------------------------------------------------
# Shared context builder
# ---------------------------------------------------------------------------


def make_context(
    query: str = "Summarise the income evidence for this application.",
    prompt_version: str = "income-v1.0.0",
    evidence_items: tuple[EvidenceEntry, ...] | None = None,
) -> InferenceContext:
    if evidence_items is None:
        evidence_items = (
            EvidenceEntry(
                evidence_ref="ev-001",
                field_name="gross_monthly_income",
                field_value="5000.00",
                confidence=0.85,
                source_ref="doc-ref-001",
                page_number=1,
            ),
            EvidenceEntry(
                evidence_ref="ev-002",
                field_name="employer_name",
                field_value="Acme Corporation",
                confidence=0.90,
                source_ref="doc-ref-001",
                page_number=1,
            ),
        )
    return InferenceContext(
        application_id="app-001",
        evidence_items=evidence_items,
        query=query,
        prompt_version=prompt_version,
    )


class TestInferenceProviderInterfaceContract:
    """Verify the abstract interface structure."""

    def test_inference_provider_is_abstract(self) -> None:
        assert InferenceProvider.__abstractmethods__ != set()

    def test_infer_is_abstract(self) -> None:
        assert "infer" in InferenceProvider.__abstractmethods__

    def test_version_is_abstract(self) -> None:
        assert "version" in InferenceProvider.__abstractmethods__

    def test_concrete_provider_is_subclass(self, inference_provider: InferenceProvider) -> None:
        assert isinstance(inference_provider, InferenceProvider)


class TestInferenceProviderVersion:
    """Version contract: providers MUST return a non-empty model version string."""

    def test_version_returns_string(self, inference_provider: InferenceProvider) -> None:
        assert isinstance(inference_provider.version(), str)

    def test_version_is_non_empty(self, inference_provider: InferenceProvider) -> None:
        assert inference_provider.version() != ""


class TestInferResultStructure:
    """InferenceResult must carry required attribution fields."""

    @pytest.fixture
    def result(self, inference_provider: InferenceProvider) -> InferenceResult:
        return inference_provider.infer(make_context())

    def test_returns_inference_result(self, result: InferenceResult) -> None:
        assert isinstance(result, InferenceResult)

    def test_content_is_string(self, result: InferenceResult) -> None:
        assert isinstance(result.content, str)

    def test_content_is_non_empty(self, result: InferenceResult) -> None:
        assert result.content != ""

    # Principle XII: model version required
    def test_model_version_is_non_empty(self, result: InferenceResult) -> None:
        assert isinstance(result.model_version, str)
        assert result.model_version != ""

    # Principle XII: prompt version required
    def test_prompt_version_is_non_empty(self, result: InferenceResult) -> None:
        assert isinstance(result.prompt_version, str)
        assert result.prompt_version != ""

    def test_prompt_version_echoed_from_context(
        self, inference_provider: InferenceProvider
    ) -> None:
        context = make_context(prompt_version="income-v2.5.0")
        result = inference_provider.infer(context)
        assert result.prompt_version == "income-v2.5.0"

    def test_model_version_matches_provider_version(
        self, inference_provider: InferenceProvider, result: InferenceResult
    ) -> None:
        assert result.model_version == inference_provider.version()

    def test_evidence_citations_is_tuple(self, result: InferenceResult) -> None:
        assert isinstance(result.evidence_citations, tuple)

    def test_latency_is_non_negative(self, result: InferenceResult) -> None:
        assert result.inference_latency_ms >= 0.0


class TestInferenceContextScoping:
    """Evidence citations in the result must reference only items in the context."""

    def test_citations_are_subset_of_context_refs(
        self, inference_provider: InferenceProvider
    ) -> None:
        context = make_context()
        context_refs = {e.evidence_ref for e in context.evidence_items}
        result = inference_provider.infer(context)

        for citation in result.evidence_citations:
            assert citation in context_refs, (
                f"Citation {citation!r} not in context evidence refs {context_refs!r}. "
                "Provider MUST NOT cite evidence outside the provided context."
            )

    def test_empty_evidence_context_does_not_raise(
        self, inference_provider: InferenceProvider
    ) -> None:
        context = make_context(evidence_items=())
        result = inference_provider.infer(context)
        assert isinstance(result, InferenceResult)
        assert result.evidence_citations == ()


class TestInferenceContextValidation:
    """InferenceContext rejects invalid inputs at construction time."""

    def test_empty_application_id_raises(self) -> None:
        with pytest.raises(ValueError, match="application_id"):
            InferenceContext(
                application_id="",
                evidence_items=(),
                query="test",
                prompt_version="v1",
            )

    def test_empty_query_raises(self) -> None:
        with pytest.raises(ValueError, match="query"):
            InferenceContext(
                application_id="app-001",
                evidence_items=(),
                query="",
                prompt_version="v1",
            )

    def test_empty_prompt_version_raises(self) -> None:
        with pytest.raises(ValueError, match="prompt_version"):
            InferenceContext(
                application_id="app-001",
                evidence_items=(),
                query="test",
                prompt_version="",
            )

    def test_zero_max_tokens_raises(self) -> None:
        with pytest.raises(ValueError, match="max_tokens"):
            InferenceContext(
                application_id="app-001",
                evidence_items=(),
                query="test",
                prompt_version="v1",
                max_tokens=0,
            )


class TestInferenceResultValidation:
    """InferenceResult rejects invalid inputs at construction time."""

    def test_empty_model_version_raises(self) -> None:
        with pytest.raises(ValueError, match="model_version"):
            InferenceResult(
                content="response",
                model_version="",
                prompt_version="v1",
                evidence_citations=(),
            )

    def test_empty_prompt_version_raises(self) -> None:
        with pytest.raises(ValueError, match="prompt_version"):
            InferenceResult(
                content="response",
                model_version="model-1.0",
                prompt_version="",
                evidence_citations=(),
            )

    def test_negative_latency_raises(self) -> None:
        with pytest.raises(ValueError, match="inference_latency_ms"):
            InferenceResult(
                content="response",
                model_version="model-1.0",
                prompt_version="v1",
                evidence_citations=(),
                inference_latency_ms=-1.0,
            )
