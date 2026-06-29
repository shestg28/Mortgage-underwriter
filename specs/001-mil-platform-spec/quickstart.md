# Quickstart Validation Guide: Mortgage Intelligence Layer (MIL)

**Phase 1 Output** | **Branch**: `001-mil-platform-spec` | **Date**: 2026-06-29

This guide documents the validation scenarios that confirm MIL is working end-to-end.
Run these scenarios after deployment to verify the platform before reviewer access is granted.

---

## Prerequisites

- MIL API service running and reachable
- Background worker (document pipeline) running
- Database migrations applied
- At least one Policy Pack loaded and activated
- Reviewer user account created with VERIFICATION_OFFICER role

---

## Scenario 1: Application and Party Setup

**Validates**: Application creation, multi-party support, Audit Event generation

1. Create an application with `POST /v1/applications`
   - Provide a `los_reference` value
   - Expect HTTP 201; record `application_id`

2. Add an Applicant party with `POST /v1/applications/{application_id}/parties`
   - Use `party_type: APPLICANT`
   - Expect HTTP 201; record `party_id`

3. Add a Co-Applicant party with `POST /v1/applications/{application_id}/parties`
   - Use `party_type: CO_APPLICANT`
   - Expect HTTP 201

4. Verify the Audit Log with `GET /v1/audit/applications/{application_id}`
   - Expect `APPLICATION_CREATED` and two `PARTY_ADDED` events in chronological order
   - Verify `sequence_number` values are consecutive with no gaps

**Pass criteria**: Application has two parties; three Audit Events recorded with consecutive sequence numbers.

---

## Scenario 2: Document Ingestion and Evidence Extraction

**Validates**: Document upload, extraction pipeline, provenance attributes (all seven), Evidence Store

1. Upload a test income statement document via the Documents API, associated with the Applicant party
   - Expect HTTP 201; record `document_id`
   - Wait for `ingestion_status` to reach COMPLETED (poll `GET /v1/applications/{application_id}/documents/{document_id}`)

2. Retrieve Evidence for the application with `GET /v1/applications/{application_id}/evidence`
   - Expect at least one Evidence item of type `MONTHLY_INCOME`

3. For each Evidence item returned, confirm all seven provenance attributes are present and non-null:
   - `document_id` (source document)
   - `page_number`
   - `field_location` (may be null only if not derivable from the document format)
   - `extraction_confidence` (must be in range 0.0–1.0)
   - `extraction_method`
   - `extraction_model_version`
   - `extracted_at`

4. Verify Audit Log includes:
   - `DOCUMENT_UPLOADED`
   - `DOCUMENT_INGESTION_STARTED`
   - `DOCUMENT_INGESTION_COMPLETED`
   - `EVIDENCE_CREATED` (one per extracted evidence item)

**Pass criteria**: At least one Evidence item with all seven provenance attributes populated; four Audit Event types recorded.

---

## Scenario 3: Finding Generation and Lifecycle

**Validates**: Finding generation, all five explainability fields, all four attribution fields, Evidence Snapshot, lifecycle state machine

1. Using the application from Scenario 2, upload a second document (e.g., a bank statement for the same Applicant)
   - Wait for ingestion to complete

2. Retrieve Findings with `GET /v1/applications/{application_id}/findings`
   - Expect at least one Finding in EXTRACTED or NEEDS_REVIEW state

3. Retrieve the Finding detail with `GET /v1/applications/{application_id}/findings/{finding_id}`

4. Verify all five explainability fields are present and non-empty:
   - `title`
   - `rationale`
   - `evidence_summary`
   - `confidence_label`
   - `recommended_action`

5. Verify all four attribution fields are present and non-empty:
   - `model_version`
   - `prompt_version`
   - `policy_pack_id`
   - `extraction_version`

6. Verify the `evidence_snapshot` array contains at least one item referencing the correct `document_id`

7. Verify Audit Log includes:
   - `EVIDENCE_SNAPSHOT_CREATED`
   - `FINDING_GENERATED`

**Pass criteria**: At least one Finding with all five explainability fields, all four attribution fields, and a non-empty evidence snapshot.

---

## Scenario 4: Human Verification and Override

**Validates**: Human review lifecycle, override record completeness, Audit Event on state transition

