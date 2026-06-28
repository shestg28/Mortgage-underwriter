-- fix_customers_pk_and_create_applications.sql
-- Convert customers to use an UUID primary key and create applications table.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

ALTER TABLE customers
    ADD COLUMN IF NOT EXISTS id UUID;

UPDATE customers
SET id = gen_random_uuid()
WHERE id IS NULL;

ALTER TABLE customers
    ALTER COLUMN id SET NOT NULL;

ALTER TABLE customers
    DROP CONSTRAINT IF EXISTS customers_pkey;

ALTER TABLE customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_customer_id ON customers(customer_id);

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
