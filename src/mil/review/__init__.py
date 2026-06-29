"""
Review & Verification bounded context.

Manages human review workflows: verification, override, escalation, and
resolution of findings. Every override record captures reviewer identity,
reason, previous value, and new value in the immutable audit trail. No finding
may reach a terminal state without an authenticated human action.

Public interface: review.service.ReviewService
"""
