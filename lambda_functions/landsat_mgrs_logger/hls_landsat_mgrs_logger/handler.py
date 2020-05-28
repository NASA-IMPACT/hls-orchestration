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


def handler(event, context):
    acquisition_date = (
        f'{event["processingYear"]}-{event["processingMonth"]}-{event["processingDay"]}'
    )
    q = "INSERT INTO landsat_mgrs_log (path, row, acquisition) ON CONFLICT DO NOTHING;"
    execute_statement(
        q,
        sql_parameters=[
            {"name": "path", "value": {"stringValue": event["path"]}},
            {"name": "row", "value": {"stringValue": event["row"]}},
            {"name": "acquisition", "value": {"stringValue": acquisition_date}},
        ],
    )
    return event
