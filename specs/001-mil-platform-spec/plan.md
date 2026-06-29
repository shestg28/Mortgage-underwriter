# Implementation Plan: Mortgage Intelligence Layer (MIL) — Foundational Platform

**Branch**: `001-mil-platform-spec` | **Date**: 2026-06-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-mil-platform-spec/spec.md`

---

## Summary

MIL is an API-first intelligence layer for regulated mortgage processing. It ingests documents,
extracts structured evidence, generates explainable findings, and supports human review workflows
— all with full auditability. This plan defines the modular monolith architecture that will
deliver the platform in five incremental phases, from domain foundation through enterprise
operational readiness.

The primary architectural decision — modular monolith over distributed microservices — is
justified in full below. The bounded context model and domain entities are defined to support
future controlled extraction of individual modules into independent services when scale requires it.

---

## Technical Context

**Language/Version**: Python 3.12+ (primary platform language for AI/ML integration and
enterprise web service development; strong ecosystem for document processing and LLM orchestration)

**Primary Dependencies**: FastAPI (ASGI web framework), SQLAlchemy (ORM and schema management),
Pydantic (data validation and serialisation), OpenTelemetry (observability), Alembic (schema
migration). Background job processing uses the Platform Kernel's `EventBus` and `JobQueue`
abstractions; the message broker implementation is a replaceable deployment configuration.

**Storage**:
- PostgreSQL — primary relational store for structured evidence, findings, verifications,
  audit events, and application state
- Object storage (S3-compatible) — immutable document archive
- Message broker (Redis, AMQP-compatible, or equivalent) — backing store for the event bus and
  job queue; selected at deployment time; the platform core has no compile-time dependency on
  the broker implementation
- Short-lived cache — operational dashboard aggregates and read-through caches; broker-agnostic

**Testing**: pytest + pytest-asyncio, factory_boy for test fixtures, httpx for API contract
testing, testcontainers for integration testing against real infrastructure

**Target Platform**: Linux server (containerised); designed for private cloud, on-premises, or
managed cloud deployment. No cloud-vendor-specific dependencies in the core platform.

**Project Type**: Web service (backend API platform) with background processing pipelines

**Performance Goals**:
- Document ingestion pipeline: complete initial evidence extraction within 60 seconds for a
  standard 20-page mortgage document
- API response latency: p95 < 300ms for interactive reviewer endpoints (finding retrieval,
  verification submission, Copilot queries)
- Audit event write latency: < 50ms (synchronous, non-blocking from the caller's perspective)
- Operational dashboards: data freshness < 5 minutes

**Constraints**:
- Evidence and audit records are immutable once written — no UPDATE or DELETE on these tables
- All PII must be encrypted at rest; column-level encryption for high-sensitivity fields
- AI inference contexts must be isolated per-application (no cross-application prompt leakage)
- Platform must be deployable in air-gapped environments (no mandatory external SaaS dependencies)
- Zero Trust: every inbound request must be authenticated and authorised regardless of origin

**Scale/Scope**:
- Initial target: single-institution deployment processing 500–5,000 applications per month
- Architecture must accommodate 10x growth (50,000 applications/month) via horizontal scaling
  of stateless components without data model changes
- Multi-tenancy (multiple institutions on a shared deployment) is a Phase 5 concern; the
  architecture must not preclude it

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| **I. Human Decision Authority** | No component may make autonomous lending decisions. All Finding terminal states require a human action. | ✅ PASS — lifecycle model enforces human-in-the-loop for all terminal Finding states |
| **II. Evidence First** | All seven provenance attributes present on every Evidence object. Evidence Snapshot captured at Finding generation. | ✅ PASS — domain model mandates provenance fields; snapshot recorded as immutable FK reference |
| **III. Explainability by Default** | Every Finding surfaced to a user includes all five explainability fields. | ✅ PASS — Finding entity schema requires all five fields; serialiser validation enforced at API boundary |
| **IV. Trust Before Automation** | No automation introduced beyond evidence extraction and finding generation; all verification decisions are human. | ✅ PASS — no automated verification in scope; Copilot is advisory only |
| **V. Security and Privacy by Design** | Zero Trust, RBAC/ABAC, encryption, AI context isolation, data minimisation implemented from Phase 1. | ✅ PASS — security architecture defined in this plan; all controls are Phase 1 requirements |
| **VI. API-First Integration** | All capabilities exposed through versioned REST APIs. No LOS-specific coupling in core platform. | ✅ PASS — Integration Gateway bounded context provides LOS adapters; core domain has no LOS dependency |
| **VII. Domain-Driven Design** | All canonical entities present and correctly named. No technical abstractions obscuring domain language. | ✅ PASS — domain model maps directly to spec entities; no generic CRUD abstractions |
| **VIII. Auditability** | Immutable Audit Events for all significant actions. Finding lifecycle state transitions logged. Override records capture all required fields. | ✅ PASS — audit module writes append-only; all state transitions emit Audit Events |
| **IX. Incremental Evolution** | Plan uses phased delivery; no complete rewrites; new phases are additive. | ✅ PASS — five phases, each additive and independently deployable |
| **X. Operational Excellence** | Observability (structured logging, tracing, metrics) is Phase 1 requirement. Operational Intelligence dashboards in Phase 3. | ✅ PASS — OpenTelemetry instrumentation from Phase 1; OI module in Phase 3 |
| **XI. Regulatory Alignment** | Platform outputs structured for regulatory audit. Policy Packs configurable per jurisdiction. Data residency configurable. | ✅ PASS — policy engine is fully configurable; data residency is a deployment configuration |
| **XII. Deterministic Intelligence** | Every AI Finding attributed to model/prompt/policy/extraction version + timestamp. Evidence Snapshot preserved. | ✅ PASS — Finding entity carries all five attribution fields; snapshot is immutable |

**GATE RESULT: ALL PRINCIPLES PASS. Proceed to Phase 0.**

---

## Architectural Decision: Modular Monolith

### Decision

MIL will be implemented as a **Modular Monolith** for its initial platform release (Phases 1–4).
The architecture defines clean bounded context boundaries within a single deployable unit, with
explicit contracts between modules enforced through well-defined internal APIs.

### Justification

**Against premature microservices:**

1. **Evidence chain coupling**: The core MIL processing pipeline (Document → Evidence →
   Evidence Snapshot → Finding → Verification → Audit Event) requires strong consistency.
   Every step in this chain must be atomic or compensated — a distributed architecture introduces
   the complexity of sagas, eventual consistency, and distributed transaction coordination at the
   core of a regulated data product. The cost of getting this wrong is an incomplete or
   inconsistent audit trail.

2. **Regulatory auditability is hardest when distributed**: The immutability and reconstruction
   guarantees required by Principle VIII are simpler to enforce within a single process and a
   single database transaction boundary. Cross-service audit event assembly introduces ordering
   and completeness risks.

3. **Domain boundaries are still stabilising**: This is version 1 of a new domain model.
   Distributed services require stable contracts between them; extracting a service prematurely
   locks in a boundary that may need to change as the domain is better understood. A modular
   monolith allows internal boundary revision without breaking external consumers.

4. **Operational security surface**: Each additional service is an additional network endpoint,
   authentication boundary, and deployment artefact. A modular monolith has a smaller attack
   surface and is easier to secure, audit, and maintain for the initial regulated deployment.

5. **Enterprise deployment reality**: Most initial enterprise customers will deploy MIL in a
   single institution environment with conservative infrastructure. A monolith is easier to
   deploy, operate, and support in an on-premises or private cloud context.

**Preserving future extractability:**

The modular monolith is designed with clean module boundaries:
- Each bounded context is a Python package with explicit public interfaces
- Inter-module communication uses defined service interfaces, not direct model access
- No module imports from another module's internal implementation
- Each module owns its own database tables and schema migrations

This design allows any bounded context to be extracted into an independent service in a future
phase without changing the domain model, the API contracts, or the audit record structure.

**The candidate for first extraction** (if and when scale demands it) is Document Processing,
which is naturally asynchronous, CPU/memory-intensive, and has the clearest service boundary.

### Trade-offs Accepted

| Trade-off | Accepted Because |
|---|---|
| Single deployment unit limits independent scaling of processing components | Background worker processes are independently scalable — the Intelligence Orchestrator decouples pipeline execution from the API process; worker replicas can be added without redeploying the API |
| Schema changes affect all modules | Strict migration discipline and module-owned table namespaces mitigate coupling |
| Cannot use different technology stacks per module | Domain complexity is better served by consistency; polyglot introduces operational burden |

---

## Bounded Contexts

| Bounded Context | Responsibility | Owns |
|---|---|---|
| **Platform Kernel** | Configuration management, event definitions, shared security primitives, observability primitives, common domain types, error contracts, dependency injection wiring. Depended on by all other bounded contexts. | No domain tables; `kernel/` package only |
| **Intelligence Orchestrator** | Orchestration of document processing workflows, AI pipeline coordination, retry handling, workflow state, execution sequencing. Does not own business logic or persistence for Evidence or Findings. | `workflow_runs`, `workflow_steps` tables |
| **Application & Party** | Application lifecycle state, Party management, document association | `applications`, `parties`, `party_documents` tables |
| **Document Processing** | Document ingestion, format handling, evidence extraction pipeline; delegates AI extraction to `ExtractionProvider` and storage to `StorageProvider` | `documents`, `extractions` tables; object storage references via `StorageProvider` |
| **Evidence Management** | Evidence store, provenance, immutability, relationships, snapshots | `evidence`, `evidence_snapshots`, `evidence_relationships` tables |
| **Policy Engine** | Policy Pack loading, versioning, rule evaluation against evidence | `policy_packs`, `policy_rules`, `policy_versions` tables |
| **Finding Management** | Finding generation, lifecycle state machine, attribution | `findings`, `finding_attributions`, `finding_evidence_refs` tables |
| **Review & Verification** | Human review workflows, verification and override recording | `verifications`, `overrides` tables |
| **Evidence Copilot** | Evidence-grounded natural language query; response generation; delegates inference to `InferenceProvider` | No owned tables; reads from Evidence and Finding bounded contexts |
| **Audit & Governance** | Append-only Audit Event log; compliance reporting | `audit_events` table (append-only, separate schema) |
| **Operational Intelligence** | SLA tracking, queue ageing, turnaround analytics, workload | `oi_snapshots`, `oi_sla_configs` tables; materialised views |
| **Integration Gateway** | LOS adapters (via `LOSAdapter` interface), inbound webhook handling, outbound event dispatch | `integration_configs`, `webhook_deliveries` tables |
| **Identity & Access** | RBAC/ABAC enforcement, session management, identity provider integration | `roles`, `permissions`, `role_assignments` tables |

---

## Platform Kernel

The Platform Kernel is a shared package (`mil/kernel/`) that every bounded context imports.
It is the only cross-cutting dependency in the monolith. All other cross-context imports are
forbidden — bounded contexts communicate through published service interfaces or domain events,
not direct package imports.

**Platform Kernel responsibilities:**

| Area | Contents |
|---|---|
| **Configuration** | Typed settings schema; environment-variable loading; deployment-profile resolution |
| **Event definitions** | Canonical domain event types (`DocumentIngested`, `EvidenceExtracted`, `FindingGenerated`, etc.); `EventBus` abstract interface |
| **Job queue** | `JobQueue` abstract interface; `Job` base type; worker registration contract |
| **Security primitives** | `AuthenticatedUser` context type; permission constants; RBAC/ABAC enforcement hooks; encryption helper interfaces |
| **Observability primitives** | Structured log factory (pre-wired with mandatory fields); trace context propagation helpers; metric emitter interface |
| **Common domain types** | `ApplicationId`, `EvidenceItemId`, `FindingId`, `TenantId` and other strongly-typed identifiers; `Money`, `Confidence`, `PolicyVersion` value objects |
| **Error contracts** | Canonical error codes; `DomainError` base class hierarchy; API error response schema |
| **Dependency injection** | Container configuration; provider binding declarations |

**Dependency rule**: Bounded contexts depend on `mil/kernel/` and on the published interfaces
(`service.py`) of other bounded contexts they need. They MUST NOT import from another bounded
context's `models.py`, `repository.py`, or any internal module.

---

## Intelligence Orchestrator

The Intelligence Orchestrator (`mil/orchestrator/`) owns the coordination layer for all
multi-step AI processing workflows. It is the only component that knows the sequence of steps
in the document ingestion and finding generation pipelines. All other bounded contexts are
unaware of the pipeline they participate in.

**Responsibilities:**

- Receives domain events from the Platform Kernel event bus (e.g., `DocumentIngested`)
- Constructs and executes workflow plans — sequences of named steps with dependency ordering
- Submits individual steps to the job queue as isolated units of work
- Tracks workflow run state (`workflow_runs`, `workflow_steps` tables) — not business state
- Handles step failures: configurable retry policies, dead-letter handling, compensating actions
- Emits pipeline-level observability events (workflow started, step completed, workflow failed)
- Escalates unrecoverable failures to the Audit & Governance module via the event bus

**What the Orchestrator does NOT own:**

- Evidence extraction logic (owned by Document Processing, delegated to `ExtractionProvider`)
- Finding generation logic (owned by Finding Management)
- Evidence storage (owned by Evidence Management)
- Business rules (owned by Policy Engine)

The Orchestrator treats each step as a black box. It knows inputs, outputs, and success/failure
signals — not internal business logic. This makes the pipeline testable step-by-step and
ensures that business logic changes do not require orchestration changes.

**Workflow definitions are declarative** — pipeline sequences are defined in configuration,
not code, making it possible to adjust processing order, add steps, or disable steps without
a code change.

---

## Provider Abstractions

Provider interfaces are architectural extension points defined in the Platform Kernel. Each
provider interface represents a category of external capability that the platform requires but
does not implement directly. Concrete implementations are registered in the dependency injection
container at startup and are fully substitutable without changing business logic.

| Provider | Interface | Responsibility |
|---|---|---|
| **OCRProvider** | `mil/kernel/providers/ocr.py` | Converts scanned and image-based documents into machine-readable text and structured layout; returns page-level text with positional metadata |
| **ExtractionProvider** | `mil/kernel/providers/extraction.py` | Extracts structured Evidence attributes from document text and layout; returns typed evidence items with confidence scores and field locations; records its own version identifier |
| **InferenceProvider** | `mil/kernel/providers/inference.py` | Executes prompted inference against a scoped evidence context; returns structured responses with token attribution; records model version and prompt version used |
| **StorageProvider** | `mil/kernel/providers/storage.py` | Stores and retrieves immutable document files; returns content-addressed references; ensures durability and content integrity (hash verification) |
| **LOSAdapter** | `mil/kernel/providers/los_adapter.py` | Translates between MIL's domain model and a specific LOS data format; each LOS is a separate implementation; the core platform has no LOS-specific code |

**Interface contract requirements:**

- Every provider method that produces an AI output MUST return the provider's version identifier
  as part of the response — this populates the attribution fields on Evidence and Finding entities
- Provider implementations are tested against a conformance test suite in `tests/providers/`
  to verify that any concrete implementation satisfies the interface contract
- Provider failures MUST propagate structured errors (using the Platform Kernel error contract)
  that the Intelligence Orchestrator can inspect to determine retry eligibility

**In-process vs. remote providers:**
The same provider interface works whether the implementation calls an in-process library or a
remote inference endpoint. This makes air-gapped deployments (using on-premises models) and
managed cloud deployments (using hosted model APIs) both first-class configurations — no code
changes required, only provider registration.

---

## Asynchronous Job Processing Architecture

MIL uses domain events as the primary coordination mechanism for asynchronous work. When a
significant state change occurs (e.g., a document is uploaded), the responsible bounded context
emits a domain event onto the `EventBus`. The Intelligence Orchestrator subscribes to these
events and dispatches workflow steps onto the `JobQueue`. Background worker processes pick up
jobs from the queue and execute them.

**Flow:**

```
API Layer
  └─ DocumentService.ingest(document)
       └─ emits: DocumentIngested (via EventBus)

