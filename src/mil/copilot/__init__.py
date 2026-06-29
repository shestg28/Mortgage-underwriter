"""
Evidence Copilot bounded context.

Provides an evidence-grounded natural language query interface for mortgage
reviewers. The Copilot constructs its context window from evidence items scoped
strictly to the queried application and the requesting user's permissions.
Evidence from other applications must never appear in a Copilot response.
Delegates inference to InferenceProvider. Every response includes citations.

Public interface: copilot.service.CopilotService
"""
