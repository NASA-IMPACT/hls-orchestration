"""Select failed Landsat AC processing jobs and re-process them in blocks"""
import json
import os
from datetime import datetime, timedelta

import boto3
from botocore.errorfactory import ClientError
from hls_lambda_layer.landsat_scene_parser import landsat_parse_scene_id

db_credentials_secrets_store_arn = os.getenv("HLS_SECRETS")
database_name = os.getenv("HLS_DB_NAME")
db_cluster_arn = os.getenv("HLS_DB_ARN")
state_machine = os.getenv("STATE_MACHINE")
rds_client = boto3.client("rds-data")
step_function_client = boto3.client("stepfunctions")


def chunk(chunk_list, chunk_size):
    for i in range(0, len(chunk_list), chunk_size):
        yield chunk_list[i : i + chunk_size]


def execute_statement(sql, sql_parameters=[]):
    response = rds_client.execute_statement(
        secretArn=db_credentials_secrets_store_arn,
        database=database_name,
        resourceArn=db_cluster_arn,
        sql=sql,
        parameters=sql_parameters,
    )
    return response


def convert_records(record):
    scene_id = record[1]["stringValue"]
    scene_meta = landsat_parse_scene_id(scene_id)
    acquisitionYear = scene_meta["acquisitionYear"]
    path = scene_meta["path"]
    row = scene_meta["row"]
    prefix = f"collection02/level-1/standard/oli-tirs/{acquisitionYear}/{path}/{row}/{scene_id}"
    converted = {
        "id": record[0]["longValue"],
        "scene_id": scene_id,
        "scheme": "s3",
        "bucket": "usgs-landsat",
        "prefix": prefix,
    }
    converted.update(scene_meta)
    return converted


def execute_step_function(error_chunk, submit_errors):
    input = json.dumps(
        {
            "errors": error_chunk,
        }
    )
    try:
        step_function_client.start_execution(
            stateMachineArn=state_machine,
            input=input,
        )
    except ClientError as ce:
        print(ce)
        submit_errors.append(ce)


def handler(event, context):
    retry_limit = int(os.getenv("RETRY_LIMIT"))
    #  Using the view ensures we are only using records which have jobinfo
    q = (
        "SELECT id, scene_id from landsat_ac_granule_log WHERE"
        + " (jobinfo->'Container'->>'ExitCode' = '1'"
        + " or jobinfo->'Container'->>'ExitCode' is NULL)"
        + " AND scene_id is not null AND run_count >= 1 AND"
        + " run_count < :retry_limit::integer;"
    )
    response = execute_statement(
        q,
        sql_parameters=[
            {"name": "retry_limit", "value": {"longValue": retry_limit}},
        ],
    )
    records = map(convert_records, response["records"])
    granule_errors = list(records)
    error_chunks = list(chunk(granule_errors, 100))
    submission_errors = []

    for error_chunk in error_chunks:
        execute_step_function(error_chunk, submission_errors)

    if len(submission_errors) > 0:
        raise NameError("A step function execution error occurred")
