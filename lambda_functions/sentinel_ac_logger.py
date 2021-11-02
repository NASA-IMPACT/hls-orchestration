"""Update sentinel_log table with results of sentinel batch job."""
import json
import os
from operator import itemgetter

import boto3
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
    """
    Update sentinel_log table with results of sentinel batch job.

    Parameters:
    event (dict) Event source of Step Function SubmitJob result

    Returns:
    exitcode (int) The exit code of the logged job result

    """
    parsed_info = parse_jobinfo("jobinfo", event)
    jobinfo, jobinfostring, exitcode = itemgetter(
        "jobinfo", "jobinfostring", "exitcode"
    )(parsed_info)
    q = (
        "UPDATE sentinel_log SET (jobinfo, run_count) ="
        + " (:jobinfo::jsonb, run_count + 1)"
        + " WHERE granule = :granule::text"
    )
    sql_parameters = [
        {"name": "jobinfo", "value": {"stringValue": jobinfostring}},
        {"name": "granule", "value": {"stringValue": event["granule"]}},
    ]
    execute_statement(q, sql_parameters=sql_parameters)
    print(f"Exit Code is {exitcode}")
    return exitcode
