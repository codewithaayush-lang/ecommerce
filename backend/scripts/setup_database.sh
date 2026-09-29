#!/usr/bin/env bash
#
# Create (or reuse) the local PostgreSQL role and database for this project.
#
# This script needs superuser access to PostgreSQL, so it must be run with
# sudo. It is idempotent: an existing role or database is reused rather than
# recreated.
#
# The role password is read from backend/.env so that it never has to appear
# in this file, in shell history, or in any commit.
#
# Usage:
#   sudo bash backend/scripts/setup_database.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$BACKEND_DIR/.env"

DB_NAME="ecommerce"
DB_USER="ecommerce"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "error: $ENV_FILE not found. Create it from .env.example first." >&2
    exit 1
fi

DB_PASSWORD="$(grep -E '^POSTGRES_PASSWORD=' "$ENV_FILE" | head -1 | cut -d= -f2-)"
if [[ -z "$DB_PASSWORD" ]]; then
    echo "error: POSTGRES_PASSWORD is not set in $ENV_FILE" >&2
    exit 1
fi

if [[ $EUID -ne 0 ]]; then
    echo "error: this script needs superuser access. Re-run with sudo." >&2
    exit 1
fi

echo "==> Ensuring PostgreSQL is running"
systemctl is-active --quiet postgresql || systemctl start postgresql

echo "==> Creating role '$DB_USER' if it does not exist"
# The password is passed as a psql variable rather than interpolated into the
# SQL text, so it is never written to a file. It does briefly appear in this
# process's own argv, which is acceptable for local development.
sudo -u postgres psql --no-psqlrc --set=ON_ERROR_STOP=1 \
    --set=db_user="$DB_USER" --set=db_password="$DB_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'db_user', :'db_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'db_user')
\gexec

-- Keep the stored password in sync with .env if the role already existed.
SELECT format('ALTER ROLE %I LOGIN PASSWORD %L', :'db_user', :'db_password')
WHERE EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'db_user')
\gexec
SQL

echo "==> Creating database '$DB_NAME' if it does not exist"
sudo -u postgres psql --no-psqlrc --set=ON_ERROR_STOP=1 \
    --set=db_name="$DB_NAME" --set=db_user="$DB_USER" <<'SQL'
SELECT format('CREATE DATABASE %I OWNER %I', :'db_name', :'db_user')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'db_name')
\gexec

-- Runs unconditionally so ownership is correct even if the database existed.
SELECT format('ALTER DATABASE %I OWNER TO %I', :'db_name', :'db_user') \gexec
SELECT format('GRANT ALL PRIVILEGES ON DATABASE %I TO %I', :'db_name', :'db_user') \gexec
SQL

echo "==> Result"
sudo -u postgres psql --no-psqlrc --set=ON_ERROR_STOP=1 \
    --set=db_name="$DB_NAME" <<'SQL'
SELECT r.rolname AS role,
       r.rolcanlogin AS can_login,
       d.datname AS database,
       pg_get_userbyid(d.datdba) AS owner
FROM pg_roles r
LEFT JOIN pg_database d ON d.datname = 'ecommerce'
WHERE r.rolname = 'ecommerce';
SQL

echo "==> Done. Password value is never printed."
