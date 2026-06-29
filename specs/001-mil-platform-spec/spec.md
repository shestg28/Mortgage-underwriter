# Feature Specification: Mortgage Intelligence Layer (MIL) — Foundational Product

**Feature Branch**: `001-mil-platform-spec`

**Created**: 2026-06-29

**Status**: Draft

---

## 1. Product Vision

### Why MIL Exists

Mortgage underwriting is one of the most document-intensive, high-stakes processes in financial
services. Lenders and underwriters must review dozens of documents per application — income
statements, bank statements, property valuations, identity documents, employment records, and
more — to build a picture of an applicant's creditworthiness and the risk of the proposed loan.

Today, this process is largely manual. Verification officers and underwriters read documents,
extract facts, cross-reference information, and construct judgements — all under time pressure,
regulatory scrutiny, and the constant risk of human error. Documents arrive in multiple formats,
from multiple sources, with varying quality. The burden of assembling evidence falls almost
entirely on individual reviewers.

The result is slow turnaround times, inconsistent verification quality, limited audit
traceability, and growing operational costs as mortgage volumes scale.

**MIL exists to transform mortgage documents into structured, traceable, explainable evidence
that equips human decision makers to review applications faster, with greater confidence, and
with a complete audit trail.**

### The Business Problem

- **Evidence assembly is slow**: Reviewers spend significant time extracting facts from documents
  that could be identified and structured automatically.
- **Verification is inconsistent**: Without structured evidence, the completeness and quality of
  review depends heavily on the individual reviewer.
- **Audit trails are fragile**: Manually assembled evidence is difficult to reproduce and defend
  in regulatory audit or customer dispute scenarios.
- **LOS platforms do not provide intelligence**: Existing Loan Origination Systems manage
  application lifecycle and workflow but do not interpret document content.
- **Decision quality is opaque**: When a lending decision is made, the evidence chain that
  supported it is often distributed across emails, notes, and scanned files — not structured
  or traceable.

### Long-Term Vision

MIL will become the intelligence foundation for mortgage lending operations — a trusted layer
that every lender, servicer, and mortgage BPO deploys alongside their existing LOS to ensure
that every underwriting decision is evidence-backed, explainable, and audit-ready.

Over time, MIL will expand from document intelligence and evidence assembly to operational
intelligence — giving mortgage operations teams visibility into workflow efficiency, bottlenecks,
reviewer performance, and portfolio risk patterns.

The long-term vision is a lending environment where every decision can be fully reconstructed,
every finding traced to its source, and every override justified — not because compliance
requires it, but because the platform makes it natural.

---

## 2. Product Positioning

### What MIL Is

MIL is an **API-first Mortgage Intelligence Layer**. It reads mortgage application data and
documents from existing systems, enriches that data with structured, provenance-bearing evidence
and findings, and returns those outputs to the requesting system or user interface.

MIL provides **Decision Assurance rather than Decision Automation**. Its purpose is to increase
reviewer confidence and reduce manual effort — not to replace the human underwriting process.

### What MIL Is Not

| MIL Is NOT | MIL IS |
|---|---|
| A Loan Origination System | An intelligence layer that integrates with LOS platforms |
| A replacement for existing LOS platforms | A complement that adds intelligence to existing workflows |
| A system that approves or rejects loans | A system that equips reviewers to make better-informed decisions |
| A KYC or identity verification system | A document intelligence and evidence management platform |
| A Credit Bureau or credit scoring system | An evidence assembly and cross-verification platform |
| A core banking system | A decision support layer for mortgage operations |

MIL integrates with Loan Origination Systems including, but not limited to, Wipro NetOxygen,
Encompass, Temenos, Finastra, and nCino. It does not require changes to those systems and does
not compete with their core functions.

---

## 3. Target Customers

MIL is designed for organisations that originate, service, or process mortgage applications at scale.

