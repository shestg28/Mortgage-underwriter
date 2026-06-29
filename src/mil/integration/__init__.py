"""
Integration Gateway bounded context.

Manages bidirectional communication with LOS platforms via the LOSAdapter
interface. Inbound: receives application and document data from LOS platforms.
Outbound: dispatches readiness status and finding summaries. The platform core
has no LOS-specific code — all LOS coupling is in the adapter layer.

Integration model: read → enrich → return. MIL must not autonomously write
application state back to any LOS.

Public interface: integration.webhook.WebhookHandler, integration.dispatcher.EventDispatcher
"""
