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
"""

execute_statement(ddl)


def handler(event, context):
    print(event)
    if event.get('Cause'):
        event['Cause']=json.loads(event['Cause'])
    q = "INSERT INTO eventlog (event) VALUES (:event::jsonb);"
    execute_statement(
        q,
        sql_parameters=[{"name": "event", "value": {"stringValue": json.dumps(event)}}],
    )

    return event