| Customer Segment | Description |
|---|---|
| **Banks** | Retail and commercial banks with mortgage origination operations |
| **Non-Banking Financial Companies (NBFCs)** | Specialist mortgage lenders operating outside traditional banking infrastructure |
| **Mortgage Lenders** | Dedicated mortgage lending organisations seeking to improve underwriting efficiency |
| **Mortgage Servicers** | Organisations managing the ongoing administration of existing mortgage portfolios |
| **Mortgage Business Process Outsourcers (BPOs)** | Third-party organisations processing mortgage applications on behalf of lenders |
| **LOS Vendors** | Loan Origination System providers seeking to add intelligence capabilities to their platforms |
| **Enterprise Mortgage Operations** | Large-scale mortgage processing operations within financial services groups |

---

## 4. Target Users

MIL serves a range of professionals involved in the mortgage application lifecycle.

| User Role | Primary MIL Interaction |
|---|---|
| **Relationship Manager** | Initiates application review; uses MIL to confirm document completeness before submission |
| **Verification Officer** | Reviews AI-extracted evidence against source documents; validates or overrides findings |
| **Credit Analyst** | Examines structured financial evidence to assess applicant creditworthiness |
| **Underwriter** | Reviews complete evidence packages and findings to form lending recommendations |
| **Risk Team** | Uses findings and verification outcomes to assess portfolio and application-level risk |
| **Compliance Team** | Reviews audit trails and evidence records to confirm regulatory alignment |
| **Audit Team** | Reconstructs application decision history; reviews human overrides and AI finding attribution |
| **Mortgage Operations Manager** | Monitors operational throughput, bottlenecks, and workload distribution across the team |

---

## 5. Core Product Capabilities

### Document Intelligence

MIL ingests mortgage documents in their native formats and extracts structured facts. Every
extracted fact retains its source document, page location, extraction confidence, and the
method by which it was identified. The platform handles diverse document types including
income statements, bank statements, property valuations, identity documents, employment records,
and legal instruments.

MIL supports native digital documents, scanned documents, image-based files, multi-page
documents, and mixed bundles containing documents of different types and quality levels within
a single submission. The platform processes each document without requiring the submitting party
to pre-classify or pre-convert files. Documents may be associated with specific Parties within
the application, enabling evidence to be attributed to the correct applicant, co-applicant,
guarantor, or corporate entity.

### Evidence Management

MIL organises extracted facts as structured Evidence objects — provenance-bearing, timestamped,
and attributed to a specific document, model version, and extraction method. Evidence objects
are the foundational unit of the platform. All findings, verifications, and recommendations
are anchored to evidence.

Evidence does not exist in isolation. MIL maintains explicit relationships between evidence items
and the findings they support. A single Finding may reference multiple evidence items drawn from
multiple documents. A single evidence item may support multiple findings. These relationships are
first-class records — not inferred at query time — so that the full evidence chain behind any
conclusion can be traversed and audited without reconstruction. When a Finding is generated, MIL
captures an immutable Evidence Snapshot — a point-in-time record of every evidence item referenced
at the moment the finding was produced. This snapshot preserves reproducibility: if the underlying
evidence is later corrected or superseded, the original basis for the finding remains intact and
auditable.

### Cross-Document Verification

MIL identifies consistencies and discrepancies across multiple documents within an application.
Income stated on an application form is compared against income evident in bank statements and
employment records. Property values are cross-referenced against valuation reports. Discrepancies
are surfaced as structured findings for reviewer attention.

### Finding Lifecycle

Findings move through a defined sequence of review states from the moment they are generated
to final resolution. The lifecycle ensures that no finding is left in an indeterminate state
and that the complete review history of each finding is preserved.

The standard Finding lifecycle is:

- **Extracted** — the finding has been generated by the platform and is awaiting reviewer attention
- **Needs Review** — the finding has been flagged as requiring human examination before it can progress
- **Verified** — a reviewer has confirmed the finding as accurate
- **Overridden** — a reviewer has replaced the finding with a corrected value, with a recorded reason
- **Escalated** — the finding has been referred to a senior officer or specialist team for resolution
- **Resolved** — the finding has reached a terminal state through verification, override, or escalation closure

