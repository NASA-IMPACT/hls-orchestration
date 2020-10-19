import os
import boto3
import json
from operator import itemgetter
from hls_lambda_layer.hls_batch_utils import parse_jobinfo

db_credentials_secrets_store_arn = os.getenv("HLS_SECRETS")
database_name = os.getenv("HLS_DB_NAME")
db_cluster_arn = os.getenv("HLS_DB_ARN")
rds_client = boto3.client("rds-data")


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
    parsed_info = parse_jobinfo("jobinfo", event)
    jobinfo, jobinfostring, exitcode = itemgetter(
        "jobinfo", "jobinfostring", "exitcode"
    )(parsed_info)
    q = "INSERT INTO eventlog (event) VALUES (:event::jsonb);"
    execute_statement(
        q,
        sql_parameters=[{"name": "event", "value": {"stringValue": jobinfostring}}],
    )

    print(f"Exit Code is {exitcode}")
    return exitcode
