"""
Operational Intelligence bounded context.

Provides aggregate operational visibility: queue state, SLA compliance,
turnaround analytics, reviewer workload distribution, and bottleneck indicators.
Operational data is produced by scheduled snapshots and is never application-
specific — it reflects aggregate platform state only.

Public interface: operational.service.OperationalService
"""
