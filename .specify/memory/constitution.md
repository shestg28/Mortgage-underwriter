<!--
SYNC IMPACT REPORT
==================
Version change: [template/unversioned] → 1.0.0
Bump rationale: MAJOR — initial population of all principles from template placeholders.
                This is the founding document for the Mortgage Intelligence Layer (MIL).

Modified principles:
  All 11 principles are new (template had 5 placeholder slots; expanded to 11).

Added sections:
  - Core Principles (I–XI, fully populated)
  - Domain Entities (reference table)
  - Integration Model
  - Governance

Removed sections:
  - [SECTION_2_NAME] / [SECTION_3_NAME] generic placeholders (replaced with domain-specific sections)

Templates reviewed:
  ✅ .specify/templates/plan-template.md
     — Constitution Check section references "constitution file" generically; remains valid.
     — No outdated principle references found.
  ✅ .specify/templates/spec-template.md
     — Key Entities section aligns with MIL domain entities defined in Principle VII.
     — No changes required.
  ✅ .specify/templates/tasks-template.md
     — Task structure is domain-agnostic; no constitution-specific references found.
     — No changes required.

Deferred TODOs:
  - None. Ratification date set to 2026-06-29 (today, as the founding date of this document).

---

Version change: 1.0.0 → 1.1.0
Bump rationale: MINOR — one new principle added (XII. Deterministic Intelligence); four existing
                principles materially expanded (II, V, VIII, Domain Entities); Purpose and
                Integration Model sections strengthened with governing identity statements.

Modified principles:
  II. Evidence First — expanded Evidence provenance requirements (7 mandatory attributes)
  V. Security and Privacy by Design — added Zero Trust, RBAC/ABAC, key management,
     AI context isolation, data residency awareness, least-data principle for AI prompts
  VIII. Auditability — expanded override requirements; lifecycle reconstruction mandate added
  Domain Entities — Policy added as ninth canonical entity

Added sections:
  - Principle XII. Deterministic Intelligence (new immutable principle)

Purpose: Added "Decision Assurance rather than Decision Automation" identity statement.
Integration Model: Clarified read → enrich → return; explicit no-autonomous-write guarantee.

Templates reviewed:
  ✅ .specify/templates/plan-template.md — no changes required
  ✅ .specify/templates/spec-template.md — no changes required
  ✅ .specify/templates/tasks-template.md — no changes required

Deferred TODOs:
  - None.
-->

# Mortgage Intelligence Layer (MIL) — Engineering Constitution

## Purpose

This document defines the permanent engineering philosophy of the Mortgage Intelligence Layer.
It governs how the platform is designed, built, extended, and evaluated.
These principles are immutable in intent. Amendments require the governance procedure defined below.

MIL is an API-first intelligence layer that augments human underwriting decisions in regulated
mortgage environments. It integrates with existing Loan Origination Systems — it does not replace them.

MIL provides Decision Assurance rather than Decision Automation.

---

## Core Principles

### I. Human Decision Authority

AI MUST NOT approve or reject mortgage applications.
AI MUST assist human decision makers by surfacing evidence, flagging anomalies, and presenting
structured findings. Every lending decision is the legal and ethical responsibility of a human
underwriter or authorised officer.

Rationale: Regulatory frameworks governing mortgage lending assign accountability to licensed
humans. Automated approval introduces legal liability and undermines consumer protection.

### II. Evidence First

Every conclusion the platform produces MUST be backed by traceable, source-linked evidence.
Documents are inputs; evidence is the primary product.

Every Evidence object MUST retain the following provenance attributes:

- **Source document** — the originating file or document reference
- **Page number** — the page on which the fact appears
- **Field location** — the specific field or region within the page, when available
- **Extraction confidence** — a quantified or qualified measure of extraction certainty
- **Extraction method** — the technique or component used to extract the fact
- **Timestamp** — when the extraction occurred
- **Originating model version** — the AI model version that produced the extraction

