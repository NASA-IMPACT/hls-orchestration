"""Lambda function for omnipotent setup and modification of HLS logging database"""
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

CREATE TABLE IF NOT EXISTS landsat_mgrs_log (
    id bigserial primary key,
    ts timestamptz default now() not null,
    path varchar(3) not null,
    mgrs varchar(5) not null,
    acquisition date not null,
    jobinfo jsonb,
    constraint no_dupe_mgrs unique(path, mgrs, acquisition)
);

CREATE TABLE IF NOT EXISTS landsat_ac_log (
    id bigserial primary key,
    ts timestamptz default now() not null,
    path varchar(3) not null,
    row varchar(3) not null,
    acquisition date not null,
    jobid text not null,
    jobinfo jsonb,
    constraint no_dupe_pathrowdate unique(path, row, acquisition)
);

ALTER TABLE landsat_ac_log ADD COLUMN IF NOT EXISTS scene_id VARCHAR(100);
ALTER TABLE landsat_ac_log ALTER COLUMN jobid DROP NOT NULL;

DO $$
BEGIN
  IF EXISTS(SELECT *
    FROM information_schema.columns
    WHERE table_name='eventlog' and column_name='event')
  THEN
      ALTER TABLE eventlog RENAME COLUMN event TO jobinfo;
  END IF;
END $$;

ALTER TABLE IF EXISTS eventlog RENAME TO sentinel_log;

CREATE TABLE IF NOT EXISTS sentinel_log (
    id bigserial primary key,
    ts timestamptz default now() not null,
    jobinfo jsonb,
    granule varchar,
    run_count integer
);

ALTER TABLE sentinel_log ADD COLUMN IF NOT EXISTS granule VARCHAR;
ALTER TABLE sentinel_log ADD COLUMN IF NOT EXISTS run_count INTEGER;

DROP VIEW IF EXISTS sentinel_granule_log;
CREATE VIEW sentinel_granule_log AS
select id, ts, granule, run_count,
jobinfo->>'Status' as status,
to_timestamp((jobinfo->>'CreatedAt')::float/1000) as job_created,
to_timestamp((jobinfo->>'StartedAt')::float/1000) as job_started,
to_timestamp((jobinfo->>'StoppedAt')::float/1000) as job_stopped,
jobinfo
from sentinel_log WHERE jobinfo IS NOT NULL;

DROP VIEW IF EXISTS granule_log;
DROP FUNCTION IF EXISTS granule(IN event jsonb, OUT granule text);

ALTER TABLE landsat_ac_log ADD COLUMN IF NOT EXISTS run_count INTEGER;
ALTER TABLE landsat_mgrs_log ADD COLUMN IF NOT EXISTS run_count INTEGER;

DROP VIEW IF EXISTS landsat_ac_granule_log;
CREATE VIEW landsat_ac_granule_log AS
select id, ts, run_count, scene_id,
jobinfo->>'Status' as status,
to_timestamp((jobinfo->>'CreatedAt')::float/1000) as job_created,
to_timestamp((jobinfo->>'StartedAt')::float/1000) as job_started,
to_timestamp((jobinfo->>'StoppedAt')::float/1000) as job_stopped,
jobinfo
from landsat_ac_log WHERE jobinfo IS NOT NULL;

DROP VIEW IF EXISTS landsat_mgrs_granule_log;
CREATE VIEW landsat_mgrs_granule_log AS
select id, ts, run_count,
jobinfo->>'Status' as status,
to_timestamp((jobinfo->>'CreatedAt')::float/1000) as job_created,
to_timestamp((jobinfo->>'StartedAt')::float/1000) as job_started,
to_timestamp((jobinfo->>'StoppedAt')::float/1000) as job_stopped,
jobinfo
from landsat_mgrs_log WHERE jobinfo IS NOT NULL;
"""


def handler(event, context):
    """
    Run omnipotent set up PSQL for HLS logging database.

    Parameters:
    event (dict) Lambda trigger event source

    Returns:
    event (dict) Lambda trigger event source

    """
    print(event)
    print(context)
    execute_statement(ddl)
    return event
