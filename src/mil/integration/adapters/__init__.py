"""
LOS adapter implementations.

Each module in this package is a concrete LOSAdapter implementation for a
specific LOS platform. Adapters translate between the LOS platform's data
format and MIL's domain model. Each adapter is independently registered in
the DI container and selected by deployment configuration.

Implementations added here must pass the LOSAdapter conformance tests in
tests/providers/test_los_conformance.py before production registration.
"""
