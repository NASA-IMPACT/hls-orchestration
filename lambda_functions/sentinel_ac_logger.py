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
    print(f"Exit Code is {exitcode}")

    succeeded = False
    expected_error = False
    unexpected_error = True

    if exitcode == 0:
        succeeded = True
        unexpected_error = False
    elif exitcode in [137, 3, 4]:
        succeeded = False
        expected_error = True
        unexpected_error = False
    else:
        succeeded = False
        expected_error = False
        unexpected_error = True

    if "id" in event:
        selector_string = " WHERE id = :selector::text"
        selector_value = event["id"]
        selector_parameter = {
            "name": "selector",
            "value": {"longValue": selector_value},
        }
    else:
        selector_string = " WHERE granule = :selector::text"
        selector_value = event["granule"]
        selector_parameter = {
            "name": "selector",
            "value": {"stringValue": selector_value},
        }
    q = (
        "UPDATE sentinel_log SET"
        + " (jobinfo, run_count, succeeded, expected_error, unexpected_error) ="
        + " (:jobinfo::jsonb, run_count + 1, :succeeded::boolean, :expected_error::boolean, :unexpected_error::boolean)"
        + selector_string
    )
    sql_parameters = [
        {"name": "jobinfo", "value": {"stringValue": jobinfostring}},
        {"name": "succeeded", "value": {"booleanValue": succeeded}},
        {"name": "expected_error", "value": {"booleanValue": expected_error}},
        {"name": "unexpected_error", "value": {"booleanValue": unexpected_error}},
    ]
    sql_parameters.append(selector_parameter)
    execute_statement(q, sql_parameters=sql_parameters)
    return exitcode