Intelligence Orchestrator (subscriber)
  └─ receives: DocumentIngested
       └─ creates: WorkflowRun(document_id)
            ├─ dispatches: Job(step=OCR, document_id)
            ├─ dispatches: Job(step=Extraction, document_id)   [after OCR]
            └─ dispatches: Job(step=FindingGeneration, application_id)  [after Extraction]

Background Worker Process
  └─ picks up Job from JobQueue
       └─ executes step via bounded context service
            └─ emits: EvidenceExtracted (on success) or WorkflowStepFailed (on failure)
```

**Broker replaceability:**
The `EventBus` and `JobQueue` abstractions in the Platform Kernel have no dependency on a
specific message broker. The concrete implementation (backed by Redis, AMQP, an in-process
queue for development, or any conforming broker) is registered in the dependency injection
container at startup. Changing the broker requires only a new `JobQueue` implementation and
a container configuration change — no business logic changes.

**Worker process types:**

| Worker | Subscribes / Polls | Executes |
|---|---|---|
| **Document Pipeline Worker** | `JobQueue` — OCR and Extraction jobs | OCR and evidence extraction steps via `OCRProvider` and `ExtractionProvider` |
| **Finding Generation Worker** | `JobQueue` — FindingGeneration jobs | Finding generation via Policy Engine and Finding Management |
| **Operational Intelligence Worker** | Scheduled (configurable interval) | Queue snapshot generation; SLA threshold evaluation |

Workers are stateless processes. Any number of worker replicas may run concurrently; job
deduplication and idempotency are enforced at the `JobQueue` level.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-mil-platform-spec/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── applications.yaml
│   ├── documents.yaml
│   ├── evidence.yaml
│   ├── findings.yaml
│   ├── verifications.yaml
│   ├── audit.yaml
│   ├── copilot.yaml
│   └── operational.yaml
└── tasks.md             # Phase 2 output (speckit-tasks command)
```

