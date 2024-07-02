#!/bin/bash

POSTGRES_USER=$(aws ssm get-parameter --profile digital-dev --name /drb/production/postgres/user --with-decryption | jq -r '.Parameter.Value') \
POSTGRES_PSWD=$(aws ssm get-parameter --profile digital-dev --name /drb/production/postgres/pswd --with-decryption | jq -r '.Parameter.Value') \
POSTGRES_HOST="sfr-new-metadata-production-cluster.cluster-cvy7z512hcjg.us-east-1.rds.amazonaws.com" \
POSTGRES_PORT="5432" \
POSTGRES_NAME="dcdw_production" \
  alembic -c alembic.ini upgrade head
