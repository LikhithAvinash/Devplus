FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PGDATA=/var/lib/postgresql/data
ENV POSTGRES_DB=agg_db

WORKDIR /app

# Install Python build deps and PostgreSQL server/client for the bundled DB
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        postgresql \
        postgresql-client \
    && POSTGRES_BIN_DIR="$(dirname "$(readlink -f /usr/lib/postgresql/*/bin/postgres)")" \
    && ln -s ${POSTGRES_BIN_DIR}/* /usr/local/bin/ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && chown -R postgres:postgres /app /var/lib/postgresql

EXPOSE 8000 5432

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