### Source Code (repository root)

```text
src/
├── mil/                          # Core platform package
│   ├── kernel/                   # Platform Kernel — shared by all bounded contexts
│   │   ├── config.py             # Typed settings schema; environment resolution
│   │   ├── events.py             # Canonical domain event type definitions
│   │   ├── event_bus.py          # EventBus abstract interface
│   │   ├── job_queue.py          # JobQueue abstract interface; Job base type
│   │   ├── security.py           # AuthenticatedUser context; permission constants
│   │   ├── observability.py      # Structured log factory; trace helpers; metric emitter
│   │   ├── types.py              # Strongly-typed identifiers; shared value objects
│   │   ├── errors.py             # DomainError hierarchy; error contract types
│   │   ├── container.py          # Dependency injection wiring
│   │   └── providers/            # Provider interface definitions
│   │       ├── ocr.py            # OCRProvider interface
│   │       ├── extraction.py     # ExtractionProvider interface
│   │       ├── inference.py      # InferenceProvider interface
│   │       ├── storage.py        # StorageProvider interface
│   │       └── los_adapter.py    # LOSAdapter interface
│   ├── orchestrator/             # Intelligence Orchestrator bounded context
│   │   ├── models.py             # WorkflowRun, WorkflowStep
│   │   ├── service.py            # Workflow plan construction and dispatch
│   │   ├── subscribers.py        # Event bus subscribers (DocumentIngested, etc.)
│   │   ├── retry.py              # Retry policy definitions
│   │   └── repository.py
│   ├── application/              # Application & Party bounded context
│   │   ├── models.py
│   │   ├── service.py
│   │   └── repository.py
│   ├── document/                 # Document Processing bounded context
│   │   ├── models.py
│   │   ├── service.py            # Delegates to OCRProvider and ExtractionProvider
│   │   └── repository.py
│   ├── evidence/                 # Evidence Management bounded context
│   │   ├── models.py
│   │   ├── service.py
│   │   ├── snapshot.py           # Evidence Snapshot management
│   │   └── repository.py
│   ├── policy/                   # Policy Engine bounded context
│   │   ├── models.py
│   │   ├── engine.py             # Rule evaluation
│   │   ├── loader.py             # Policy Pack versioning
│   │   └── repository.py
│   ├── finding/                  # Finding Management bounded context
│   │   ├── models.py
│   │   ├── service.py
│   │   ├── lifecycle.py          # Finding state machine
│   │   └── repository.py
│   ├── review/                   # Review & Verification bounded context
│   │   ├── models.py
│   │   ├── service.py
│   │   └── repository.py
│   ├── copilot/                  # Evidence Copilot bounded context
│   │   ├── service.py            # Delegates inference to InferenceProvider
│   │   ├── grounding.py          # Evidence grounding and citation
│   │   └── prompt_builder.py
│   ├── audit/                    # Audit & Governance bounded context
│   │   ├── models.py
│   │   ├── writer.py             # Append-only audit event emission
│   │   └── repository.py
│   ├── operational/              # Operational Intelligence bounded context
│   │   ├── models.py
│   │   ├── service.py
│   │   └── repository.py
│   ├── integration/              # Integration Gateway bounded context
│   │   ├── adapters/             # LOSAdapter implementations (one per LOS)
│   │   ├── webhook.py
│   │   └── dispatcher.py
│   ├── identity/                 # Identity & Access bounded context
│   │   ├── models.py
│   │   ├── rbac.py
│   │   ├── abac.py
│   │   └── provider.py           # External IdP integration
│   └── api/                      # HTTP API layer (FastAPI routers)
│       ├── v1/
│       │   ├── applications.py
│       │   ├── documents.py
│       │   ├── evidence.py
│       │   ├── findings.py
│       │   ├── verifications.py
│       │   ├── audit.py
│       │   ├── copilot.py
│       │   └── operational.py
│       └── middleware/
│           ├── auth.py
│           ├── audit_context.py
│           └── telemetry.py
├── workers/                      # Background worker process entry points
│   ├── document_pipeline.py      # Document Pipeline Worker (OCR + extraction jobs)
│   ├── finding_generation.py     # Finding Generation Worker
│   └── operational_snapshots.py  # Operational Intelligence Worker (scheduled)
├── providers/                    # Concrete provider implementations
│   ├── ocr/                      # OCRProvider implementations
│   ├── extraction/               # ExtractionProvider implementations
│   ├── inference/                # InferenceProvider implementations
│   ├── storage/                  # StorageProvider implementations
│   └── los/                      # LOSAdapter implementations (one per LOS)
└── migrations/                   # Alembic schema migrations

tests/
├── contract/                     # API contract tests (httpx against running service)
├── providers/                    # Provider conformance tests (each implementation vs. interface)
├── integration/                  # Integration tests (testcontainers)
│   ├── test_document_pipeline.py
│   ├── test_evidence_chain.py
│   ├── test_finding_lifecycle.py
│   ├── test_audit_immutability.py
│   ├── test_policy_engine.py
│   └── test_orchestrator_retry.py
└── unit/                         # Unit tests per bounded context
    ├── kernel/
    ├── orchestrator/
    ├── evidence/
    ├── finding/
    ├── policy/
    └── review/
```