Findings remain in the audit record at every lifecycle stage. State transitions are recorded as
Audit Events. No finding may move to a terminal state without an associated human action.

### Explainability

Every finding produced by MIL answers five questions: what was found, why it was found, what
evidence supports it, how confident the system is in the finding, and what action the reviewer
should consider. No finding is surfaced without a complete, human-readable explanation.

### Evidence Copilot

MIL provides an interactive evidence review capability that allows users to interrogate evidence,
ask questions about specific documents or findings, and request additional context — without
leaving the review workflow. The Evidence Copilot assists reviewers in navigating complex
applications and understanding the evidence basis for findings.

All Copilot responses are grounded in the evidence record for the application. The Copilot does
not speculate beyond the available evidence and clearly signals when information is absent or
unresolved. Representative interactions include:

- **"Explain this finding."** — The Copilot provides a plain-language explanation of what the
  finding means, why it was generated, and which evidence items support it.
- **"Why was this flagged?"** — The Copilot identifies the specific policy rule or discrepancy
  that caused the finding to be surfaced.
- **"Which evidence supports this conclusion?"** — The Copilot lists and links every evidence
  item referenced in the finding, with source document and page context.
- **"Which documents contradict this information?"** — The Copilot identifies evidence items
  from other documents that are inconsistent with a stated fact.
- **"Summarise this application."** — The Copilot produces a structured summary of verified
  evidence, outstanding findings, and current readiness status for the application.
- **"What evidence is still missing?"** — The Copilot identifies evidence gaps based on the
  active readiness checklist and policy requirements.
- **"What changed since the previous review?"** — The Copilot highlights new documents
  ingested, findings generated, and verifications recorded since a specified point in the
  application lifecycle.

### Operational Intelligence

MIL provides mortgage operations teams with visibility into application throughput, reviewer
workload, bottlenecks, and verification completion rates. Operational intelligence allows
managers to identify inefficiencies, balance workload, and improve process quality over time.

Operational Intelligence capabilities include:

- **SLA Monitoring** — tracking of applications and findings against defined service level
  agreement thresholds, with alerts when applications approach or breach SLA boundaries
- **Queue Ageing** — visibility into how long applications and individual findings have
  remained in each review state, identifying items at risk of delay
- **Turnaround Analytics** — measurement of end-to-end and stage-by-stage processing times,
  enabling identification of where time is gained or lost in the review lifecycle
- **Reviewer Productivity** — aggregate, non-invasive visibility into finding verification
  rates, override rates, and throughput per reviewer role, supporting performance management
  without individual surveillance
- **Workload Balancing** — tools to support equitable distribution of review queues across
  available reviewers, reducing concentration of work on individual officers
- **Operational Bottleneck Analysis** — identification of recurring delays, high-override
  document types, and policy rules that generate disproportionate rework, enabling targeted
  process improvement

### Policy Management

MIL separates verification intelligence from platform logic through configurable, versioned
Policy Packs. A Policy Pack is a structured collection of verification rules, compliance
requirements, and institution-specific business constraints that governs how evidence is
evaluated and which findings are generated. Verification logic is never hardcoded into the
platform — it is always expressed through a Policy Pack, which can be authored, versioned,
and deployed independently of platform releases.

Institutions configure Policy Packs to reflect their jurisdiction-specific regulatory
requirements, internal credit policies, and risk appetite. A lender operating across multiple
jurisdictions may maintain separate Policy Packs for each, applied selectively based on the
application context. Policy Packs are versioned independently of AI models — a policy change
and a model update are distinct events, each captured separately in the finding attribution record.

### Mortgage Readiness

MIL evaluates the completeness and quality of evidence assembled for an application before it
proceeds to the next stage of the lending process. Readiness assessments identify missing
documents, unresolved discrepancies, and incomplete verifications — reducing the rate of
applications returned for rework downstream.

### Trust and Governance

MIL maintains a complete, immutable audit record of every significant platform action, including
all AI findings, human verifications, reviewer overrides, and configuration changes. Every AI
finding is attributed to the model, prompt, policy, and extraction engine version that produced
it. Human overrides are recorded with the reviewer identity, the reason for the override, and
the previous and new values. The governance layer ensures that every lending decision supported
by MIL can be fully reconstructed and defended.

