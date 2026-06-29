"""
Identity & Access bounded context.

Manages authentication, role-based access control (RBAC), attribute-based
access control (ABAC), and identity provider integration. Enforces Zero Trust:
every inbound request is authenticated and authorised regardless of origin.
Cross-application data access is denied at the ABAC layer even for roles with
broad permissions.

Public interface: identity.rbac.require_permission, identity.abac.enforce_scope
"""
