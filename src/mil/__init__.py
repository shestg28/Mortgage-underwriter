"""
Mortgage Intelligence Layer (MIL) — Platform Core.

This is the root package for the MIL modular monolith. All bounded contexts
are sub-packages of this package. The only permitted cross-cutting import is
from `mil.kernel`, which provides shared primitives for the entire platform.

Architecture: see specs/001-mil-platform-spec/plan.md
Constitution: see .specify/memory/constitution.md
"""