---

## 6. Core Business Workflows

### 6.1 LOS Integration Model: Read → Enrich → Return

MIL integrates with Loan Origination Systems using a three-phase interaction model:

1. **Read**: MIL receives application data and document references from the LOS. This may occur
   through event-driven notification, scheduled polling, or direct invocation by the LOS workflow.

2. **Enrich**: MIL processes the application — ingesting documents, extracting evidence,
   generating findings, and assembling a structured evidence package. This enrichment is
   performed asynchronously and does not block the LOS workflow.

3. **Return**: MIL returns structured findings, evidence summaries, verification statuses, and
   readiness assessments to the LOS or to a user interface. The enriched data is available for
   review through MIL's own interface or consumed by the LOS directly.

MIL does not write decisions into the LOS autonomously. Any state change in the LOS that
reflects a lending decision must be initiated by an authenticated human user acting through
the host system.

### 6.2 Document Ingestion Workflow

1. A new application or document is submitted to the LOS.
2. MIL is notified (or polled) and retrieves the document.
3. MIL ingests the document, extracts structured evidence, and records provenance attributes.
4. Extracted evidence is stored and associated with the application and originating document.
5. MIL evaluates extracted evidence against the active policy pack and generates findings.
6. Findings are made available to assigned reviewers.

### 6.3 Reviewer Workflow

1. A Verification Officer or Underwriter opens an application review in MIL.
2. MIL presents a structured evidence summary with associated findings.
3. The reviewer examines each finding, views the supporting evidence, and the source document
   context.
4. For each finding, the reviewer can:
   - **Verify**: Confirm the finding as accurate.
   - **Override**: Replace the finding with a corrected value, providing a mandatory reason.
   - **Escalate**: Flag the finding for review by a senior officer or risk team.
5. MIL records every verification and override as an Audit Event.
6. Once all findings are reviewed, MIL produces a verification summary and readiness assessment.
7. The reviewer or underwriter uses this evidence package to inform their lending recommendation.

### 6.4 Audit and Compliance Workflow

1. An auditor or compliance officer accesses the application audit trail.
2. MIL presents the complete lifecycle of the application — every document ingested, every
   finding generated, every verification and override recorded.
3. The auditor can reconstruct the state of evidence at any point in the review process.
4. AI finding attribution — model version, prompt version, policy version, extraction version,
   timestamp — is available for every finding.
5. Human override records — reviewer identity, reason, previous value, new value, timestamp —
   are fully accessible.

---

## 7. Functional Requirements

### Document Ingestion

- **FR-001**: The platform MUST accept mortgage documents in common document formats and extract
  structured evidence from their content.
- **FR-002**: Every extracted evidence item MUST retain provenance attributes: source document,
  page number, field location (where derivable), extraction confidence, extraction method,
  timestamp, and originating model version.
- **FR-003**: The platform MUST support ingestion of multiple documents per application.
- **FR-004**: The platform MUST handle documents of varying quality, including native digital
  documents, scanned documents, image-based files, multi-page documents, and mixed document
  bundles submitted in a single ingestion event.
- **FR-005**: Document ingestion MUST be non-destructive — source documents MUST be retained
  in their original form alongside extracted evidence.
- **FR-006**: Documents MUST be associable with a specific Party within the application —
  Applicant, Co-Applicant, Guarantor, or Corporate Entity — so that extracted evidence can be
  attributed to the correct party.

### Multi-Party Applications

- **FR-007**: The platform MUST support applications containing multiple Parties, including
  Applicants, Co-Applicants, Guarantors, and Corporate Entities.
- **FR-008**: Evidence MUST be attributable to the specific Party whose documents were the
  source of extraction.
- **FR-009**: Findings MUST be associable with one or more Parties, reflecting the scope of
  the finding within a multi-party application.

### Evidence Management

- **FR-010**: The platform MUST maintain a structured Evidence store associated with each
  application.
