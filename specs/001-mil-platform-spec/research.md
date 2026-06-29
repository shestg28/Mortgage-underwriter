# Research: Mortgage Intelligence Layer (MIL) — Architecture Decisions

**Phase 0 Output** | **Branch**: `001-mil-platform-spec` | **Date**: 2026-06-29

---

## Decision 1: Modular Monolith vs. Microservices

**Decision**: Modular Monolith for initial platform release (Phases 1–5).

**Rationale**:
The evidence processing chain (Document → Evidence → Snapshot → Finding → Verification → Audit)
requires strong consistency guarantees. Distributing this chain across services introduces
distributed transaction complexity (sagas, compensating transactions, eventual consistency) that
directly threatens the immutability and completeness of the audit record — a non-negotiable
compliance requirement. A modular monolith maintains ACID guarantees across the full chain within
a single database transaction boundary while providing the clean module separation needed for
future extraction.

The regulated financial domain also demands that the audit trail be unambiguous and complete.
In a distributed architecture, assembling a complete application lifecycle record requires
correlating events across multiple service logs, which introduces ordering and completeness
risks that are difficult to defend in a regulatory examination.

**Alternatives considered**:
- *Microservices from day one*: Rejected. The domain boundaries are still stabilising; locking
  them into service contracts prematurely would require costly breaking changes as the model
  evolves. Operational complexity (service mesh, distributed tracing, inter-service auth) is
  disproportionate to the initial scale.
- *Event-driven architecture (event sourcing)*: Considered as a complementary pattern for the
  audit log. Rejected as the primary architecture because event replay for audit reconstruction
  adds complexity without clear benefit over an append-only relational audit table. Event-driven
  patterns may be introduced for the Integration Gateway bounded context (outbound LOS events)
  in Phase 5.

**Extractability preserved**: Each bounded context is a Python package with explicit service
interfaces. No cross-context model imports. The Document Processing context is the strongest
candidate for future service extraction — it is CPU/memory-intensive, naturally asynchronous,
and has the clearest interface boundary (input: document reference; output: evidence records).

---

## Decision 2: Evidence Immutability Pattern

**Decision**: Evidence objects are immutable after creation. Corrections use a supersession
pattern: a new evidence item references the superseded item via a `supersedes_id` foreign key.

**Rationale**:
Immutability is required by the Engineering Constitution (Principle II) and by the audit
requirements of the specification. The supersession pattern preserves the original extraction
for audit purposes while making the correction discoverable. The Evidence Snapshot (captured at
Finding generation) always references the evidence items as they existed at the moment the
Finding was produced — even if those items are later superseded.

**Alternatives considered**:
- *Soft-delete with version history*: Rejected. Soft-delete leaves the door open for logical
  deletion of audit-relevant evidence, which is constitutionally incompatible.
- *Versioned evidence rows*: Considered. Rejected in favour of supersession because versioning
  at the row level makes the "original extraction" harder to identify and requires version
  predicates on all queries.

---

## Decision 3: Finding Lifecycle State Machine

**Decision**: Findings use an explicit state machine with the following states and transitions:

```
Extracted ──→ Needs Review ──→ Verified   (terminal)
                         ──→ Overridden  (terminal)
                         ──→ Escalated ──→ Resolved  (terminal)
```

Needs Review is the default entry state after extraction. No Finding may bypass human action
to reach a terminal state. State transition validation is enforced in the Finding service layer,
not only at the database layer.

**Rationale**: The state machine formalises Principle I (Human Decision Authority). Every
terminal state requires an authenticated human action. The state machine is implemented in code
(not only as database constraints) so that invalid transitions produce meaningful domain errors
rather than database constraint violations.

**Alternatives considered**:
- *Simple boolean flags (is_verified, is_overridden)*: Rejected. Flags do not represent the
  lifecycle as a first-class concept, make audit querying complex, and allow invalid combinations
  (e.g., both verified and overridden simultaneously).

