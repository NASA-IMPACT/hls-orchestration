import os
import boto3
import json

rds_client = boto3.client("rds-data")

db_credentials_secrets_store_arn = os.getenv("HLS_SECRETS")
database_name = os.getenv("HLS_DB_NAME")
db_cluster_arn = os.getenv("HLS_DB_ARN")


def execute_statement(sql, sql_parameters=[]):
    response = rds_client.execute_statement(
        secretArn=db_credentials_secrets_store_arn,
        database=database_name,
        resourceArn=db_cluster_arn,
        sql=sql,
        parameters=sql_parameters,
    )
    return response


ddl = """
CREATE TABLE IF NOT EXISTS eventlog (
    id bigserial primary key,
    ts timestamptz default now() not null,
    event jsonb
);
CREATE TABLE IF NOT EXISTS landsat_mgrs_log (
    id bigserial primary key,
    ts timestamptz default now() not null,
    path varchar(3) not null,
    mgrs varchar(5) not null,
    acquisition date not null,
    jobstatus boolean,
    constraint no_dupe_mgrs unique(path, mgrs, acquisition)
);
CREATE TABLE IF NOT EXISTS landsat_ac_log (
    id bigserial primary key,
    ts timestamptz default now() not null,
    path varchar(3) not null,
    row varchar(3) not null,
    acquisition date not null,
    jobid text not null,
    constraint no_dupe_pathrowdate unique(path, row, acquisition)
);
CREATE OR REPLACE FUNCTION
granule(IN event jsonb, OUT granule text)
AS $$
SELECT a->>'Value'
FROM jsonb_array_elements(event->'Container'->'Environment') a
WHERE a->>'Name'='GRANULE_LIST'
$$ LANGUAGE SQL IMMUTABLE STRICT;
DROP VIEW IF EXISTS granule_log;
CREATE VIEW granule_log AS
select id, ts,
granule(event),
event->>'Status' as status,
to_timestamp((event->>'CreatedAt')::float/1000) as job_created,
to_timestamp((event->>'StartedAt')::float/1000) as job_started,
to_timestamp((event->>'StoppedAt')::float/1000) as job_stopped,
event
from eventlog WHERE granule(event) IS NOT NULL;
"""


def handler(event, context):
    print(event)
    print(context)
    execute_statement(ddl)
    return event
