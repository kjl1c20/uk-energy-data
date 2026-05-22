BEGIN;

CREATE USER readonly WITH PASSWORD :'readonly_password';

GRANT CONNECT ON DATABASE postgres TO readonly;
GRANT USAGE ON SCHEMA public TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;

-- Covers tables created after this script runs.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO readonly;

COMMIT;
