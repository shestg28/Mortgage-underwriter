"""
API v1 route modules.

Each module in this package owns the HTTP endpoints for one bounded context.
Route modules must not contain business logic — they delegate to bounded
context services and serialise responses. All response schemas are validated
against the OpenAPI contracts in specs/001-mil-platform-spec/contracts/.
"""