**Structure Decision**: Single project, web service with background workers. The `mil/` package
is the modular monolith core. `mil/kernel/` is the shared foundation; all other bounded contexts
depend on it and on each other's published service interfaces only. Provider implementations
live in `providers/` (outside the domain), registered at startup via the dependency injection
container. Background worker processes in `workers/` are thin entry points — they pick up jobs
from the `JobQueue` and call bounded context services; all business logic remains in the domain.

---

## Implementation Phases

### Phase 1 — Domain Foundation and Security Core (Weeks 1–6)

**Goal**: A working, secure platform foundation with the core domain model, authentication,
authorisation, and audit infrastructure in place. No AI capabilities yet — only the structural
backbone.

**Deliverables**:
- Platform Kernel (`mil/kernel/`): configuration, event definitions, `EventBus` and `JobQueue`
  abstractions, security primitives, observability primitives, common domain types, error
  contracts, dependency injection container
- Provider interface definitions (`mil/kernel/providers/`): all five provider interfaces with
  conformance test stubs
- Application and Party management (create, retrieve, associate documents)
- Identity & Access module (RBAC, ABAC, IdP integration, Zero Trust middleware)
- Audit & Governance module (append-only audit event writer, all entity event types)
- Document storage and archival (upload, associate with Party, `StorageProvider` implementation)
- Database schema with all core entities, migrations framework
- OpenTelemetry instrumentation wired through Platform Kernel observability primitives
- REST API skeleton with OpenAPI documentation
- Containerised deployment configuration (API process + worker process containers)

