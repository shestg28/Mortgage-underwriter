"""
Request middleware — applied to every inbound request before route handlers.

Middleware execution order (outermost to innermost):
  1. telemetry.py     — OpenTelemetry trace context initialisation
  2. auth.py          — Zero Trust authentication; populates AuthenticatedUser
  3. audit_context.py — Propagates request_id, user_id, application_id for audit events
"""
