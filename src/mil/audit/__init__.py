"""
Audit & Governance bounded context.

Owns the append-only audit event log. The `audit.audit_events` table is
INSERT-only at the database permission level — no UPDATE or DELETE is granted
to the application database user. Sequence numbers are monotonically increasing
for tamper detection. All significant platform and user actions emit an audit
event. The full application lifecycle must be reconstructable from this log.

Public interface: audit.writer.AuditWriter (write), audit.repository.AuditRepository (read)
"""