---

## Decision 4: Audit Event Architecture

**Decision**: Append-only audit table in a dedicated schema (`audit` schema). Application
database user has INSERT permission only on `audit.audit_events`. No UPDATE or DELETE granted.
Audit events written synchronously within the originating transaction where possible; written
asynchronously (with compensation) for background worker operations.

**Rationale**: The audit table must be tamper-evident. Restricting the application user to
INSERT-only at the database permission level provides a technical control that is harder to
bypass than application-layer controls alone. Synchronous writes for interactive operations
ensure no audit event is lost due to a worker failure.

**Alternatives considered**:
- *Separate audit microservice*: Rejected for Phase 1 (see Decision 1). The audit module
  remains in the monolith with database-level write controls.
- *File-based audit log*: Rejected. File-based logs are susceptible to rotation, deletion, and
  format drift. A relational audit table with immutability controls is more defensible in a
  regulatory context.

---

## Decision 5: Policy Pack Architecture

**Decision**: Policy Packs are YAML documents stored in versioned configuration, loaded into
the database at deployment time. The Policy Engine evaluates rules from the active Policy Pack
against evidence attributes. Rules are expressed in a domain-specific rule format (not Python
code) to ensure that policy changes do not require platform releases.

**Rationale**: The specification explicitly requires that verification logic never be hardcoded
(FR-034). Separating policy rules from platform code means institutions can update their
compliance rules through a controlled configuration change without requiring a code review,
build pipeline, or deployment of the platform itself. The domain-specific rule format also makes
rules auditable by compliance teams who are not software engineers.

**Alternatives considered**:
- *Rules as Python code*: Rejected. Code-based rules require platform deployments for policy
  changes, which is operationally burdensome and introduces software change risk into what
  should be a configuration change.
- *Rego/OPA for policy rules*: Considered. Deferred to Phase 5. OPA is powerful but introduces
  an additional operational dependency; a simpler rule format is appropriate for Phase 1.

---

## Decision 6: Evidence Copilot Grounding Architecture

**Decision**: The Evidence Copilot constructs its context window per-request by retrieving
evidence items scoped to the specific application and filtered by the requesting user's
permissions. The evidence context is assembled before the AI model is invoked. The AI model
receives structured evidence objects (not raw document text) to minimise token consumption and
enforce the least-data principle (Principle V).

**Rationale**: Evidence-grounding is the primary mechanism for preventing Copilot hallucination
and enforcing application-level isolation. By constructing the context from structured evidence
objects rather than raw documents, the grounding layer can enforce the boundary that evidence
from application A cannot appear in a Copilot response for application B. The structured format
also allows citations to be specific (evidence item ID, source document, page number) rather
than vague references to document content.

**Alternatives considered**:
- *RAG over raw document text*: Considered. Rejected for the core Copilot because raw text
  retrieval makes citation specificity harder and increases the risk of returning content from
  outside the scoped evidence set. Structured evidence retrieval is more auditable.
- *Full document context in every prompt*: Rejected on least-data principle grounds and
  practical token limits for complex multi-document applications.

---

## Decision 7: Multi-Tenancy Strategy

**Decision**: Multi-tenancy is deferred to Phase 5. For Phases 1–4, the platform is designed
for single-institution deployment. The schema and access control model are designed to
accommodate a `tenant_id` column on all core entities without requiring data model changes.

**Rationale**: Multi-tenancy introduces significant complexity in data isolation, policy
separation, and access control. Getting single-institution deployments right first reduces risk
and accelerates time to initial production. The reserved `tenant_id` column approach means the
migration to multi-tenancy is a data migration and access control policy change — not a schema
redesign.

---

## Decision 8: Provider Abstraction Architecture

