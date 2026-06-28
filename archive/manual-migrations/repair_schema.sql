-- repair_schema.sql
-- Add missing schema elements and create applications table for local loan_system DB.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Ensure customers has an id PK and audit fields.
ALTER TABLE customers
    ADD COLUMN IF NOT EXISTS id UUID DEFAULT gen_random_uuid();

UPDATE customers
SET id = gen_random_uuid()
WHERE id IS NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'customers'::regclass
          AND contype = 'p'
    ) THEN
        ALTER TABLE customers ADD PRIMARY KEY (id);
    END IF;
END$$;

ALTER TABLE customers
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();
ALTER TABLE customers
    ADD COLUMN IF NOT EXISTS date_of_birth DATE;

-- Create applications table.
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    risk_score INTEGER,
    decision VARCHAR(50),
    decision_reason TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_applications_customer_id ON applications(customer_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
