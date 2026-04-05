#!/bin/bash
set -e
set -u

function create_user_and_database() {
    local database=$1
    local owner=$2
    local password=$3

    echo "  Creating user '$owner' and database '$database'"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE USER $owner WITH PASSWORD '$password';
        CREATE DATABASE $database OWNER $owner;
        GRANT ALL PRIVILEGES ON DATABASE $database TO $owner;
EOSQL
}

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
    echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
    for entry in $(echo "$POSTGRES_MULTIPLE_DATABASES" | tr ',' ' '); do
        db=$(echo "$entry" | cut -d':' -f1)
        owner=$(echo "$entry" | cut -d':' -f2)
        password=$(echo "$entry" | cut -d':' -f3)
        create_user_and_database "$db" "$owner" "$password"
    done
    echo "Multiple databases created"
fi