**Constitution gates**: Principles I, V, VIII, XII are the primary focus of this phase.

### Phase 2 — Document Intelligence and Evidence Core (Weeks 7–12)

**Goal**: End-to-end document ingestion pipeline producing structured evidence with full
provenance. Evidence relationships and Evidence Snapshot capture in place.

**Deliverables**:
- Intelligence Orchestrator (`mil/orchestrator/`): workflow plan construction, step dispatch,
  retry policy, event bus subscribers for `DocumentIngested` and `EvidenceExtracted`
- Document pipeline background workers (Document Pipeline Worker, Finding Generation Worker)
  using the `JobQueue` abstraction; broker-agnostic
- Document Processing bounded context: format handling for native PDFs, scanned PDFs, images,
  multi-page documents, and mixed bundles; delegates OCR to `OCRProvider` and extraction to
  `ExtractionProvider`
- Evidence extraction: `ExtractionProvider` implementation; provenance attribution for all
  seven required fields; provider version recorded on every evidence item
- Evidence Management module (immutable evidence store, evidence relationships, evidence
  snapshots)
- Policy Engine v1 (Policy Pack loading, versioning, basic rule evaluation)
- Finding generation (initial finding types: income verification, property value, identity
  consistency); `InferenceProvider` integration
- Finding lifecycle state machine (Extracted → Needs Review)
- Provider conformance tests for `OCRProvider`, `ExtractionProvider`, `InferenceProvider`
- Evidence and Finding REST API endpoints

