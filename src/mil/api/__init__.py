"""
HTTP API layer — FastAPI application and router registration.

All routes are versioned under /v1/. The middleware stack applies Zero Trust
authentication, audit context propagation, and OpenTelemetry tracing before
any business logic executes.

Route modules: api/v1/
Middleware: api/middleware/
"""