**Decision**: Five explicit provider interfaces are defined in the Platform Kernel
(`OCRProvider`, `ExtractionProvider`, `InferenceProvider`, `StorageProvider`, `LOSAdapter`).
All AI, OCR, storage, and LOS interactions go through these interfaces. Concrete implementations
are registered in the dependency injection container at startup. The platform core has no
compile-time dependency on any specific implementation.

**Rationale**: Provider interfaces serve three purposes simultaneously: (1) they make the
platform vendor-agnostic and air-gap-capable (Principle VI); (2) they enforce the version
attribution contract — every provider method that produces AI output returns its version
identifier, which is recorded on Evidence and Finding entities (Principle XII); (3) they
make bounded contexts independently testable with stub implementations, without requiring real
AI model access in unit or integration test environments.

Each provider has a conformance test suite in `tests/providers/`. Any concrete implementation
must pass the conformance tests before it can be registered as a production provider.

**Alternatives considered**:
- *Direct integration with specific vendor SDKs in bounded context code*: Rejected. Vendor
  coupling in business logic makes vendor changes costly and testing dependent on external
  services. Abstraction at the provider level keeps the domain clean.
- *Single "AI provider" interface combining all AI capabilities*: Rejected. OCR, extraction,
  and inference have different contracts, different version attribution requirements, and
  different failure modes. Separate interfaces enforce the correct contract per capability.

---

## Decision 9: Asynchronous Job Processing Architecture

**Decision**: MIL uses an internal event bus and job queue abstraction (defined in the Platform
Kernel) rather than coupling to a specific background task framework. Domain events are the
coordination mechanism; the Intelligence Orchestrator translates events into job queue dispatches.
The message broker implementation is a replaceable deployment configuration.

**Rationale**: Coupling the architecture to a specific task framework (e.g., Celery) creates
a dependency that is difficult to replace if deployment constraints change (air-gapped
environments, broker technology preferences, scale requirements). The `EventBus` and `JobQueue`
abstractions in the Platform Kernel allow the broker to be replaced with a configuration change.
The use of domain events as the coordination mechanism also keeps the business language in the
pipeline — events are named after domain occurrences (`DocumentIngested`, `EvidenceExtracted`),
not technical tasks.

The Intelligence Orchestrator bounded context centralises all pipeline coordination, ensuring
that retry logic, dead-letter handling, and workflow state tracking are in one place and do
not bleed into business-logic bounded contexts.

**Alternatives considered**:
- *Celery as the task framework*: Evaluated. Rejected because it creates a compile-time
  dependency on a specific broker protocol and makes the architecture harder to adapt to
  air-gapped or enterprise-mandated broker environments. The abstraction-first approach
  achieves the same capabilities without the coupling.
- *Direct async calls (no queue)*: Rejected. Synchronous processing of document ingestion
  in the API request path would violate the performance targets and make the pipeline
  non-resilient to transient AI provider failures.

---

## Decision 10: Platform Kernel as Shared Foundation

**Decision**: A `Platform Kernel` package (`mil/kernel/`) is the sole permitted cross-cutting
dependency. All bounded contexts depend on the Kernel. No bounded context imports from another
bounded context's internal modules — only from their published `service.py` interface.

**Rationale**: Without a shared kernel, cross-cutting concerns (structured logging, typed
identifiers, error contracts) are either duplicated across bounded contexts or shared through
uncontrolled imports. Either outcome degrades the module boundary discipline over time.
The Kernel externalises this tension by providing a single, controlled location for shared
primitives. Keeping the Kernel free of domain logic (it owns types and interfaces, not
business rules) ensures it does not become a coupling point for domain concepts.

**Alternatives considered**:
- *Shared utilities module without a defined boundary*: Rejected. Uncontrolled shared modules
  tend to accumulate domain logic over time, creating hidden coupling between bounded contexts.
- *No shared code; full duplication*: Rejected. Duplicating observability primitives, typed
  identifiers, and error contracts across 13 bounded contexts creates maintenance drift and
  inconsistent behaviour.