**Constitution gates**: Principles II, VII, XII are primary focus of this phase.

### Phase 3 — Human Review, Verification, and Explainability (Weeks 13–18)

**Goal**: Complete the human-in-the-loop review cycle. Reviewers can verify, override, and
escalate findings. The full finding lifecycle operates end-to-end.

**Deliverables**:
- Review & Verification module (verify, override, escalate, resolve actions)
- Override record capture (reviewer identity, reason, previous value, new value, timestamp)
- Finding lifecycle completion (all state transitions, Audit Events per transition)
- Mortgage Readiness assessment engine (configurable checklist, readiness status API)
- Cross-document verification findings (income consistency, property value cross-reference)
- Explainability fields validated at API boundary (all five fields required on every Finding)
- Reviewer-facing REST API endpoints

**Constitution gates**: Principles I, III, IV, VIII are primary focus of this phase.

### Phase 4 — Evidence Copilot and Operational Intelligence (Weeks 19–26)

**Goal**: Interactive evidence review capability and operational visibility for mortgage
operations teams.

**Deliverables**:
- Evidence Copilot (evidence-grounded natural language query, seven representative interaction
  types, citation of specific evidence items)
- AI context isolation enforcement (per-application evidence scoping, no cross-application leakage)
- Operational Intelligence module (SLA monitoring, queue ageing, turnaround analytics,
  workload distribution, bottleneck analysis)