- **FR-011**: Evidence objects MUST be immutable after creation. Corrections MUST be recorded
  as new evidence items with a reference to the item being superseded.
- **FR-012**: The platform MUST support retrieval of evidence by application, document, Party,
  entity type, and confidence level.
- **FR-013**: Evidence MUST be associated with the Policy version under which it was evaluated.
- **FR-014**: The platform MUST maintain explicit, traversable relationships between evidence
  items and the Findings they support. A Finding may reference multiple evidence items; an
  evidence item may support multiple Findings.
- **FR-015**: When a Finding is generated, the platform MUST capture an immutable Evidence
  Snapshot — a point-in-time record of every evidence item referenced at the moment of generation.
  The Evidence Snapshot MUST be retained alongside the Finding for the full audit retention period.

### Findings and Verification

- **FR-016**: The platform MUST generate structured Findings from evidence, each answering:
  what was found, why, what evidence supports it, confidence level, and recommended reviewer action.
- **FR-017**: Every Finding MUST be attributed to model version, prompt version, policy version,
  extraction version, and timestamp.
- **FR-018**: The platform MUST support cross-document verification — identifying consistencies
  and discrepancies across evidence from multiple documents and multiple Parties.
- **FR-019**: Every Finding MUST progress through a defined lifecycle: Extracted → Needs Review
  → Verified / Overridden / Escalated → Resolved. State transitions MUST be recorded as Audit
  Events. No Finding may reach a terminal state without an associated human action.
- **FR-020**: Reviewers MUST be able to verify, override, or escalate each Finding.
- **FR-021**: Human overrides MUST capture reviewer identity, override reason, previous value,
  new value, and timestamp.
- **FR-022**: Overridden findings MUST remain in the audit record; they MUST NOT be deleted.

### Explainability

- **FR-023**: Every Finding surfaced to a user MUST include a human-readable explanation
  answering all five explainability questions.
- **FR-024**: The platform MUST provide access to the source evidence and originating document
  context for every Finding.
- **FR-025**: Confidence levels MUST be expressed in terms a non-technical reviewer can
  interpret.

### Evidence Copilot

- **FR-026**: The platform MUST provide an interactive capability that allows reviewers to query
  evidence and findings for a specific application using natural language.
- **FR-027**: Copilot responses MUST be grounded in the evidence record for the application and
  MUST reference specific evidence items in their answers.
- **FR-028**: The Copilot MUST NOT speculate beyond the available evidence record.
- **FR-029**: The Copilot MUST be capable of responding to the representative query types
  defined in the Evidence Copilot capability description, covering finding explanation,
  flagging rationale, evidence attribution, document contradictions, application summary,
  evidence gap identification, and change history.

### Mortgage Readiness

- **FR-030**: The platform MUST evaluate each application against a configurable readiness
  checklist before it advances to the next review stage.
- **FR-031**: Readiness assessments MUST identify missing documents, unresolved findings, and
  incomplete verifications, with awareness of the Parties present in the application.
- **FR-032**: Readiness status MUST be available to the LOS for workflow gating decisions
  (initiated by a human actor).

### Policy Management

- **FR-033**: The platform MUST support versioned Policy Packs that define verification rules,
  compliance requirements, and institution-specific business constraints.
- **FR-034**: Verification logic MUST be expressed entirely through Policy Packs and MUST NOT
  be hardcoded into platform behaviour. The platform MUST be capable of applying different
  Policy Packs to different applications without requiring a platform release.
- **FR-035**: Institutions MUST be able to configure distinct Policy Packs reflecting
  jurisdiction-specific regulatory requirements, internal credit policy, and risk parameters.
- **FR-036**: Policy versions MUST be retained permanently to allow historical findings to be
  re-evaluated or explained in their original policy context.
- **FR-037**: Changing the active Policy version MUST not retroactively alter existing findings;
  new findings MUST be generated under the new Policy version.
- **FR-038**: Policy version changes MUST be recorded as Audit Events, distinct from AI model
  version changes.

### Operational Intelligence