No Evidence object MUST be accepted into the platform without these attributes populated
to the extent they are derivable from the source.

Rationale: Without provenance, findings cannot be audited, disputed, or reproduced. Lending
decisions that cannot be evidenced expose lenders to regulatory and legal risk.

### III. Explainability by Default

Every AI output MUST answer, in terms a non-technical reviewer can interpret:

- **What** was found?
- **Why** was it found?
- **What evidence** supports it?
- **How confident** is the finding, and what are its limits?
- **What action** should the reviewer take?

Outputs that cannot satisfy all five questions MUST NOT be surfaced to end users.

Rationale: Explainability is not a feature — it is the primary interface between the platform
and the human decision maker. Opaque outputs erode trust and are incompatible with regulatory
expectations around fair lending.

### IV. Trust Before Automation

The objective of MIL is not maximum automation.
The objective is increasing confidence in human decisions through transparent, verifiable,
and reproducible intelligence.

Automation SHOULD be introduced only where it demonstrably reduces error, improves consistency,
or removes low-value repetition — and only after the underlying intelligence has been validated
by human reviewers. Confidence in the system MUST precede expansion of its autonomy.

Rationale: Premature automation in a regulated domain introduces compounding risk. Trust is
earned incrementally through verifiable accuracy, not asserted through feature releases.

### V. Security and Privacy by Design

Sensitive mortgage data MUST be protected by design, not by convention.
The platform MUST enforce the following controls:

- **Zero Trust architecture** — no actor, system, or network segment is trusted by default;
  every request MUST be authenticated, authorised, and validated regardless of origin
- **Least-privilege access** — every actor and service receives only the permissions required
  for its specific function, and no more
- **Role-Based Access Control (RBAC)** — access to platform resources MUST be governed by
  defined roles aligned to job function
- **Attribute-Based Access Control (ABAC)** — where RBAC alone is insufficient to express
  the required policy granularity, ABAC MUST be applied
- **Encryption in transit and at rest** — all data transmissions and stored data MUST be
  encrypted using current, vetted standards
- **Encryption key management** — cryptographic keys MUST be managed through dedicated,
  auditable key management practices; keys MUST NOT be embedded in source code or configuration
- **Secure secret management** — credentials, tokens, and secrets MUST be stored and
  rotated through dedicated secret management infrastructure
- **Secure AI context isolation** — data passed to AI models as context MUST be scoped to
  the minimum required; applicant data from different applications MUST NOT leak across
  AI inference boundaries
- **Data residency awareness** — the platform MUST support deployment configurations that
  respect data residency requirements; cross-jurisdiction data movement MUST be explicit
  and auditable
- **Least-data principle for AI prompts** — AI prompts MUST contain only the data attributes
  necessary to produce the required output; prompts MUST NOT carry surplus personal data
- **Data minimisation** — the platform MUST not collect or retain personal data beyond what
  is required for the stated processing purpose
- **Full auditability of data access** — all access to sensitive data MUST be logged

Security controls are product features. They MUST be designed, tested, and reviewed with
the same rigour as functional requirements. Security debt MUST NOT be deferred to post-launch.

Rationale: Mortgage applications contain among the most sensitive personal and financial data
a consumer can disclose. Breaches carry severe regulatory, reputational, and legal consequences.

### VI. API-First Integration

MIL is an Intelligence Layer, not a Loan Origination System.
Every capability MUST be consumable through well-defined, versioned APIs.
The platform MUST remain vendor-agnostic and integrate with existing LOS platforms
(including but not limited to Wipro NetOxygen, Encompass, Temenos, Finastra, and nCino)
without requiring changes to those systems.

MIL MUST NOT replicate or compete with LOS functionality. Its scope is intelligence, not origination.

Rationale: Replacing existing LOS platforms is not feasible, commercially or operationally.
The intelligence layer creates value only if it can be adopted without disrupting existing workflows.