- Operational dashboard REST API endpoints
- Evidence Copilot REST API endpoints

**Constitution gates**: Principles I, III, X are primary focus of this phase.

### Phase 5 — Enterprise Hardening and Integration Framework (Weeks 27–36)

**Goal**: Production-ready enterprise deployment with LOS integration framework, data residency
support, multi-institution configuration, and performance validation.

**Deliverables**:
- Integration Gateway (LOS adapter framework, inbound webhook handling, outbound event dispatch)
- Reference LOS adapters (Wipro NetOxygen, Encompass integration patterns)
- Multi-institution configuration (tenant isolation at data layer, per-institution policy packs)
- Data residency configuration (deployment-time data region selection)
- Performance validation against defined targets
- Security penetration test and remediation
- Compliance documentation package (audit trail completeness, regulatory alignment evidence)
- Extensibility module scaffold (fraud intelligence, regulatory intelligence hooks)

**Constitution gates**: All principles re-validated; Principles VI, XI are primary focus.

---

## Technical Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| AI extraction accuracy below reviewer acceptance threshold | Medium | High | Phase 2 includes accuracy baseline measurement; finding acceptance rate tracked as success metric; policy rules tunable without platform release |
| Audit event volume degrades query performance at scale | Medium | High | Append-only audit table uses time-partitioned storage; audit queries use read replicas; audit schema is separate from transactional schema |
| Evidence Snapshot storage growth impacts costs | Low | Medium | Snapshots store evidence references (foreign keys), not evidence content copies; content deduplication at evidence level |
| Cross-application AI context leakage | Low | Critical | Copilot grounding layer enforces application-scoped evidence retrieval; AI inference context constructed per-request with scoped evidence only; reviewed in security phase |
| LOS integration diversity (each LOS has unique data model) | High | Medium | Integration Gateway adapter pattern isolates LOS specifics; core domain is LOS-agnostic; adapters implemented per LOS in Phase 5 |
| Policy Pack misconfiguration produces incorrect findings | Medium | High | Policy Packs require version-controlled deployment; staging environment with test evidence sets validates packs before production promotion |
| Schema migration complexity as domain model matures | Medium | Medium | Alembic with strict migration reviews; bounded context table ownership prevents cross-module migrations; blue-green deployment for zero-downtime migrations |
| Regulatory requirements differ per deployment jurisdiction | High | Medium | Policy Packs and data residency configuration externalised; jurisdiction-specific requirements captured in Policy Packs, not platform code |

---

## Testing Strategy

### Principles

- Tests are written against the domain model and API contracts, not implementation internals
- Integration tests run against real infrastructure (real database, real object storage) using
  testcontainers — no mocked databases
- Contract tests verify API responses against the OpenAPI schemas defined in `/contracts/`
- Audit immutability is tested explicitly: no test may assume an audit event can be deleted or updated
- Finding lifecycle tests cover every valid and invalid state transition

### Test Layers

**Unit tests** (per bounded context):
- Domain model validation logic (entity invariants, state machine transitions)
- Policy rule evaluation with fixture evidence sets
- Explainability field completeness validation
- Provenance attribute completeness on Evidence objects

**Integration tests** (against real infrastructure):
- End-to-end document ingestion pipeline (upload → extract → evidence created with all seven
  provenance attributes)
- Evidence Snapshot capture at Finding generation
- Finding lifecycle: all valid transitions; rejection of invalid transitions
- Human override: all required fields captured; previous value preserved; audit event written
- Audit immutability: attempt to update or delete an audit event must fail
- Policy version change: existing findings unchanged; new findings use new policy version
- Cross-document verification: income inconsistency correctly surfaced as finding

**Contract tests**:
- All API endpoints respond with schemas conforming to `/contracts/` specifications
- All Finding responses include all five explainability fields
- All Evidence responses include all seven provenance attributes

**Security tests**:
- RBAC enforcement: access denied when role lacks permission
- ABAC enforcement: cross-application data access denied even with valid role
- AI context isolation: Copilot query cannot return evidence from another application
- Audit event write-only: no DELETE or UPDATE succeeds on audit_events table

---

## Security Strategy

### Zero Trust Architecture

