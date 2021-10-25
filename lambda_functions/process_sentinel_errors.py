"""Select failed Sentinel processing jobs and re-process them in blocks"""
import os
import boto3
import json
from botocore.errorfactory import ClientError
from datetime import datetime, timedelta


db_credentials_secrets_store_arn = os.getenv("HLS_SECRETS")
database_name = os.getenv("HLS_DB_NAME")
db_cluster_arn = os.getenv("HLS_DB_ARN")
state_machine = os.getenv("STATE_MACHINE")
rds_client = boto3.client("rds-data")
step_function_client = boto3.client("stepfunctions")


def chunk(chunk_list, chunk_size):
    for i in range(0, len(chunk_list), chunk_size):
        yield chunk_list[i:i + chunk_size]


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
    converted = {
        "id": record[0]["longValue"],
        "granule": record[1]["stringValue"]
    }
    return converted


def execute_step_function(error_chunk, submit_errors):
    input = json.dumps({
        "errors": error_chunk,
    })
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
    historic = os.getenv("HISTORIC")

    if historic == "historic":
        historic_value = True
    else:
        historic_value = False

    q = (
        "SELECT id, granule from sentinel_log WHERE"
        + " (jobinfo->'Container'->>'ExitCode' NOT IN ('0', '137', '3', '4')"
        + " or jobinfo->'Container'->>'ExitCode' is NULL)"
        + " AND jobinfo is NOT NULL"
        + " AND run_count < :retry_limit::integer"
        + " AND historic = :historic_value::boolean"
        + " LIMIT 4000;"
    )
    print(q)
    response = execute_statement(
        q,
        sql_parameters=[
            {"name": "retry_limit", "value": {"longValue": retry_limit}},
            {"name": "historic_value", "value": {"booleanValue": historic_value}},
        ]
    )
    records = map(convert_records, response["records"])
    granule_errors = list(records)
    error_chunks = list(chunk(granule_errors, 100))
    submission_errors = []

    for error_chunk in error_chunks:
        execute_step_function(error_chunk, submission_errors)

    if len(submission_errors) > 0:
        raise NameError("A step function execution error occurred")
