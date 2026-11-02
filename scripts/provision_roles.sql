-- ============================================================================
-- PostgreSQL Administrator Provisioning Script
-- Target: PostgreSQL 18.6 (Port 5433)
-- Database: agent_orchestrator
-- Execute as: postgres (Superuser)
-- ============================================================================

\c agent_orchestrator postgres

-- 1. Create or configure the dedicated migration group role (NOLOGIN, NOINHERIT)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'agent_orchestrator_migrator') THEN
        CREATE ROLE agent_orchestrator_migrator WITH NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE;
        RAISE NOTICE 'Role agent_orchestrator_migrator created.';
    ELSE
        ALTER ROLE agent_orchestrator_migrator WITH NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE;
        RAISE NOTICE 'Role agent_orchestrator_migrator security attributes updated.';
    END IF;
END
$$;

-- 2. Create or configure the dedicated migration login role (LOGIN, INHERIT)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'agent_orchestrator_migrator_user') THEN
        CREATE ROLE agent_orchestrator_migrator_user WITH LOGIN INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE;
        RAISE NOTICE 'Role agent_orchestrator_migrator_user created.';
    ELSE
        ALTER ROLE agent_orchestrator_migrator_user WITH LOGIN INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE;
        RAISE NOTICE 'Role agent_orchestrator_migrator_user security attributes updated.';
    END IF;
END
$$;

-- Ensure membership is explicitly granted so agent_orchestrator_migrator_user inherits migration group privileges
GRANT agent_orchestrator_migrator TO agent_orchestrator_migrator_user;

-- 3. Grant schema creation and DDL execution privileges to the migration group
GRANT CONNECT ON DATABASE agent_orchestrator TO agent_orchestrator_migrator;
GRANT USAGE, CREATE ON SCHEMA public TO agent_orchestrator_migrator;

-- Grant permissions on any existing tables and sequences in public schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public
TO agent_orchestrator_migrator;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public
TO agent_orchestrator_migrator;

-- 4. Transfer ownership of existing alembic_version table to migration user (if it exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_tables WHERE schemaname = 'public' AND tablename = 'alembic_version') THEN
        EXECUTE 'ALTER TABLE public.alembic_version OWNER TO agent_orchestrator_migrator_user';
        RAISE NOTICE 'Ownership of public.alembic_version transferred to agent_orchestrator_migrator_user.';
    END IF;
END
$$;

-- 5. Configure default privileges for future objects created by agent_orchestrator_migrator_user
-- Grants runtime DML access to agent_orchestrator_user while preserving object ownership with the creator
ALTER DEFAULT PRIVILEGES FOR ROLE agent_orchestrator_migrator_user IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO agent_orchestrator_user;

ALTER DEFAULT PRIVILEGES FOR ROLE agent_orchestrator_migrator_user IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO agent_orchestrator_user;

-- 6. Ensure runtime application role has connect and schema usage privileges only
GRANT CONNECT ON DATABASE agent_orchestrator TO agent_orchestrator_user;
GRANT USAGE ON SCHEMA public TO agent_orchestrator_user;

-- 7. Strictly enforce separation: ensure application role has NO migration role membership
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM pg_catalog.pg_auth_members am
        JOIN pg_catalog.pg_roles r ON r.oid = am.roleid
        JOIN pg_catalog.pg_roles m ON m.oid = am.member
        WHERE r.rolname = 'agent_orchestrator_migrator' 
          AND m.rolname = 'agent_orchestrator_user'
    ) THEN
        EXECUTE 'REVOKE agent_orchestrator_migrator FROM agent_orchestrator_user';
        RAISE NOTICE 'Revoked agent_orchestrator_migrator from agent_orchestrator_user.';
    ELSE
        RAISE NOTICE 'Role agent_orchestrator_user is not a member of agent_orchestrator_migrator (verified).';
    END IF;
END
$$;