Every inbound request is authenticated via a validated identity token regardless of network
origin. The authentication middleware runs before any business logic. Background worker processes
authenticate using service account tokens when calling bounded context services or emitting
audit events — no network-level trust is assumed between the API process and worker processes.

### Access Control

RBAC is the primary access control mechanism, with roles aligned to the user roles defined in
the specification (Relationship Manager, Verification Officer, Credit Analyst, Underwriter,
Risk Team, Compliance Team, Audit Team, Mortgage Operations Manager).

ABAC supplements RBAC for fine-grained access: a Verification Officer may have the `findings:read`
permission at the role level, but ABAC policies restrict access to findings belonging to
applications assigned to their team.

Role and permission assignments are recorded as Audit Events.

### Data Protection

All database columns containing PII (applicant name, income figures, address, document content)
use column-level encryption with institution-managed keys. Encryption keys are never stored in
application configuration or source code.

AI inference context construction enforces the least-data principle: only evidence attributes
required by the specific prompt are included. Full applicant profiles are never passed to AI
inference as a precaution — only the specific evidence fields needed to answer the query.

### AI Context Isolation

Each Evidence Copilot request constructs its evidence context from a scoped query that filters
strictly by application ID and the requesting user's access permissions. The evidence context
is assembled and validated before being passed to the AI model. The scope enforcement is tested
as part of the security test suite.

### Secret Management

Credentials, API keys, database connection strings, and encryption keys are injected at runtime
through a secret management system (e.g., HashiCorp Vault or cloud-native equivalent). No secret
appears in source code, configuration files checked into version control, or container images.

---

## Observability Strategy

### Structured Logging

All log output is structured (JSON format) with mandatory fields: timestamp, severity, service,
request_id, application_id (where applicable), user_id (where applicable), event_type.
No free-text log messages that cannot be machine-parsed.

### Distributed Tracing

OpenTelemetry traces span the full request lifecycle including background worker processing.
Document ingestion pipeline traces connect the initial upload request to the evidence extraction
worker to the finding generation step — a single trace can reconstruct the complete pipeline
execution for any document.

### Metrics

Key metrics emitted:
- Document ingestion pipeline duration (per document type and page count)
- Evidence extraction confidence distribution
- Finding generation rate and finding lifecycle transition rates
- API endpoint latency (p50, p95, p99) per endpoint
- Audit event write latency
- Policy rule evaluation duration
- Copilot query latency and evidence items retrieved per query
- Queue depth and queue ageing per finding lifecycle state

### Alerts

Alert thresholds defined for:
- Document ingestion pipeline failure rate > 1%
- Evidence extraction with all-null provenance fields (data quality alert)
- Audit event write failures (critical — compliance risk)
- API p95 latency exceeding 300ms for interactive endpoints
- Any attempt to UPDATE or DELETE from the audit_events table (security alert)

---

## Deployment Strategy

### Containerisation

The platform is packaged as a set of container images:
- `mil-api`: The FastAPI web service (stateless; scales horizontally)
- `mil-worker`: Background worker process — runs document pipeline and finding generation jobs
  from the `JobQueue`; stateless; scales horizontally and independently of the API container
- `mil-scheduler`: Scheduled worker process — triggers operational intelligence snapshots and
  SLA evaluations on a configurable interval; single instance per deployment

### Environment Tiers

- **Development**: Single-machine compose stack; all infrastructure in containers
- **Staging**: Production-equivalent infrastructure; used for integration testing, policy pack
  validation, and security review before production promotion
- **Production**: Institutional deployment (on-premises, private cloud, or managed cloud)

### Migration Strategy

Database migrations are applied using Alembic before the new application version starts. All
migrations are backward-compatible with the previous application version to support zero-downtime
rolling deployments. Migrations that cannot be made backward-compatible require a multi-phase
deployment process documented in the migration plan.

### Data Residency

Data residency is a deployment configuration: the database, object storage, and processing
infrastructure are provisioned within the institution's chosen region. No data leaves the
institution's configured residency boundary during normal operation. AI inference is configurable
to use on-premises models or region-bound managed inference endpoints.

---

## Complexity Tracking

> No constitution violations requiring justification. All design decisions are within scope
> of the 11 (and XII) principles.

---

## Post-Phase 1 Constitution Re-Check

*To be completed after Phase 1 design artifacts are generated (data-model.md, contracts/).*

Re-check will verify that the domain model and API contracts are consistent with all constitution
principles, particularly:
- Evidence provenance fields present in the data model (Principle II)
- Finding lifecycle states correct and complete (Principle VIII)
- No API endpoint returns a Finding without all five explainability fields (Principle III)
- All Evidence Snapshot references are immutable foreign keys (Principle XII)
