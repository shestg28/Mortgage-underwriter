"""
Dependency injection container for the MIL Platform.

The ``Container`` class is a lightweight service registry.  It supports
singleton and transient lifetimes and is the single point where concrete
provider implementations are bound to their abstract interfaces.

The platform has no compile-time dependency on any concrete implementation.
All providers (OCR, extraction, inference, storage, LOS adapter) are
registered here at application startup, after reading the deployment
configuration.  Bounded context code resolves them via
``container.resolve(InterfaceType)`` rather than importing concrete classes.

Usage::

    from mil.kernel.config import get_settings
    from mil.kernel.container import build_container

    container = build_container(get_settings())
    emitter = container.resolve(MetricEmitter)

Dependency rule: this module imports from ``mil.kernel.errors``,
``mil.kernel.config``, and ``mil.kernel.observability`` only.
No bounded context code should be imported here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, cast

if TYPE_CHECKING:
    from collections.abc import Callable

from mil.kernel.config import Settings
from mil.kernel.errors import DependencyNotRegisteredError
from mil.kernel.observability import MetricEmitter, NoOpMetricEmitter

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Internal binding record
# ---------------------------------------------------------------------------


class _Binding:
    """
    Internal record for a single registered dependency.

    Tracks whether the binding is singleton (instantiated once) or transient
    (factory called on each ``resolve``).  Singletons cache their instance
    after the first call to ``resolve``.
    """

    __slots__ = ("_factory", "_instance", "_resolved", "_singleton")

    def __init__(self, factory: Callable[[], Any], singleton: bool) -> None:
        self._factory = factory
        self._singleton = singleton
        self._instance: Any = None
        self._resolved = False

    def resolve(self) -> Any:
        if self._singleton:
            if not self._resolved:
                self._instance = self._factory()
                self._resolved = True
            return self._instance
        return self._factory()


# ---------------------------------------------------------------------------
# Container
# ---------------------------------------------------------------------------


class Container:
    """
    Lightweight dependency injection container.

    Bindings are registered by interface type and resolved on demand.  The
    container is assembled once at application startup by ``build_container``
    and then treated as immutable for the lifetime of the process.

    Binding lifetimes:

    - **Singleton** (``register_singleton``, ``register_instance``): the factory
      is called at most once; subsequent ``resolve`` calls return the cached
      instance.  Use for stateful infrastructure objects (database sessions,
      provider clients).

    - **Transient** (``register_transient``): the factory is called on every
      ``resolve``.  Use for lightweight, stateless service objects.
    """

    def __init__(self) -> None:
        self._bindings: dict[type[Any], _Binding] = {}

    # ---- Registration methods ----------------------------------------------

    def register_singleton(self, interface: type[T], factory: Callable[[], T]) -> None:
        """
        Register a singleton binding.

        The ``factory`` is called the first time ``resolve(interface)`` is
        called; the result is cached and returned on all subsequent calls.
        """
        self._bindings[interface] = _Binding(factory, singleton=True)

    def register_instance(self, interface: type[T], instance: T) -> None:
        """
        Register a pre-constructed instance as a singleton.

        Equivalent to ``register_singleton`` with a factory that returns the
        supplied ``instance``.
        """
        binding = _Binding(lambda: instance, singleton=True)
        binding._instance = instance
        binding._resolved = True
        self._bindings[interface] = binding

    def register_transient(self, interface: type[T], factory: Callable[[], T]) -> None:
        """
        Register a transient binding.

        The ``factory`` is called on every ``resolve(interface)`` call.
        """
        self._bindings[interface] = _Binding(factory, singleton=False)

    # ---- Resolution --------------------------------------------------------

    def resolve(self, interface: type[T]) -> T:
        """
        Resolve a registered dependency.

        Raises:
            DependencyNotRegisteredError: If no binding exists for ``interface``.
        """
        if interface not in self._bindings:
            raise DependencyNotRegisteredError(interface)
        return cast("T", self._bindings[interface].resolve())

    def is_registered(self, interface: type[Any]) -> bool:
        """Return ``True`` if a binding exists for ``interface``."""
        return interface in self._bindings

    def registered_interfaces(self) -> list[type[Any]]:
        """Return all currently registered interface types."""
        return list(self._bindings.keys())


# ---------------------------------------------------------------------------
# Application container factory
# ---------------------------------------------------------------------------


def build_container(settings: Settings) -> Container:
    """
    Assemble and return the platform dependency injection container.

    This function is called once at application startup (in the FastAPI
    ``lifespan`` handler).  As bounded contexts and provider implementations
    are added, their registrations are appended here.

    Provider registrations are added in later sprints when their interfaces
    and concrete implementations exist:

    .. code-block:: python

        # Sprint 3+ — provider interface registrations:
        # container.register_singleton(StorageProvider, lambda: S3StorageProvider(settings))
        # container.register_singleton(OCRProvider, ...)
        # container.register_singleton(ExtractionProvider, ...)
        # container.register_singleton(InferenceProvider, ...)
        # container.register_singleton(LOSAdapter, ...)
    """
    container = Container()

    # Platform settings are always available as a singleton.
    container.register_instance(Settings, settings)

    # Metric emitter — defaults to no-op in development; replaced by a
    # concrete OTel-backed implementation in staging and production.
    container.register_instance(MetricEmitter, NoOpMetricEmitter())  # type: ignore[type-abstract]

    return container
