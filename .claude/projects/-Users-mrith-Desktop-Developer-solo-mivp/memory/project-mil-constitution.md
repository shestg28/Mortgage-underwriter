---
name: project-mil-constitution
description: MIL Engineering Constitution — version history, principles summary, and governance rules
metadata:
  type: project
---

The MIL Engineering Constitution was ratified on 2026-06-29 at version 1.0.0.
It lives at `.specify/memory/constitution.md`.

**Why:** Establishes immutable engineering philosophy for a regulated financial intelligence platform.

**How to apply:** Every feature spec must include a Constitution Check in its plan.md. Any design
decision should be evaluated against the 11 principles before implementation.

The 11 principles (in order):
1. Human Decision Authority — AI never approves/rejects; humans are accountable
2. Evidence First — every conclusion is source-linked with provenance
3. Explainability by Default — every output answers what/why/evidence/confidence/action
4. Trust Before Automation — confidence precedes autonomy expansion
5. Security and Privacy by Design — least-privilege, encryption, auditability built in
6. API-First Integration — vendor-agnostic; integrates with LOS, never replaces them
7. Domain-Driven Design — canonical entities: Applicant, Application, Document, Evidence,
   Finding, Verification, Recommendation, Audit Event
8. Auditability — immutable Audit Events for all significant actions; AI output reproducible
9. Incremental Evolution — prefer additive changes; breaking changes must be versioned
10. Operational Excellence — analytics, bottleneck visibility, structured observability
11. Regulatory Alignment — outputs must support compliance, audit, governance by design

Amendment requires technical lead + compliance/legal sign-off and a version bump.
