# Stage 1: Builder - compila extensões PostgreSQL
FROM postgres:16-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    gcc \
    make \
    git \
    postgresql-server-dev-16 \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/postgrespro/pg_wait_sampling.git /tmp/pg_wait_sampling \
    && cd /tmp/pg_wait_sampling \
    && make USE_PGXS=1 \
    && make USE_PGXS=1 install

RUN git clone https://github.com/percona/pg_stat_monitor.git /tmp/pg_stat_monitor \
    && cd /tmp/pg_stat_monitor \
    && make USE_PGXS=1 \
    && make USE_PGXS=1 install

# Stage 2: Runtime - imagem final com extensões e New Relic
FROM postgres:16-bookworm

COPY --from=builder /usr/lib/postgresql/16/lib/pg_wait_sampling.so /usr/lib/postgresql/16/lib/
COPY --from=builder /usr/share/postgresql/16/extension/pg_wait_sampling* /usr/share/postgresql/16/extension/
COPY --from=builder /usr/lib/postgresql/16/lib/pg_stat_monitor.so /usr/lib/postgresql/16/lib/
COPY --from=builder /usr/share/postgresql/16/extension/pg_stat_monitor* /usr/share/postgresql/16/extension/

RUN printf '#!/bin/sh\nexit 0' > /usr/bin/systemctl && chmod +x /usr/bin/systemctl \
    && apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl gnupg2 \
    && curl -fsSL https://download.newrelic.com/infrastructure_agent/gpg/newrelic-infra.gpg \
       | gpg --dearmor -o /etc/apt/trusted.gpg.d/newrelic-infra.gpg \
    && echo "deb https://download.newrelic.com/infrastructure_agent/linux/apt bookworm main" \
       > /etc/apt/sources.list.d/newrelic-infra.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends newrelic-infra nri-postgresql \
    && rm -rf /var/lib/apt/lists/* \
    && rm /usr/bin/systemctl

COPY init-extensions.sql /docker-entrypoint-initdb.d/
COPY entrypoint-wrapper.sh /usr/local/bin/entrypoint-wrapper.sh
RUN chmod +x /usr/local/bin/entrypoint-wrapper.sh

ENTRYPOINT ["entrypoint-wrapper.sh"]
CMD ["postgres", \
     "-c", "shared_preload_libraries=pg_stat_statements,pg_wait_sampling,pg_stat_monitor", \
     "-c", "pg_stat_statements.max=10000", \
     "-c", "pg_stat_statements.track=all", \
     "-c", "pg_stat_statements.save=on"]
