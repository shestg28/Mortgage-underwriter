---
description: "Task list for MIL — Mortgage Intelligence Layer foundational platform"
---

# Tasks: Mortgage Intelligence Layer (MIL) — Foundational Platform

**Input**: Design documents from `specs/001-mil-platform-spec/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | data-model.md ✅ | research.md ✅ | contracts/ ✅ | quickstart.md ✅

**Organization**: Tasks are grouped by platform capability phase to enable independent implementation
and validation of each layer. Each phase is independently deployable and testable before the next begins.

---

## User Story Mapping

| Label | Platform Capability | Plan Phase | Independent Test |
|---|---|---|---|
| **US1** | Platform Foundation (Identity, Audit, Application, Party, Document Storage) | Phase 1 | Application created; Parties added; document uploaded; Audit Events recorded with consecutive sequence numbers |
| **US2** | Document Intelligence and Evidence Core (Orchestrator, OCR, Extraction, Evidence, Policy, Finding generation) | Phase 2 | Document ingested; Evidence items created with all seven provenance attributes; Finding generated with all five explainability fields and all four attribution fields; Evidence Snapshot captured |
| **US3** | Human Review, Verification, and Explainability | Phase 3 | Finding verified, overridden, and escalated; override record captures all required fields; terminal state rejects further transitions; Readiness assessment reflects current state |
| **US4** | Evidence Copilot and Operational Intelligence | Phase 4 | Copilot returns evidence-grounded response with citations scoped to the queried application; Operational dashboard reflects current queue state |
| **US5** | Enterprise Integration Framework | Phase 5 | LOS adapter translates inbound application data; multi-tenant data isolation enforced; integration events dispatched correctly |

---

## Format: `[ID] [P?] [Story?] Description with exact file path`

- **[P]**: Parallelizable — different files, no dependency on incomplete tasks in the same phase
- **[Story]**: User story label [US1]–[US5]; omitted for Setup, Foundational, and Polish phases

---

## Phase 1: Setup

**Purpose**: Repository scaffold, tooling, and development environment. No business logic.

- [ ] T001 Create Python package structure per plan.md: `src/mil/` with all bounded context sub-packages and `__init__.py` files
- [ ] T002 [P] Create `pyproject.toml` with core dependencies: FastAPI, SQLAlchemy, Pydantic, OpenTelemetry, Alembic, pytest, httpx, testcontainers
- [ ] T003 [P] Create `docker-compose.yml` for local development: PostgreSQL, object storage (MinIO), and message broker services
- [ ] T004 [P] Initialise Alembic in `migrations/` with `env.py` wired to SQLAlchemy base
- [ ] T005 [P] Create `Makefile` with targets: `install`, `lint`, `test-unit`, `test-integration`, `migrate`, `run-api`, `run-worker`
- [ ] T006 [P] Create `tests/` directory structure: `contract/`, `integration/`, `unit/`, `providers/` with `conftest.py` stubs

---

## Phase 2: Foundational — Platform Kernel

**Purpose**: The shared foundation that all bounded contexts depend on. No user story work can begin until this phase is complete.

**⚠️ CRITICAL**: Every subsequent task depends on the Platform Kernel being complete.

- [ ] T007 Implement `src/mil/kernel/types.py` — strongly-typed identifiers (`ApplicationId`, `EvidenceItemId`, `FindingId`, `TenantId`) and value objects (`Money`, `Confidence`, `PolicyVersion`)
- [ ] T008 [P] Implement `src/mil/kernel/errors.py` — `DomainError` base class hierarchy; canonical error codes; API error response schema aligned to `contracts/` error shape
- [ ] T009 [P] Implement `src/mil/kernel/config.py` — typed `Settings` schema with Pydantic; environment-variable resolution; deployment-profile support
- [ ] T010 Implement `src/mil/kernel/events.py` — canonical domain event type definitions: `DocumentIngested`, `EvidenceExtracted`, `FindingGenerated`, `FindingStateChanged`, `OverrideRecorded`, `WorkflowStepFailed`
- [ ] T011 Implement `src/mil/kernel/event_bus.py` — `EventBus` abstract interface; in-process synchronous implementation for development; broker-backed implementation registered via DI
- [ ] T012 Implement `src/mil/kernel/job_queue.py` — `JobQueue` abstract interface; `Job` base type with idempotency key; in-process implementation for development; broker-backed implementation registered via DI
- [ ] T013 [P] Implement `src/mil/kernel/security.py` — `AuthenticatedUser` context type; permission constants matching roles in `spec.md` (VERIFICATION_OFFICER, UNDERWRITER, AUDIT_TEAM, etc.); enforcement hook signatures for RBAC and ABAC
- [ ] T014 [P] Implement `src/mil/kernel/observability.py` — structured log factory (JSON output with mandatory fields: timestamp, severity, service, request_id, application_id, user_id, event_type); trace context propagation helpers; metric emitter interface
- [ ] T015 [P] Implement `src/mil/kernel/providers/ocr.py` — `OCRProvider` abstract interface: `process_document(document_ref) -> OCRResult` where result includes page-level text, layout, and provider version
- [ ] T016 [P] Implement `src/mil/kernel/providers/extraction.py` — `ExtractionProvider` abstract interface: `extract_evidence(ocr_result, document_id) -> list[EvidenceAttributes]`; contract requires all seven provenance attributes and provider version in return type
- [ ] T017 [P] Implement `src/mil/kernel/providers/inference.py` — `InferenceProvider` abstract interface: `infer(context: InferenceContext) -> InferenceResult`; contract requires model version and prompt version in return type
- [ ] T018 [P] Implement `src/mil/kernel/providers/storage.py` — `StorageProvider` abstract interface: `store(content, content_hash) -> StorageReference`; `retrieve(reference) -> bytes`; `verify_integrity(reference, expected_hash) -> bool`
- [ ] T019 [P] Implement `src/mil/kernel/providers/los_adapter.py` — `LOSAdapter` abstract interface: `read_application(los_reference) -> ApplicationData`; `read_documents(los_reference) -> list[DocumentReference]`; `notify_readiness(los_reference, readiness_status) -> None`
- [ ] T020 Implement `src/mil/kernel/container.py` — dependency injection container; provider binding declarations; bounded context service registrations
- [ ] T021 Implement `src/mil/api/middleware/auth.py` — Zero Trust authentication middleware; validates identity token on every inbound request; populates `AuthenticatedUser` context; rejects unauthenticated requests before any business logic runs
- [ ] T022 [P] Implement `src/mil/api/middleware/audit_context.py` — propagates `request_id`, `user_id`, and `application_id` through request context for audit event enrichment
- [ ] T023 [P] Implement `src/mil/api/middleware/telemetry.py` — OpenTelemetry request tracing; wires structured log factory to request context
- [ ] T024 Create Alembic migration for `audit` schema: `audit.audit_events` table with `sequence_number BIGSERIAL`, all columns per `data-model.md`; application DB user granted INSERT only (no UPDATE, no DELETE)
- [ ] T025 [P] Implement `src/mil/audit/models.py` — `AuditEvent` ORM model; `AuditEventType` enumeration matching all types in `data-model.md`
- [ ] T026 Implement `src/mil/audit/writer.py` — append-only audit event writer; `emit(event_type, entity_type, entity_id, event_data, actor, application_id)` — single public method; raises `AuditWriteError` on failure (never silently discards)
- [ ] T027 [P] Implement `src/mil/audit/repository.py` — read-only audit queries: by application, by entity, by sequence range, lifecycle reconstruction; verify sequence number continuity
- [ ] T028 Write unit tests for Platform Kernel: `tests/unit/kernel/test_types.py`, `test_errors.py`, `test_event_bus.py`, `test_job_queue.py` — verify in-process implementations satisfy interface contracts

**Checkpoint**: Platform Kernel complete. All bounded context work can now begin.

---

## Phase 3: User Story 1 — Platform Foundation 🎯 MVP

**Goal**: A secure, observable platform that can manage Applications, Parties, and uploaded Documents with a complete Audit trail. No AI capabilities yet.

**Independent Test**: Create an application; add two parties; upload a document associated with a party; verify four Audit Events recorded with consecutive sequence numbers; verify document metadata retrievable. See `quickstart.md` Scenario 1.

### Implementation for User Story 1

- [ ] T029 [P] [US1] Implement `src/mil/identity/models.py` — `User`, `Role`, `RoleAssignment` ORM models; `PartyType` enumeration
- [ ] T030 [P] [US1] Implement `src/mil/identity/rbac.py` — RBAC enforcement; permission-to-role mapping; `require_permission(user, permission)` decorator
- [ ] T031 [P] [US1] Implement `src/mil/identity/abac.py` — ABAC policies; cross-application access denial; application-scoped data access enforcement
- [ ] T032 [P] [US1] Implement `src/mil/identity/provider.py` — external IdP integration; token validation and `AuthenticatedUser` population
- [ ] T033 [US1] Create Alembic migration for `core` schema: `core.users`, `core.roles`, `core.role_assignments`, `core.applications`, `core.parties`, `core.policy_packs` tables per `data-model.md`
- [ ] T034 [P] [US1] Implement `src/mil/application/models.py` — `Application`, `Party` ORM models; application lifecycle status enumeration
- [ ] T035 [P] [US1] Implement `src/mil/application/repository.py` — CRUD for Application and Party; emits `APPLICATION_CREATED` and `PARTY_ADDED` audit events via `audit.writer`
- [ ] T036 [US1] Implement `src/mil/application/service.py` — create application; add party; validate party type; associate document with party; emit audit events
- [ ] T037 [P] [US1] Implement `src/providers/storage/` — concrete `StorageProvider` implementation: object storage (content-addressed, SHA-256 integrity verification, immutable after write)
- [ ] T038 [P] [US1] Implement `src/mil/document/models.py` — `Document` ORM model; `IngestionStatus` enumeration (PENDING, IN_PROGRESS, COMPLETED, FAILED)
- [ ] T039 [P] [US1] Implement `src/mil/document/repository.py` — document creation; status update; party association; emits `DOCUMENT_UPLOADED` audit event
- [ ] T040 [US1] Implement `src/mil/document/service.py` upload path — receive file, compute SHA-256, delegate to `StorageProvider`, persist `Document` record with PENDING status, emit `DocumentIngested` event on `EventBus`
- [ ] T041 [US1] Implement `src/mil/api/v1/applications.py` — REST endpoints: `POST /v1/applications`, `GET /v1/applications`, `GET /v1/applications/{id}`, `POST /v1/applications/{id}/parties`, `GET /v1/applications/{id}/parties`; validate against `contracts/applications.yaml`
- [ ] T042 [US1] Implement `src/mil/api/v1/documents.py` — REST endpoints: `POST /v1/applications/{id}/documents`, `GET /v1/applications/{id}/documents`, `GET /v1/applications/{id}/documents/{doc_id}`; validate against `contracts/documents.yaml`
- [ ] T043 [US1] Implement `src/mil/api/v1/audit.py` — REST endpoints: `GET /v1/audit/applications/{id}`, `GET /v1/audit/applications/{id}/lifecycle`, `GET /v1/audit/events/{id}`; validate against `contracts/audit.yaml`
- [ ] T044 [US1] Create `Dockerfile` for `mil-api` container; verify Zero Trust middleware executes before all routes
- [ ] T045 [US1] Integration test in `tests/integration/test_audit_immutability.py`: attempt UPDATE and DELETE on `audit.audit_events`; verify both fail at database permission level; verify sequence numbers are consecutive

**Checkpoint**: Platform Foundation complete. Application, Party, Document upload, and Audit trail all independently functional and testable.

---

## Phase 3.5: Architecture Readiness (Pre-US2)

**Purpose**: Prepare the platform's event, transaction, and coordination architecture for the Intelligence Pipeline. This phase eliminates the architectural risks identified in the US2 Architecture Readiness Review **without changing current runtime behaviour**. It introduces no OCR, Evidence, Finding, or Orchestrator business logic.

**⚠️ CRITICAL**: This phase **BLOCKS US2**. No Phase 4 task may begin until this phase is complete and all existing tests still pass. It is governed by ADR-007, ADR-008, and ADR-009.

**Scope discipline**: tasks below state architectural objectives only. Implementation detail (file layout, schema columns, code) is deliberately deferred to the implementing engineer, consistent with the readiness nature of this phase.

- [ ] TR01 Transactional Outbox: introduce a committed-event outbox so cross-context `DomainEvent`s are recorded in the same database transaction as the state change that produces them, per ADR-007. Audit remains synchronous and in-transaction — audit does **not** move through the outbox.
- [ ] TR02 Relay process: add a relay that publishes committed outbox events to the `EventBus` and records publication, establishing commit-before-publish and at-least-once delivery, per ADR-007.
- [ ] TR03 [P] Migrate `DocumentIngested` publication from the direct service-layer `event_bus.publish()` call to an outbox write inside the ingestion transaction, per ADR-007. No change to observable upload behaviour.
- [ ] TR04 Idempotency foundation: define deterministic idempotency keys and a per-job Unit of Work for pipeline work, backed by database unique constraints, so that at-least-once delivery yields exactly-once effects, per ADR-008.
- [ ] TR05 [P] Retry policy foundation: express retryable-vs-terminal classification on the provider/error contract, with bounded retries, backoff, and dead-letter routing, per ADR-008.
- [ ] TR06 Workflow version pinning: establish the `WorkflowRun` contract that pins the policy, model, prompt, and extraction versions at run creation, so pipeline output is reproducible and attributable, per ADR-009.
- [ ] TR07 [P] Correlation ID propagation: populate and propagate `DomainEvent.correlation_id` (set to the workflow run identity) through outbox events, jobs, and audit events, enabling single-trace pipeline reconstruction, per ADR-009.
- [ ] TR08 [P] Workflow lifecycle events: add the typed domain events promised by the plan but absent from the kernel — workflow started, workflow step completed, workflow completed — alongside the existing `WorkflowStepFailed`, per ADR-009.
- [ ] TR09 Finding generation trigger alignment: record that finding generation is triggered by the `MortgageApplication` DRAFT → SUBMITTED transition and evaluates all application evidence at that point — not per document — per ADR-009. (Architectural alignment only; orchestrator implementation is US2.)
- [ ] TR10 Regression gate: confirm all existing US1 unit and integration tests still pass and that no current runtime behaviour has changed as a result of this phase.

**Checkpoint**: Architecture Readiness complete. Outbox + relay (commit-before-publish), idempotency foundation, workflow version pinning, correlation-ID propagation, workflow lifecycle events, and the submission-triggered finding-generation decision are all in place. Audit remains synchronous and transactional. US2 may now begin.

---

## Phase 4: User Story 2 — Document Intelligence and Evidence Core

**Goal**: End-to-end document ingestion pipeline producing Evidence with full provenance. Intelligence Orchestrator coordinates the pipeline. Findings generated with complete attribution and Evidence Snapshots.

**Independent Test**: Upload a document; wait for ingestion to complete; verify Evidence items exist with all seven provenance attributes; retrieve a Finding with all five explainability fields and four attribution fields; verify Evidence Snapshot is captured. See `quickstart.md` Scenarios 2 and 3.

### Implementation for User Story 2

- [ ] T046 [P] [US2] Implement `src/mil/orchestrator/models.py` — `WorkflowRun`, `WorkflowStep` ORM models; workflow status and step status enumerations
- [ ] T047 [P] [US2] Implement `src/mil/orchestrator/repository.py` — workflow run and step persistence; step status updates
- [ ] T048 [US2] Implement `src/mil/orchestrator/retry.py` — configurable retry policy: max attempts, backoff strategy, dead-letter handling; structured error classification (retryable vs. terminal)
- [ ] T049 [US2] Implement `src/mil/orchestrator/service.py` — workflow plan construction (declarative step sequences); step dispatch to `JobQueue`; step completion and failure handling; emit `WorkflowStepFailed` audit event on unrecoverable failure
- [ ] T050 [US2] Implement `src/mil/orchestrator/subscribers.py` — `EventBus` subscriber for `DocumentIngested`; creates `WorkflowRun`; dispatches OCR job to `JobQueue`
- [ ] T051 [US2] Create Alembic migration for orchestrator schema: `workflow_runs`, `workflow_steps` tables per `data-model.md`
- [ ] T052 [P] [US2] Implement `src/providers/ocr/` — concrete `OCRProvider` implementation: returns page-level text with positional metadata and provider version string
- [ ] T053 [P] [US2] Implement `src/providers/extraction/` — concrete `ExtractionProvider` implementation: extracts typed evidence attributes from OCR result; returns all seven provenance fields and provider version
- [ ] T054 [P] [US2] Create `tests/providers/test_ocr_conformance.py` — OCRProvider conformance tests: verifies page text returned; provider version present; structured errors on failure
- [ ] T055 [P] [US2] Create `tests/providers/test_extraction_conformance.py` — ExtractionProvider conformance tests: verifies all seven provenance attributes present; provider version returned; confidence in [0, 1]
- [ ] T056 [US2] Implement `src/mil/document/service.py` pipeline path — OCR step: delegates to `OCRProvider`; updates document status to IN_PROGRESS; records step completion in orchestrator
- [ ] T057 [P] [US2] Implement `src/mil/evidence/models.py` — `EvidenceItem`, `EvidenceRelationship`, `EvidenceSnapshot` ORM models; all seven provenance fields mapped; `supersedes_id` self-referential FK
- [ ] T058 [P] [US2] Implement `src/mil/evidence/repository.py` — append-only evidence item writes (no UPDATE, no DELETE); relationship writes; snapshot writes; supersession chain queries
- [ ] T059 [US2] Implement `src/mil/evidence/service.py` — create evidence item from extraction result; enforce all seven provenance attributes are present and non-null (raise `DomainError` if any missing); emit `EVIDENCE_CREATED` audit event
- [ ] T060 [US2] Implement `src/mil/evidence/snapshot.py` — capture evidence snapshot at finding generation time: record all evidence item IDs referenced as append-only rows in `evidence.evidence_snapshots`
- [ ] T061 [US2] Create Alembic migration for evidence schema: `evidence.evidence_items`, `evidence.evidence_relationships`, `evidence.evidence_snapshots` per `data-model.md`; no UPDATE or DELETE on `evidence_items`
- [ ] T062 [P] [US2] Implement `src/mil/policy/models.py` — `PolicyPack` ORM model; active pack enforcement (only one active per tenant at a time)
- [ ] T063 [P] [US2] Implement `src/mil/policy/loader.py` — YAML Policy Pack loading; SHA-256 content hash verification; version registration; activate/deactivate lifecycle
- [ ] T064 [P] [US2] Implement `src/mil/policy/engine.py` — rule evaluation: takes evidence items and active policy pack; returns triggered rule identifiers and evaluation metadata; never hardcodes verification logic
- [ ] T065 [P] [US2] Implement `src/mil/policy/repository.py` — policy pack CRUD; active pack lookup; version history queries
- [ ] T066 [US2] Create Alembic migration for policy schema: `core.policy_packs` (finalize); `policy_rules` table
- [ ] T067 [P] [US2] Implement `src/mil/finding/models.py` — `Finding` ORM model; all five explainability fields (title, rationale, evidence_summary, confidence_label, recommended_action) marked NOT NULL; all four attribution fields (model_version, prompt_version, policy_pack_id, extraction_version) marked NOT NULL; `FindingLifecycleState` enumeration; `FindingPartyRef` association table
- [ ] T068 [P] [US2] Implement `src/mil/finding/lifecycle.py` — finding state machine: valid transition table; `transition(finding, action, actor) -> Finding`; raises `InvalidStateTransition` for invalid transitions; emits `FINDING_STATE_CHANGED` audit event on every transition
- [ ] T069 [P] [US2] Implement `src/mil/finding/repository.py` — finding persistence; party reference writes; finding queries by application, state, party, type
- [ ] T070 [US2] Implement `src/mil/finding/service.py` — finding generation from policy engine output: populates all five explainability fields and all four attribution fields from inference result; captures evidence snapshot before persisting finding; emits `FINDING_GENERATED` audit event; emits `EVIDENCE_SNAPSHOT_CREATED` audit event
- [ ] T071 [US2] Create Alembic migration for finding schema: `finding.findings`, `finding.finding_party_refs` per `data-model.md`
- [ ] T072 [US2] Implement `src/workers/document_pipeline.py` — Document Pipeline Worker: picks up OCR and Extraction jobs from `JobQueue`; executes via `document.service` and `evidence.service`; reports step completion to orchestrator; stateless, idempotent
- [ ] T073 [US2] Implement `src/workers/finding_generation.py` — Finding Generation Worker: picks up FindingGeneration jobs from `JobQueue`; runs policy engine then finding service; reports completion to orchestrator; stateless, idempotent
- [ ] T074 [US2] Create `Dockerfile` for `mil-worker` container; wire both Document Pipeline and Finding Generation workers
- [ ] T075 [US2] Implement `src/mil/api/v1/evidence.py` — REST endpoints: `GET /v1/applications/{id}/evidence`, `GET /v1/applications/{id}/evidence/{ev_id}`, `GET /v1/applications/{id}/evidence/{ev_id}/relationships`; validate against `contracts/evidence.yaml`; all seven provenance attributes required in response serialiser
- [ ] T076 [US2] Implement `src/mil/api/v1/findings.py` (read endpoints only) — `GET /v1/applications/{id}/findings`, `GET /v1/applications/{id}/findings/{fid}`; validate against `contracts/findings.yaml`; all five explainability fields required in serialiser; reject serialisation if any field is empty
- [ ] T077 [US2] Integration test in `tests/integration/test_document_pipeline.py`: upload document → wait for COMPLETED status → retrieve evidence → assert all seven provenance attributes non-null on every item → assert `EVIDENCE_CREATED` audit event exists
- [ ] T078 [US2] Integration test in `tests/integration/test_evidence_chain.py`: trigger finding generation → assert `evidence_snapshots` rows captured → assert Finding has all five explainability fields and four attribution fields → assert `EVIDENCE_SNAPSHOT_CREATED` and `FINDING_GENERATED` audit events exist

**Checkpoint**: Document Intelligence complete. Document upload → Evidence extraction → Finding generation operates end-to-end and is independently testable.

---

## Phase 5: User Story 3 — Human Review, Verification, and Explainability

**Goal**: Complete the human-in-the-loop review cycle. Reviewers can verify, override, and escalate findings. The finding lifecycle operates fully. Mortgage Readiness assessed correctly.

**Independent Test**: Verify a finding; override a finding (assert all required fields captured); attempt to transition an overridden finding (assert rejection); check readiness reflects unresolved count. See `quickstart.md` Scenarios 4, 5, and 7.

### Implementation for User Story 3

- [ ] T079 [P] [US3] Implement `src/mil/review/models.py` — `Verification` ORM model; all required override fields: `reviewer_id`, `action`, `previous_state`, `new_state`, `previous_value`, `new_value`, `reason`, `recorded_at`
- [ ] T080 [P] [US3] Implement `src/mil/review/repository.py` — append-only verification writes; verification history queries by finding; emits `VERIFICATION_RECORDED` or `OVERRIDE_RECORDED` audit event
- [ ] T081 [US3] Implement `src/mil/review/service.py` — `verify(finding_id, reviewer)`, `override(finding_id, new_value, reason, reviewer)`, `escalate(finding_id, reason, reviewer)`, `resolve(finding_id, reason, reviewer)`; delegates state transition to `finding.lifecycle`; validates `reason` is non-empty for override and escalate; emits audit events
- [ ] T082 [US3] Create Alembic migration for review schema: `review.verifications` per `data-model.md`; no UPDATE or DELETE
- [ ] T083 [US3] Complete `src/mil/finding/lifecycle.py` — implement all terminal transition guards: VERIFIED, OVERRIDDEN, RESOLVED reject any further transition with `InvalidStateTransition`; ESCALATED → RESOLVED is the only valid post-escalation transition
- [ ] T084 [US3] Complete `src/mil/api/v1/findings.py` — add action endpoints: `POST /v1/applications/{id}/findings/{fid}/verify`, `POST /v1/applications/{id}/findings/{fid}/override`, `POST /v1/applications/{id}/findings/{fid}/escalate`, `POST /v1/applications/{id}/findings/{fid}/resolve`; validate request bodies against `contracts/findings.yaml`; `reason` field minimum length enforced
- [ ] T085 [P] [US3] Implement cross-document verification finding type in `src/mil/finding/service.py` — income cross-reference: compare MONTHLY_INCOME evidence items across documents for the same party; surface INCOME_INCONSISTENCY finding if values differ beyond policy threshold
- [ ] T086 [US3] Implement Mortgage Readiness assessment in `src/mil/application/service.py` — evaluate: missing required evidence types per policy, unresolved findings count, incomplete verifications count; return structured `ReadinessAssessment`
- [ ] T087 [US3] Add readiness endpoint to `src/mil/api/v1/applications.py` — `GET /v1/applications/{id}/readiness`; validate against `contracts/applications.yaml` ReadinessAssessment schema
- [ ] T088 [US3] Integration test in `tests/integration/test_finding_lifecycle.py`: exercise all valid transitions; assert terminal state rejects further transitions with HTTP 409; assert each transition produces a `FINDING_STATE_CHANGED` audit event; assert override record captures reviewer_id, reason, previous_value, new_value
- [ ] T089 [US3] Integration test (extend `tests/integration/test_audit_immutability.py`): assert policy version change does not alter existing findings; assert `POLICY_PACK_ACTIVATED` audit event recorded with distinct sequence number from AI model version change events

**Checkpoint**: Human review lifecycle fully functional. US1, US2, and US3 are all independently testable in sequence (full quickstart.md scenarios 1–5 and 7 pass).

---

## Phase 6: User Story 4 — Evidence Copilot and Operational Intelligence

**Goal**: Reviewers can query evidence interactively using natural language. Operations managers have real-time visibility into queue state, SLA compliance, and bottlenecks.

**Independent Test**: Submit Copilot query; assert response contains citations to evidence items belonging to the queried application only; query second application's context; assert evidence from first application not returned. See `quickstart.md` Scenarios 6 and 8.

### Implementation for User Story 4

- [ ] T090 [P] [US4] Implement `src/providers/inference/` — concrete `InferenceProvider` implementation: structured evidence context window; model version and prompt version returned in result; configurable endpoint (supports on-premises or managed inference)
- [ ] T091 [P] [US4] Create `tests/providers/test_inference_conformance.py` — InferenceProvider conformance tests: verifies model version and prompt version present in result; verifies evidence context scoping enforced; verifies structured errors on failure
- [ ] T092 [US4] Implement `src/mil/copilot/grounding.py` — evidence grounding layer: retrieves evidence items scoped strictly to `application_id` and requesting user permissions; assembles structured evidence context (typed fields, not raw text); validates scope before passing to inference; raises `ScopeViolation` if evidence from another application is detected
- [ ] T093 [US4] Implement `src/mil/copilot/prompt_builder.py` — builds typed prompt templates for the seven Copilot query types (explain finding, flagging rationale, evidence attribution, document contradictions, application summary, evidence gaps, change history); enforces least-data principle: only evidence fields required by the specific query are included
- [ ] T094 [US4] Implement `src/mil/copilot/service.py` — orchestrates grounding → prompt building → `InferenceProvider.infer()` → citation extraction → response assembly; enforces `is_evidence_grounded` flag; emits `COPILOT_QUERY_SUBMITTED` audit event with model version and prompt version
- [ ] T095 [US4] Implement `src/mil/api/v1/copilot.py` — REST endpoints: `POST /v1/applications/{id}/copilot/query`, `GET /v1/applications/{id}/copilot/history`; validate against `contracts/copilot.yaml`; every response must include non-empty `citations` array
- [ ] T096 [P] [US4] Implement `src/mil/operational/models.py` — `QueueSnapshot`, `SLAConfig` ORM models per `data-model.md`
- [ ] T097 [P] [US4] Implement `src/mil/operational/repository.py` — snapshot writes; SLA config reads; queue ageing queries; bottleneck indicator queries (high override rate by document type, high rework by policy rule)
- [ ] T098 [US4] Implement `src/mil/operational/service.py` — SLA evaluation (compare finding age to `SLAConfig` thresholds; classify as within SLA, at risk, or breached); queue ageing aggregation per lifecycle state; turnaround analytics; workload distribution by reviewer; bottleneck analysis
- [ ] T099 [US4] Create Alembic migration for operational schema: `oi.sla_configs`, `oi.queue_snapshots` per `data-model.md`
- [ ] T100 [US4] Implement `src/workers/operational_snapshots.py` — Operational Intelligence Worker: scheduled at configurable interval; runs queue snapshot generation and SLA threshold evaluation; emits observability metrics; single instance per deployment
- [ ] T101 [US4] Create `Dockerfile` for `mil-scheduler` container; wires `operational_snapshots` worker with configurable interval
- [ ] T102 [US4] Implement `src/mil/api/v1/operational.py` — REST endpoints: `GET /v1/operational/dashboard`, `GET /v1/operational/queues`, `GET /v1/operational/sla`, `GET /v1/operational/turnaround`, `GET /v1/operational/bottlenecks`; validate against `contracts/operational.yaml`; all data in aggregate form only
- [ ] T103 [US4] Integration test in `tests/integration/test_copilot_isolation.py`: query Copilot for application A; assert all `evidence_item_id` values in citations belong to application A; query Copilot for application B; assert evidence from application A absent from response; assert `evidence_scope_count` matches application B's evidence count

**Checkpoint**: Evidence Copilot and Operational Intelligence functional. All quickstart.md scenarios (1–8) pass.

---

## Phase 7: User Story 5 — Enterprise Integration Framework

**Goal**: MIL connects to LOS platforms via the LOSAdapter pattern. Multi-tenant data isolation enforced. Deployment supports data residency configuration and future intelligence modules.

**Independent Test**: Inbound LOS webhook received; application data translated via LOSAdapter; application created in MIL; readiness status dispatched to LOS via outbound event; tenant A data inaccessible from tenant B's authenticated context.

### Implementation for User Story 5

- [ ] T104 [P] [US5] Implement `src/providers/los/wipro_netoxml_adapter.py` — concrete `LOSAdapter` for Wipro NetOxygen: maps NetOxml application data to MIL `ApplicationData`; maps document references to MIL `DocumentReference` format
- [ ] T105 [P] [US5] Implement `src/providers/los/encompass_adapter.py` — concrete `LOSAdapter` for Encompass: maps Encompass application data to MIL `ApplicationData`; handles Encompass-specific field naming and date formats
- [ ] T106 [US5] Implement `src/mil/integration/webhook.py` — inbound webhook handler: authenticates inbound LOS event (HMAC or token); routes to appropriate `LOSAdapter`; triggers document ingestion workflow via `EventBus`
- [ ] T107 [US5] Implement `src/mil/integration/dispatcher.py` — outbound event dispatcher: sends readiness status and finding summaries to LOS via `LOSAdapter.notify_readiness()`; records dispatch in `webhook_deliveries` with retry on failure
- [ ] T108 [US5] Create Alembic migration for integration schema: `integration_configs`, `webhook_deliveries` tables
- [ ] T109 [US5] Enforce `tenant_id` data isolation in all repositories: ABAC policies enforce that queries are always filtered by the requesting user's `tenant_id`; cross-tenant access raises `AccessDenied` audit event and HTTP 403
- [ ] T110 [US5] Implement data residency configuration in `src/mil/kernel/config.py` — deployment-time region selection for database, object storage, and inference endpoint; verify no data crosses region boundary in normal operation
- [ ] T111 [US5] Create extensibility scaffold in `src/mil/` — stub modules for future intelligence modules: `src/mil/fraud/`, `src/mil/regulatory/`, `src/mil/portfolio/`, `src/mil/ai_quality/`; each stub registers an `EventBus` subscriber and documents its integration contract

**Checkpoint**: Enterprise Integration Framework operational. LOS adapter pattern validates across two LOS implementations. Tenant isolation enforced end-to-end.

---

## Phase 8: Polish and Cross-Cutting Concerns

**Purpose**: Quality hardening, performance validation, compliance documentation. Affects all user stories.

- [ ] T112 [P] Security review: validate RBAC denies access when role lacks permission (`tests/unit/identity/test_rbac.py`); validate ABAC denies cross-application access even with valid role (`tests/unit/identity/test_abac.py`)
- [ ] T113 [P] Contract test suite in `tests/contract/`: verify all eight API endpoints respond with schemas conforming to `contracts/` OpenAPI specifications; verify all Finding responses include all five explainability fields; verify all Evidence responses include all seven provenance attributes
- [ ] T114 Performance validation: measure document ingestion pipeline duration for a 20-page test document; assert < 60 seconds end-to-end; measure API p95 latency for interactive reviewer endpoints; assert < 300ms
- [ ] T115 [P] Operational alert configuration: document ingestion failure rate alert (> 1%); evidence extraction all-null provenance alert; audit event write failure alert (critical); API latency threshold alerts; document in `docs/observability.md`
- [ ] T116 [P] Compliance documentation package: audit trail completeness evidence (demonstrate full lifecycle reconstruction via quickstart Scenario 5); regulatory alignment evidence mapping platform outputs to FR-047–050; document in `docs/compliance.md`
- [ ] T117 Run complete `quickstart.md` validation (all 8 scenarios); confirm all pass; confirm failure modes produce correct HTTP status codes and audit events

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Platform Kernel (Phase 2) — no dependency on other user stories
- **Architecture Readiness (Phase 3.5)**: Depends on US1 (Phase 3) — **BLOCKS US2 (Phase 4)**; governed by ADR-007, ADR-008, ADR-009
- **US2 (Phase 4)**: Depends on US1 (Platform Foundation) **and on Architecture Readiness (Phase 3.5)** — requires Application, Document, Audit infrastructure plus the outbox, idempotency, version-pinning, and correlation-ID foundations
- **US3 (Phase 5)**: Depends on US2 (finding generation must exist to verify/override)
- **US4 (Phase 6)**: Depends on US2 (evidence must exist for Copilot); OI component depends only on US1 and can proceed in parallel with US3
- **US5 (Phase 7)**: Depends on US1 (Application/Party); Integration Gateway independent of US2–US4
- **Polish (Phase 8)**: Depends on all user stories

### Within Each User Story

- Models before repositories
- Repositories before services
- Services before API endpoints
- Integration tests after all services in the story are complete

### Parallel Opportunities

Within Phase 2 (Foundational):
- T007–T009 can run in parallel (types, errors, config are independent)
- T015–T019 (all provider interfaces) can run in parallel
- T021–T023 (middleware files) can run in parallel after T020

Within Phase 3 (US1):
- T029–T032 (identity models, RBAC, ABAC, provider) can run in parallel
- T034–T035 (application models and repository) can run in parallel after T033

Within Phase 4 (US2):
- T046–T047 (orchestrator models and repository) can run in parallel
- T052–T055 (OCR and Extraction provider implementations and conformance tests) can all run in parallel
- T057–T062 (evidence models, repository, service, snapshot, and policy models) can run in parallel after T056

---

## Implementation Strategy

The task list represents the complete implementation backlog for the Mortgage Intelligence Layer (MIL) platform. Development will proceed through incremental engineering milestones rather than attempting to implement the full backlog in one iteration. Each milestone must result in a demonstrable, independently testable platform increment. No subsequent milestone begins until the previous milestone has passed architecture review, code review, integration testing, and demonstration.

### Milestone 1 — Platform Foundation

**Phases**: Phase 1 (Setup) · Phase 2 (Platform Kernel) · Phase 3 (US1)

**Deliverable**: Secure platform foundation with Identity, Audit, Applications, Parties, Document Upload, and Platform Kernel.

**Demonstration criteria**: Application created; parties added; document uploaded; audit events recorded with consecutive sequence numbers; Zero Trust middleware enforced on all routes.

### Milestone 2 — Mortgage Intelligence Core

**Phases**: Phase 3.5 (Architecture Readiness) · Phase 4 (US2)

> Phase 3.5 is a prerequisite gate, not a user story. It hardens the event,
> transaction, and coordination architecture (ADR-007, ADR-008, ADR-009) before
> any US2 intelligence code is written, and changes no current runtime behaviour.

**Deliverable**: End-to-end document processing producing Evidence, Findings, and Evidence Snapshots through the Intelligence Orchestrator.

**Demonstration criteria**: Document ingested; Evidence items created with all seven provenance attributes; Finding generated with all five explainability fields, all four attribution fields, and a captured Evidence Snapshot; audit trail complete for the full pipeline.

> **This is the first enterprise MVP demonstration.**

### Milestone 3 — Human Review

**Phases**: Phase 5 (US3)

**Deliverable**: Complete human verification workflow including review, override, escalation, readiness assessment, and explainability.

**Demonstration criteria**: All finding lifecycle transitions exercised; terminal state rejects further transitions; override record captures all required fields; Readiness assessment reflects current evidence and finding state.

### Milestone 4 — Intelligence Workspace

**Phases**: Phase 6 (US4)

**Deliverable**: Evidence Copilot and Operational Intelligence dashboards.

**Demonstration criteria**: Copilot returns evidence-grounded response with citations scoped to the queried application; evidence from a second application absent from the first application's Copilot context; Operational dashboard data is fresh within five minutes.

### Milestone 5 — Enterprise Platform

**Phases**: Phase 7 (US5) · Phase 8 (Polish)

**Deliverable**: LOS integrations, multi-tenancy, deployment hardening, compliance validation, and production readiness.

**Demonstration criteria**: LOSAdapter translates inbound application data from at least two LOS platforms; cross-tenant data isolation enforced at HTTP and repository layers; all quickstart.md scenarios pass; compliance documentation package complete.

---

> The task list remains the authoritative engineering backlog. Milestones define execution order, demonstration points, and release cadence only; they do not alter task dependencies or architecture.

---

## Notes

- [P] tasks = different files, no dependencies within the same phase
- All tasks must be completed in ID order within a phase unless marked [P]
- Every provider implementation must pass its conformance test before being registered in the DI container
- `audit.audit_events` must have INSERT-only permission at the database level, not only in application code — verify this in T024 and T045
- Audit events must be written synchronously for interactive API operations; asynchronously is acceptable for background worker operations with compensation on failure
- No Finding may be persisted without a captured Evidence Snapshot — enforce this in `finding.service`, not only in the API layer
- All five explainability fields are mandatory in the `Finding` serialiser — a finding with empty `recommended_action` must not reach the API response
