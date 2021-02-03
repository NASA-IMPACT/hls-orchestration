import os
import boto3
from botocore.errorfactory import ClientError
from random import randint


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


def execute_step_function(error_chunk, submit_errors, job_stopped):
    input = {
        "errors": error_chunk,
        "fromdate": job_stopped,
    }
    try:
        rand = randint(100, 999)
        step_function_client.start_execution(
            stateMachineArn=state_machine,
            name=f"{rand}",
            input=input,
        )
    except ClientError as ce:
        print(ce)
        submit_errors.append(ce)


def handler(event, context):
    q = (
        "SELECT id, granule, job_stopped from granule_log WHERE"
        + " (event->'Container'->>'ExitCode' = '1'"
        + " or event->'Container'->>'ExitCode' is NULL)"
        + " AND DATE(job_stopped) = TO_DATE(:fromdate::text,'DD/MM/YYYY');"
    )
    response = execute_statement(
        q,
        sql_parameters=[
            {"name": "fromdate", "value": {"stringValue": event["fromdate"]}},
        ]
    )
    records = map(convert_records, response["records"])
    granule_errors = list(records)
    error_chunks = list(chunk(granule_errors, 100))
    submission_errors = []

    for error_chunk in error_chunks:
        execute_step_function(error_chunk, submission_errors, event["fromdate"])

    if len(submission_errors) > 0:
        raise NameError("A step function execution error occurred")
