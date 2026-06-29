"""
Evidence Management bounded context.

Owns the append-only evidence store, evidence relationships, and evidence
snapshots. Evidence items are immutable once written. Corrections use the
supersession pattern: a new evidence item referencing the superseded item via
`supersedes_id`. Evidence Snapshots are captured at finding generation time
to preserve reproducibility for audit.

Public interface: evidence.service.EvidenceService
"""