### VII. Domain-Driven Design

Business entities drive the architecture. Technical implementation MUST reflect the mortgage domain.

Core entities:
- **Applicant** — the individual or organisation applying for a mortgage
- **Application** — a mortgage application submitted for review
- **Document** — a source document submitted as part of an application
- **Evidence** — a verified, provenance-bearing fact extracted from a document
- **Finding** — an AI-generated observation derived from one or more pieces of evidence
- **Verification** — a human or system confirmation of an evidence item or finding
- **Recommendation** — a structured suggestion for the human reviewer based on findings
- **Audit Event** — a timestamped, immutable record of every significant platform action
- **Policy** — a versioned collection of verification rules and business constraints governing
  how evidence is evaluated; versioned independently of AI models

Services, APIs, and data stores MUST be named and organised around these entities.
Technical abstractions that obscure domain meaning MUST be avoided.

Rationale: Alignment between the domain model and the codebase reduces cognitive overhead,
improves onboarding, and ensures that compliance teams can reason about the system directly.

### VIII. Auditability

Every significant action performed by the platform or by its users MUST be recorded as
an immutable Audit Event. This includes: AI recommendations, human overrides, document
ingestions, verification decisions, API calls that modify state, and configuration changes.

The audit history MUST be immutable — Audit Events MUST NOT be modified or deleted after
they are written. Any correction MUST be recorded as a new compensating event, not an edit.

Human overrides of AI findings MUST capture all of the following:

- **Reviewer identity** — the authenticated identity of the human actor
- **Override reason** — a mandatory, human-authored justification for the override
- **Previous value** — the original AI-generated finding or recommendation being overridden
- **New value** — the replacement value asserted by the reviewer
- **Timestamp** — when the override was recorded

Audit events MUST collectively support full reconstruction of the complete lifecycle of any
application — from initial submission through every state transition, finding, override, and
final disposition — without reliance on any data source outside the audit record.

AI recommendations MUST be reproducible — given the same inputs, the same recommendation
MUST be derivable. Audit data MUST be retained for a period consistent with regulatory
requirements and MUST be accessible to authorised auditors without requiring platform
support intervention.

Rationale: Regulators, internal audit teams, and legal counsel require a complete, tamper-evident
record of how lending decisions were reached. Auditability is a non-negotiable compliance requirement.

### IX. Incremental Evolution

The platform MUST prefer incremental improvements over complete rewrites.
Existing working functionality MUST only be replaced when there is clear architectural
justification, documented in writing, and validated against this constitution.

New capabilities MUST be additive where possible. Breaking changes to APIs or domain contracts
MUST be versioned and communicated with sufficient lead time for integrating systems to adapt.

Rationale: Complete rewrites introduce systemic risk, disrupt integrations, and erase
institutional knowledge embedded in working code. In a regulated domain, instability is costly.

### X. Operational Excellence

MIL MUST improve not only individual underwriting decisions but also the overall efficiency and
visibility of mortgage operations. The platform SHOULD provide analytics, bottleneck identification,
workload visibility, and operational insights that allow operations teams to improve at the
process level, not only the case level.

Observability — structured logging, tracing, and metrics — is a design requirement, not an
afterthought. The platform MUST be operable without requiring deep technical knowledge to diagnose
routine operational issues.

Rationale: Intelligence that improves individual cases but obscures systemic problems does not
deliver its full value. Mortgage operations are complex pipelines; platform-level visibility
enables continuous improvement.

### XI. Regulatory Alignment

MIL MUST be designed so that its outputs support regulatory compliance, internal audit,
and governance requirements across the jurisdictions in which it is deployed.

Features that reduce explainability, traceability, or accountability MUST NOT be introduced
into the core platform. Any capability that would make it harder to demonstrate fair lending,
data protection compliance, or decision accountability is architecturally incompatible with MIL.

Regulatory requirements SHOULD inform design decisions from the outset, not be retrofitted
as constraints after implementation.

