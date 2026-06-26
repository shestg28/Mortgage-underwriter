# Speckit Mortgage Underwriting Backend

## API Overview

This FastAPI backend supports:

- User registration and login with JWT authentication
- Customer CRUD
- PDF upload and document processing
- Application creation, scoring, and decision workflow
- Fraud flag generation and audit history

## Key Endpoints

### Auth
- `POST /api/auth/register`
  - Body: `{ "username": "...", "password": "...", "role": "loan_officer" }`
- `POST /api/auth/login`
  - Form data: `username`, `password`

### Customers
- `POST /api/customers/`
  - Body: `customer_id`, `full_name`, `date_of_birth`, `pan`, `aadhaar`, `salary`, `address`
- `GET /api/customers/`
- `GET /api/customers/lookup/{customer_id}`
- `PUT /api/customers/lookup/{customer_id}`
- `DELETE /api/customers/lookup/{customer_id}`

### Documents
- `POST /api/documents/upload`
  - Upload PDF file
- `POST /api/documents/process`
  - Query params: `file_id`, optional `customer_id`, optional `application_id`

### Applications
- `POST /api/applications/?customer_id={customer_id}`
- `POST /api/applications/{app_id}/score`
- `GET /api/applications/{app_id}`

### Fraud Flags
- `GET /api/fraud/flags/`
  - Query params: `application_id`, `customer_id`
- `GET /api/fraud/flags/{flag_id}`

## Loan Scoring and Decision Logic

The backend uses a rule-based scoring engine:

- salary <= 30k: high base risk
- salary <= 60k: medium base risk
- salary <= 100k: low base risk
- salary > 100k: no salary risk increment
- fraud severity adds risk points
- Aadhaar/PAN/name mismatch adds risk
- salary deviation above 20% adds risk

Decision rules:
- `risk_score < 30` → `approved`
- `30 <= risk_score < 60` → `review`
- `risk_score >= 60` → `rejected`

## Audit History

The backend stores audit records for:

- `application_created`
- `application_scored`

## Running Locally

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000/docs` for Swagger UI.

## Tests

Run the smoke test with:

```bash
cd backend
python test_api.py
```
