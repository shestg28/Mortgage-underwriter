"""
Platform Kernel — shared foundation for all MIL bounded contexts.

The Kernel is the only cross-cutting dependency permitted in this codebase.
Every bounded context imports from `mil.kernel`. No bounded context may import
from another bounded context's internal modules (models, repositories, etc.).
Inter-context communication is through published `service.py` interfaces only.

Kernel responsibilities:
  - Typed domain identifiers and value objects     (types.py)
  - Canonical error hierarchy and error contracts  (errors.py)
  - Typed settings schema and environment loading  (config.py)
  - Canonical domain event type definitions        (events.py)
  - EventBus abstract interface                    (event_bus.py)
  - JobQueue abstract interface and Job base type  (job_queue.py)
  - AuthenticatedUser context and RBAC hooks       (security.py)
  - Structured log factory and observability       (observability.py)
  - SQLAlchemy declarative base                    (db.py)
  - Dependency injection container                 (container.py)
  - Provider interface definitions                 (providers/)
"""