Rationale: Mortgage lending is subject to fair lending law, consumer protection regulation,
and data privacy legislation. The cost of non-compliance — financial, legal, and reputational
— exceeds the cost of designing for compliance from the start.

### XII. Deterministic Intelligence

Given identical inputs, identical policy versions, and identical AI model versions, the platform
SHOULD produce reproducible evidence and findings.

Where outputs differ because of updated models, prompts, extraction engines, or policy packs,
those differences MUST be versioned, traceable, and explainable. No silent change to AI behaviour
is permissible in a production environment.

Every AI-generated finding MUST be attributable to the following versioned components:

- **Model Version** — the AI model that produced the output
- **Prompt Version** — the prompt template applied during inference
- **Policy Version** — the policy pack governing evaluation rules
- **Extraction Version** — the extraction engine or pipeline version
- **Timestamp** — when the finding was produced

This attribution MUST be recorded as part of the finding and retained in the audit record.

Rationale: Mortgage decisions operate within regulated environments where reproducibility is
essential for audit, legal review, customer disputes, and regulatory compliance. An AI system
whose behaviour cannot be attributed to a specific, known configuration cannot be defended
in an audit or dispute context.

---

## Domain Entities Reference

The following canonical entities govern naming across all services, APIs, and data stores.
Introducing a new core entity requires a constitution amendment.

| Entity | Responsibility |
|---|---|
| Applicant | Identity and profile of a mortgage applicant |
| Application | A mortgage application and its lifecycle state |
| Document | A source file submitted as part of an application |
| Evidence | A provenance-bearing fact extracted from a document |
| Finding | An AI-generated observation derived from evidence |
| Verification | Confirmation of an evidence item or finding |
| Recommendation | A structured suggestion for human reviewer action |
| Audit Event | An immutable record of a significant platform action |
| Policy | A versioned collection of verification rules, compliance requirements, and institution-specific business constraints that govern how evidence is evaluated |

Policies are versioned independently of AI models. A change to a Policy version MUST be treated
as a distinct configuration change and reflected in the versioning attributes of any findings
produced under that Policy. Policy versions MUST be retained to allow historical findings to be
re-evaluated or explained in their original policy context.

---

## Integration Model

MIL integrates with LOS platforms as an intelligence layer via its APIs.
The integration model is **read → enrich → return**: MIL reads data from the LOS, enriches it
with intelligence — evidence extraction, finding generation, and structured recommendations —
and returns those outputs to the calling system or user interface.

MIL MUST NOT perform autonomous write operations into a Loan Origination System.
Any state-changing operation that affects the application record within an LOS MUST be
initiated by an authenticated human user acting through the host system. MIL may prepare and
propose a state change; it MUST NOT execute one unilaterally.

---

## Governance

This constitution supersedes all other engineering guidance in this repository.
In the event of conflict between a feature specification, a plan document, or a team convention
and this constitution, this constitution prevails.

**Amendment procedure**:
1. Propose the amendment in writing, citing the principle(s) affected and the rationale.
2. Identify all downstream impacts (APIs, services, templates, dependent documents).
3. Obtain written approval from the technical lead and a domain authority (compliance or legal).
4. Update this document, increment the version according to the versioning policy below, and
   record the amendment in the Sync Impact Report comment at the top of this file.
5. Propagate changes to all dependent templates and documentation within the same change set.

**Versioning policy**:
- MAJOR: A principle is removed, materially redefined, or a new non-negotiable constraint is added.
- MINOR: A new principle or section is added, or guidance is materially expanded.
- PATCH: Clarifications, wording improvements, or non-semantic refinements.

**Compliance review**:
All feature specifications MUST include a Constitution Check section in their implementation plan,
confirming that no principle is violated. Any violation MUST be documented with justification
and approved before implementation proceeds.

---

**Version**: 1.1.0 | **Ratified**: 2026-06-29 | **Last Amended**: 2026-06-29
