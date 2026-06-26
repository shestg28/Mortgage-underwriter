-- init.sql: runs on first container start
-- Create extensions and a sample schema
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- optional: create a speckit schema
CREATE SCHEMA IF NOT EXISTS speckit;
