# Platform Kernel

The Kernel is the shared foundation imported by every bounded context in the MIL modular monolith. It is the **only** cross-cutting dependency permitted in this codebase.

## Dependency rule

```
mil.kernel  ←  mil.application
mil.kernel  ←  mil.document
mil.kernel  ←  mil.evidence
mil.kernel  ←  mil.finding
...
```

A bounded context **must not** import from another bounded context's internal modules (`models.py`, `repository.py`, etc.). Cross-context communication is through published `service.py` interfaces or domain events on the `EventBus`.

## Contents

| Module | Responsibility | Sprint |
|---|---|---|
| `db.py` | SQLAlchemy declarative base; constraint naming convention | 1 |
| `types.py` | Strongly-typed domain identifiers; value objects | 2 (T007) |
| `errors.py` | `DomainError` hierarchy; canonical error codes | 2 (T008) |
| `config.py` | Typed `Settings` schema; environment variable resolution | 2 (T009) |
| `events.py` | Canonical domain event type definitions | 2 (T010) |
| `event_bus.py` | `EventBus` abstract interface; in-process implementation | 2 (T011) |
| `job_queue.py` | `JobQueue` abstract interface; `Job` base type | 2 (T012) |
| `security.py` | `AuthenticatedUser` context; permission constants | 2 (T013) |
| `observability.py` | Structured log factory; trace helpers; metric emitter | 2 (T014) |
| `container.py` | Dependency injection wiring | 2 (T020) |
| `providers/` | Provider interface definitions (five interfaces) | 2 (T015–T019) |
