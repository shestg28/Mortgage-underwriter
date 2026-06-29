"""
Platform lifecycle management for the MIL Platform.

``PlatformLifecycle`` coordinates application startup and shutdown:
configuring observability, building the dependency injection container,
and (in future sprints) establishing and draining infrastructure connections.

Intended usage in a FastAPI lifespan handler::

    from contextlib import asynccontextmanager
    from fastapi import FastAPI
    from mil.kernel.config import get_settings
    from mil.kernel.lifecycle import PlatformLifecycle

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings = get_settings()
        lifecycle = PlatformLifecycle(settings)
        container = lifecycle.startup()
        app.state.container = container
        yield
        lifecycle.shutdown()

    app = FastAPI(lifespan=lifespan)

Dependency rule: this module imports from ``mil.kernel.config``,
``mil.kernel.container``, and ``mil.kernel.observability`` only.
No bounded context code should be imported here.
"""

from __future__ import annotations

from mil.kernel.config import Settings, get_settings
from mil.kernel.container import Container, build_container
from mil.kernel.observability import configure_logging


class PlatformLifecycle:
    """
    Coordinates platform startup and shutdown for a single process.

    Call ``startup()`` once at process startup; call ``shutdown()`` once
    at process termination.  The returned ``Container`` from ``startup()``
    is the resolved DI registry for the lifetime of the process.

    ``PlatformLifecycle`` is intentionally not a context manager so it
    can be wired into both FastAPI lifespan and plain worker entry points
    without framework-specific coupling.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings: Settings = settings if settings is not None else get_settings()
        self._container: Container | None = None

    def startup(self) -> Container:
        """
        Initialise observability and build the DI container.

        Returns the assembled ``Container`` so the caller can store it on
        ``app.state`` (FastAPI) or pass it directly to worker processes.

        Calling ``startup()`` a second time replaces the existing container.
        """
        configure_logging(
            log_level=self._settings.mil_log_level,
            service_name=self._settings.otel_service_name,
        )
        self._container = build_container(self._settings)
        return self._container

    def shutdown(self) -> None:
        """
        Perform graceful shutdown.

        Sprint 2B: no persistent connections to close.
        Future sprints will drain the job queue and disconnect the event bus
        broker before returning.
        """

    @property
    def container(self) -> Container:
        """
        Return the active DI container.

        Raises:
            RuntimeError: If ``startup()`` has not been called yet.
        """
        if self._container is None:
            raise RuntimeError("Platform not started; call startup() first.")
        return self._container
