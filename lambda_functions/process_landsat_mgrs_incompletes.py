"""Select L30 MGRS grid squares that failed or have not yet processed and re-process them in blocks"""
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
        "MGRS": record[0]["stringValue"],
        "path": record[1]["stringValue"],
        "date": record[2]["stringValue"]
    }
    return converted


def execute_step_function(chunk, submit_errors, job_stopped):
    input = json.dumps({
        "incompletes": chunk,
        "fromdate": job_stopped,
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
    date_delta = os.getenv("DAYS_PRIOR")
    hour_delta = os.getenv("HOURS_PRIOR")
    retry_limit = int(os.getenv("RETRY_LIMIT"))
    historic = os.getenv("HISTORIC")
    event_time = datetime.strptime(event["time"], '%Y-%m-%dT%H:%M:%SZ')

    if historic == "historic":
        historic_value = True
    else:
        historic_value = False

    q = (
        "SELECT mgrs, path, acquisition from landsat_mgrs_log WHERE"
        + " (jobinfo->'Container'->>'ExitCode' IS NULL OR"
        + " jobinfo->'Container'->>'ExitCode' != '0')"
        + " AND run_count < :retry_limit::integer"
        + " AND historic = :historic_value::boolean"
    )
    sql_parameters = [
        {"name": "retry_limit", "value": {"longValue": retry_limit}},
        {"name": "historic_value", "value": {"booleanValue": historic_value}},
    ]

    if hour_delta:
        delta = (event_time - timedelta(hours=int(hour_delta))).strftime("%d-%m-%Y %H:%M:%S")
        delta_query = " AND ts <= TO_TIMESTAMP(:delta::text,'DD-MM-YYYY HH24:MI:SS');"
    else:
        delta = (event_time - timedelta(days=int(date_delta))).strftime("%d/%m/%Y")
        delta_query = " AND DATE(ts) <= TO_DATE(:delta::text,'DD/MM/YYYY');"

    sql = q + delta_query
    print(sql)
    sql_parameters.append({"name": "delta", "value": {"stringValue": delta}})

    response = execute_statement(sql, sql_parameters=sql_parameters)
    records = map(convert_records, response["records"])
    incompletes = list(records)
    incomplete_chunks = list(chunk(incompletes, 100))
    submission_errors = []

    for incomplete_chunk in incomplete_chunks:
        execute_step_function(incomplete_chunk, submission_errors, delta)

    if len(submission_errors) > 0:
        raise NameError("A step function execution error occurred")
