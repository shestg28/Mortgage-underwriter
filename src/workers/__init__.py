"""
Background worker process entry points.

Workers are thin processes that consume jobs from the JobQueue and delegate
execution to the appropriate bounded context service. All business logic remains
in the domain — workers are responsible only for job pickup, execution dispatch,
and result reporting to the Intelligence Orchestrator.

Workers are stateless. Multiple replicas of each worker may run concurrently.
Job deduplication and idempotency are enforced at the JobQueue level.

Worker processes:
  document_pipeline.py     — OCR and extraction pipeline jobs
  finding_generation.py    — Policy evaluation and finding generation jobs
  operational_snapshots.py — Scheduled operational intelligence snapshots
"""
