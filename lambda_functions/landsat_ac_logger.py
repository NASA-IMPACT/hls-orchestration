"""Update landsat_ac_log table with results of landsat ac batch job."""
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
    Update landsat_ac_log table with results of landsat ac batch job.

    Parameters:
    event (dict) Event source of Step Function SubmitJob result

    Returns:
    exitcode (int) The exit code of the logged job result

    """
    parsed_info = parse_jobinfo("jobinfo", event)
    jobinfo, jobinfostring, exitcode, jobid = itemgetter(
        "jobinfo", "jobinfostring", "exitcode", "jobid"
    )(parsed_info)
    q = (
        "UPDATE landsat_ac_log SET (jobid, jobinfo, run_count) ="
        + " (:jobid::text, :jobinfo::jsonb, run_count + 1)"
        + " WHERE scene_id = :scene::text"
    )
    sql_parameters = [
        {"name": "jobinfo", "value": {"stringValue": jobinfostring}},
        {"name": "scene", "value": {"stringValue": event["scene"]}},
    ]
    if jobid:
        sql_parameters.append(
            {
                "name": "jobid",
                "value": {"stringValue": jobid},
            },
        )
    execute_statement(q, sql_parameters=sql_parameters)

    print(f"Exit Code is {exitcode}")
    return exitcode