- **FR-039**: The platform MUST provide operational dashboards showing application throughput,
  reviewer workload, and bottleneck indicators.
- **FR-040**: The platform MUST report verification completion rates and outstanding review
  queues per reviewer and per team.
- **FR-041**: The platform MUST monitor applications and findings against defined SLA thresholds
  and surface alerts when items approach or breach those thresholds.
- **FR-042**: The platform MUST provide queue ageing visibility, showing how long applications
  and findings have remained in each lifecycle state.
- **FR-043**: The platform MUST provide turnaround analytics covering end-to-end and
  stage-by-stage processing times, enabling identification of where delays accumulate.
- **FR-044**: The platform MUST provide workload distribution visibility to support equitable
  assignment of review queues across available reviewers.
- **FR-045**: The platform MUST surface operational bottleneck indicators identifying document
  types, policy rules, or review stages that generate disproportionate rework or delay.
- **FR-046**: Operational data MUST be available in aggregate form to support management
  reporting without exposing applicant-level personal data unnecessarily.

### Audit and Governance

- **FR-047**: Every significant platform action MUST be recorded as an immutable Audit Event.
- **FR-048**: The audit record MUST support full reconstruction of the complete lifecycle of
  any application, including all Finding state transitions.
- **FR-049**: Audit data MUST be accessible to authorised auditors without requiring platform
  support intervention.
- **FR-050**: The platform MUST retain audit records for a period consistent with applicable
  regulatory requirements.

### Access and Identity

- **FR-051**: The platform MUST enforce Role-Based Access Control aligned to the user roles
  defined in this specification.
- **FR-052**: Every action that modifies platform state MUST be associated with an
  authenticated user identity.
- **FR-053**: The platform MUST support integration with enterprise identity providers.

---

## 8. Non-Functional Requirements

### Security

- The platform MUST enforce a Zero Trust security model — no actor or system is trusted by
  default regardless of network location.
- Access MUST be governed by Role-Based Access Control (RBAC) with Attribute-Based Access
  Control (ABAC) applied where RBAC granularity is insufficient.
- All data in transit and at rest MUST be encrypted using current, vetted standards.
- Cryptographic keys MUST be managed through dedicated, auditable key management practices.
- Credentials and secrets MUST be managed through dedicated secret management infrastructure
  and MUST NOT be embedded in source code or configuration files.
- AI inference contexts MUST be isolated — applicant data from one application MUST NOT be
  accessible within the inference context of another.

### Privacy

- The platform MUST collect and retain only the personal data attributes required for the
  stated processing purpose (data minimisation).
- AI prompts MUST contain only the data attributes required to produce the requested output
  (least-data principle).
- The platform MUST support deployment configurations that respect applicable data residency
  requirements.
- Personal data access MUST be logged and attributable to an authenticated identity.

### Explainability

- Every AI output MUST be accompanied by a human-readable explanation that answers: what was
  found, why, what evidence supports it, confidence level, and recommended action.
- Confidence levels MUST be communicated in plain language accessible to non-technical
  reviewers.
- The platform MUST not surface findings that cannot be explained to the applicable standard.

### Auditability

- All Audit Events MUST be immutable — they MUST NOT be modified or deleted after recording.
- The audit record MUST support reconstruction of the complete application lifecycle.
- Audit data MUST be retained in accordance with regulatory retention requirements.
- AI finding attribution MUST include model version, prompt version, policy version, extraction
  version, and timestamp.

### Performance

- Document ingestion and initial evidence extraction SHOULD complete within a timeframe that
  does not introduce material delay to the mortgage review workflow.
- Interactive reviewer workflows — finding review, evidence query, override recording — MUST
  be responsive to a degree that does not impair reviewer productivity.
- Operational intelligence dashboards MUST refresh at a frequency sufficient to support
  day-to-day workload management decisions.

### Availability

- The platform MUST be available during the operating hours of the institutions it serves.
- Planned maintenance MUST be schedulable outside of peak operating hours.
- The platform MUST degrade gracefully — if enrichment services are temporarily unavailable,
  the audit record and previously completed evidence MUST remain accessible.

