"""
Finding Management bounded context.

Generates findings from policy evaluation output. Owns the finding lifecycle
state machine (EXTRACTED → NEEDS_REVIEW → VERIFIED/OVERRIDDEN/ESCALATED →
RESOLVED). Every finding carries five explainability fields (title, rationale,
evidence_summary, confidence_label, recommended_action) and four attribution
fields (model_version, prompt_version, policy_pack_id, extraction_version).
None of these fields may be absent or empty.

Public interface: finding.service.FindingService
"""