1. Using the Finding from Scenario 3, submit an override with `POST /v1/applications/{application_id}/findings/{finding_id}/override`
   - Provide `new_value` and `reason` (minimum 10 characters)
   - Expect HTTP 200

2. Retrieve the Finding — verify `lifecycle_state` is now OVERRIDDEN

3. Verify the `verification_history` array in the Finding detail includes one record with:
   - `action: OVERRIDE`
   - `reviewer_id` matching the authenticated user
   - `previous_state: NEEDS_REVIEW` (or EXTRACTED)
   - `new_state: OVERRIDDEN`
   - `previous_value` populated
   - `new_value` populated
   - `reason` populated

4. Attempt to verify the same Finding with `POST /v1/applications/{application_id}/findings/{finding_id}/verify`
   - Expect HTTP 409 — terminal state cannot transition

5. Verify Audit Log includes:
   - `OVERRIDE_RECORDED`
   - `FINDING_STATE_CHANGED` with `new_state: OVERRIDDEN`

**Pass criteria**: Finding in OVERRIDDEN state; override record captures all required fields; terminal state transition rejected; two Audit Events recorded.

---

## Scenario 5: Audit Immutability

**Validates**: Audit records cannot be modified or deleted (Principle VIII)

1. Record the `sequence_number` of the most recent Audit Event for the test application

2. Attempt to delete an Audit Event directly — this should be rejected at the database
   permission level (no DELETE granted to the application user)
   - Verify the event still exists with `GET /v1/audit/events/{event_id}`

3. Retrieve the full lifecycle with `GET /v1/audit/applications/{application_id}/lifecycle`
   - Verify `sequence_number` values are consecutive with no gaps
   - Verify the `summary` totals match the counts from prior scenarios

**Pass criteria**: All Audit Events present and unchanged; sequence numbers consecutive.

---

## Scenario 6: Evidence Copilot

**Validates**: Evidence-grounded response, citation requirement, application scope isolation

1. Submit a Copilot query with `POST /v1/applications/{application_id}/copilot/query`
   - Query: `"Summarise this application's income evidence"`
   - Expect HTTP 200

2. Verify the response:
   - `response_text` is non-empty
   - `citations` array is non-empty
   - Each citation references an `evidence_item_id` that belongs to this application
   - `is_evidence_grounded` is `true`

3. Submit a Copilot query using a *different* application's `application_id` in the URL
   but referencing evidence from the first application in the query text
   - Verify the response does not reference evidence items from the other application
   - Verify `evidence_scope_count` reflects only the second application's evidence

**Pass criteria**: Copilot response is grounded with citations; evidence scope is isolated per application.

---

## Scenario 7: Mortgage Readiness

**Validates**: Readiness assessment identifies gaps before underwriting

1. Retrieve readiness with `GET /v1/applications/{application_id}/readiness`
   - If the application has unresolved findings, `is_ready` must be `false`
   - `unresolved_finding_count` must match the count of non-terminal findings

2. Resolve all findings (verify or override each)

3. Retrieve readiness again
   - If no missing documents and no unresolved findings, `is_ready` should be `true`
   - `missing_items` array should be empty

**Pass criteria**: Readiness reflects current evidence and finding state accurately.

---

## Scenario 8: Operational Intelligence

**Validates**: Operational dashboard, queue ageing, SLA monitoring

1. Retrieve the dashboard with `GET /v1/operational/dashboard`
   - Verify `findings_pending_review` reflects the actual count of non-terminal findings
   - Verify `snapshot_at` is within the last 5 minutes

2. Retrieve queue ageing with `GET /v1/operational/queues`
   - Verify at least one state entry is present
   - Verify `oldest_age_minutes` is a non-negative integer

**Pass criteria**: Dashboard data is fresh (within 5 minutes) and reflects actual application state.

---

## Failure Modes to Verify

| Scenario | Expected Behaviour |
|---|---|
| Upload a corrupt or unreadable document | `ingestion_status` reaches FAILED; `DOCUMENT_INGESTION_FAILED` Audit Event recorded; no Evidence items created |
| Submit an override without a reason field | HTTP 400 Validation Error; Finding state unchanged |
| Attempt to access another tenant's application | HTTP 403 Forbidden |
| Query the Copilot without authentication | HTTP 401 Unauthorized |
| Attempt to transition a terminal Finding to another state | HTTP 409 Conflict |