### Reliability

- Evidence and audit records MUST be durable — once written, they MUST not be lost due to
  system failure.
- The platform MUST detect and report document ingestion failures rather than silently
  discarding documents.
- Partial failures MUST not corrupt the evidence record for an application.

### Scalability

- The platform MUST support concurrent processing of multiple applications without degradation
  in evidence quality or finding accuracy.
- The architecture MUST accommodate growth in application volumes, document types, and
  connected LOS integrations without requiring structural redesign.
- Operational intelligence capabilities MUST remain performant as the historical data volume grows.

### Regulatory Readiness

- Platform outputs — findings, evidence records, audit trails — MUST be structured to support
  regulatory examination, internal audit, and consumer dispute resolution.
- The platform MUST support deployment in jurisdictions with distinct data residency and
  privacy regulatory requirements.
- Policy packs MUST be configurable to reflect jurisdiction-specific and institution-specific
  compliance requirements.
- The platform MUST produce outputs that support fair lending demonstration and adverse action
  explanation obligations.

---

## 9. Success Metrics

The following outcomes define product success. All metrics are measurable without reference to
implementation technology.

| Metric | Description |
|---|---|
| **Reduced manual document review time** | Reviewers spend measurably less time extracting facts from documents manually |
| **Reduced underwriting turnaround time** | End-to-end application review time decreases for applications processed through MIL |
| **Increased evidence completeness** | Applications reaching underwriting stage have a higher proportion of required evidence items present and verified |
| **Improved audit readiness** | Audit preparation time for a sample application decreases; all required evidence and override records are available without manual reconstruction |
| **Reduced rework rate** | Fewer applications are returned from underwriting for missing or incomplete evidence |
| **Increased reviewer confidence** | Reviewers report greater confidence in the completeness and accuracy of the evidence available to them |
| **Reduced repetitive data entry** | Data extracted by MIL that would otherwise be entered manually by reviewers is measurably reduced |
| **Increased finding verification rate** | A higher proportion of AI-generated findings are confirmed as accurate by human reviewers over time |
| **Operational visibility** | Mortgage operations managers can identify and resolve bottlenecks using platform-provided data without manual reporting effort |
| **Human acceptance rate of findings** | The proportion of AI-generated findings accepted without override by reviewers, reflecting finding accuracy and trust |
| **Average evidence confidence** | The mean confidence level of evidence items across processed applications, reflecting extraction quality over time |
| **Explainability completeness** | The proportion of findings that satisfy all five explainability criteria without requiring reviewer escalation for clarification |
| **Average verification latency** | The average time between a finding entering Needs Review state and reaching a terminal state, reflecting reviewer workflow efficiency |
| **Evidence coverage** | The proportion of required evidence items present and attributed for a standard application at the point of underwriting review |
| **Evidence Copilot usefulness** | The proportion of Copilot queries that reviewers rate as useful or that result in a reviewer action, reflecting the quality of Copilot responses |

---

## 10. Explicit Non-Goals

MIL is scoped to decision assurance within the mortgage review lifecycle. The following are
explicitly outside its scope:

| Non-Goal | Rationale |
|---|---|
| **Replace Loan Origination Systems** | MIL complements LOS platforms; it does not manage application lifecycle or origination workflow |
| **Replace human underwriters** | MIL assists underwriters; all lending decisions remain the responsibility of human officers |
| **Approve or reject loan applications** | MIL MUST NOT make autonomous lending decisions |
| **Replace KYC systems** | Identity verification is the domain of dedicated KYC platforms; MIL may consume KYC outputs but does not perform identity verification |
| **Replace Credit Bureau systems** | Credit scoring and bureau data retrieval are outside MIL's scope |
| **Replace core banking systems** | MIL does not manage accounts, transactions, or banking infrastructure |
| **Perform collections or servicing actions** | Post-origination servicing actions are outside MIL's scope |

---

## 11. Product Principles

This specification aligns with the MIL Engineering Constitution (v1.1.0). The following
constitutional principles directly govern product decisions within this specification.

