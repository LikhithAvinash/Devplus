#!/bin/bash
set -euo pipefail

PGDATA=${PGDATA:-/var/lib/postgresql/data}
POSTGRES_USER=${POSTGRES_USER:-agg_user}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-agg_pass}
POSTGRES_DB=${POSTGRES_DB:-agg_db}
UVICORN_PID=0
POSTGRES_PID=0

run_as_postgres() {
    runuser -u postgres -- "$@"
}

mkdir -p "$PGDATA"
chown -R postgres:postgres "$PGDATA" /var/lib/postgresql

if [ ! -s "$PGDATA/PG_VERSION" ]; then
    PASSFILE=$(mktemp)
    echo "$POSTGRES_PASSWORD" > "$PASSFILE"
    chown postgres:postgres "$PASSFILE"
    chmod 600 "$PASSFILE"
    run_as_postgres initdb -D "$PGDATA" -U "$POSTGRES_USER" -A scram-sha-256 --pwfile="$PASSFILE"
    rm -f "$PASSFILE"
    echo "listen_addresses='*'" >> "$PGDATA/postgresql.conf"
fi

run_as_postgres postgres -D "$PGDATA" -h 0.0.0.0 -p 5432 &
POSTGRES_PID=$!

cleanup() {
    if [ "$UVICORN_PID" -ne 0 ] && kill -0 "$UVICORN_PID" >/dev/null 2>&1; then
        kill "$UVICORN_PID"
    fi
    if [ "$POSTGRES_PID" -ne 0 ] && kill -0 "$POSTGRES_PID" >/dev/null 2>&1; then
        kill "$POSTGRES_PID"
    fi
}
trap cleanup EXIT INT TERM

export PGPASSWORD="$POSTGRES_PASSWORD"

until run_as_postgres pg_isready -q -h 127.0.0.1 -U "$POSTGRES_USER" -d postgres; do
    echo "Waiting for PostgreSQL to start..."
    sleep 1
done

if ! run_as_postgres psql -h 127.0.0.1 -U "$POSTGRES_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DB}'" | grep -q 1; then
    run_as_postgres createdb -h 127.0.0.1 -U "$POSTGRES_USER" "$POSTGRES_DB"
fi

export DATABASE_URL=${DATABASE_URL:-"postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5432/${POSTGRES_DB}"}

uvicorn main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

wait -n "$POSTGRES_PID" "$UVICORN_PID"
EXIT_CODE=$?
exit "$EXIT_CODE"
