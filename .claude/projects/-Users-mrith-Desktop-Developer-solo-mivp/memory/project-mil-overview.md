---
name: project-mil-overview
description: Mortgage Intelligence Layer — product identity, LOS targets, and tooling context
metadata:
  type: project
---

**Mortgage Intelligence Layer (MIL)** is an enterprise software product: an API-first intelligence
layer for mortgage processing.

**Why:** Augments human underwriting decisions in regulated environments. Does not originate loans.

**How to apply:** When designing features, always frame MIL as the intelligence consumer, not
the LOS. Features must integrate with existing systems, not duplicate them.

LOS platforms MIL integrates with: Wipro NetOxygen, Encompass, Temenos, Finastra, nCino (and others).
Integration model: read-augment-return. MIL never writes decisions back to LOS autonomously.

Tooling: Spec Kit (`.specify/`) is used for feature specification, planning, and task generation.
Constitution: `.specify/memory/constitution.md` (v1.0.0). See [[project-mil-constitution]].
