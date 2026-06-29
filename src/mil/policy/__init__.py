"""
Policy Engine bounded context.

Loads and versions Policy Packs (YAML configuration). Evaluates evidence items
against the active Policy Pack to produce triggered rule identifiers. Policy
rules are never hardcoded — all verification logic is configuration. Policy
Pack versions are retained for historical finding explanation.

Public interface: policy.engine.PolicyEngine
"""
