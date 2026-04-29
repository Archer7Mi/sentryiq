-- SentryIQ Database Initialization
-- Optional: Run on PostgreSQL container startup
-- This file is automatically executed if mounted at /docker-entrypoint-initdb.d/init.sql

-- Create extensions (optional)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- All other tables are created by SQLAlchemy on application startup
-- via the alembic migration runner or direct ORM creation