| Principle | Product Implication |
|---|---|
| **Human Decision Authority** | Every capability must equip, not replace, the human reviewer. No feature may be designed to make lending decisions autonomously. |
| **Evidence First** | Every product capability must produce, consume, or enrich structured, provenance-bearing evidence. Opinion without evidence is not a valid product output. |
| **Explainability by Default** | No finding or recommendation reaches a user without a complete, human-readable explanation. |
| **Trust Before Automation** | Automation is introduced incrementally and only after the underlying intelligence has been validated by human reviewers. |
| **Security by Design** | Security and privacy controls are product requirements, reviewed and validated with the same rigour as functional capabilities. |
| **API-First Integration** | Every capability is consumable through versioned APIs. MIL never requires changes to the LOS it integrates with. |
| **Auditability** | Every significant action is recorded immutably. The platform must be able to reconstruct the full lifecycle of any application at any time. |
| **Regulatory Alignment** | Product design must support, not hinder, the ability of lenders to demonstrate regulatory compliance. |

---

## Key Entities

| Entity | Description |
|---|---|
| **Party** | A participant in a mortgage application — one of: Applicant, Co-Applicant, Guarantor, or Corporate Entity. Applications may contain one or more Parties. |
| **Application** | A mortgage application and its complete lifecycle state, containing one or more Parties |
| **Document** | A source file submitted as part of an application, associated with a specific Party |
| **Evidence** | A provenance-bearing, structured fact extracted from a document, attributed to the Party whose document was the source |
| **Evidence Snapshot** | An immutable point-in-time capture of every evidence item referenced when a Finding was generated, preserved to support reproducibility and audit |
| **Finding** | An AI-generated observation derived from one or more evidence items, progressing through a defined lifecycle: Extracted → Needs Review → Verified / Overridden / Escalated → Resolved |
| **Verification** | A human or system confirmation or override of an evidence item or finding, recorded with reviewer identity, reason, and previous and new values |
| **Recommendation** | A structured suggestion for reviewer action based on findings |
| **Audit Event** | A timestamped, immutable record of every significant platform action, including Finding state transitions |
| **Policy** | A versioned collection of verification rules and compliance constraints governing evidence evaluation, configurable per institution and jurisdiction |

---

## 12. Extensibility

MIL is designed to support future intelligence modules without requiring architectural redesign.
The platform's separation of document intelligence, evidence management, policy evaluation, and
governance into distinct capabilities means that new intelligence domains can be introduced as
additional modules that consume the same evidence foundation.

Future intelligence modules that MIL is designed to accommodate include:

- **Fraud Intelligence** — detection of anomalies, fabricated documents, or inconsistencies
  that indicate potential misrepresentation or fraud, surfaced as findings with full evidence
  attribution
- **Regulatory Intelligence** — monitoring of regulatory change, mapping of updated requirements
  to existing policy packs, and identification of evidence gaps created by regulatory amendments
- **Portfolio Intelligence** — aggregate analysis of verified evidence and finding patterns
  across applications to identify portfolio-level trends, concentrations, and risk signals
- **AI Quality Monitoring** — ongoing measurement of finding acceptance rates, override
  patterns, and confidence calibration to surface degradation in AI output quality before it
  affects operational outcomes

Each future module integrates with MIL through its existing evidence and audit infrastructure.
No future module may introduce autonomous decision-making or bypass the human review lifecycle
defined in this specification.

---

## Assumptions

- Existing LOS platforms in scope are capable of exposing application data and documents
  through integration interfaces; specific integration mechanisms will be defined in
  feature-level specifications.
- The institutions deploying MIL retain responsibility for configuring Policy packs to reflect
  their jurisdiction-specific and institution-specific compliance requirements.
- User authentication and identity provisioning is managed by enterprise identity infrastructure;
  MIL integrates with existing identity providers rather than replacing them.
- The scope of document types initially supported will be defined in feature-level specifications
  based on the highest-volume document categories in target customer workflows.
- Data retention periods will be configured per-deployment to reflect applicable regulatory
  requirements in the jurisdiction of operation.
