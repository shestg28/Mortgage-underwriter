"""
Intelligence Orchestrator — document processing pipeline coordination.

Owns workflow sequencing, step dispatch, retry handling, and workflow state.
Does NOT own Evidence, Finding, or any business logic. Treats each pipeline
step as a black box: it knows inputs, outputs, and success/failure signals.

Public interface: orchestrator.service.OrchestratorService
"""
