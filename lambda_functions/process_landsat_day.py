import os
import boto3
from botocore.errorfactory import ClientError
from random import randint
import json
import datetime
from datetime import timedelta
from hls_lambda_layer.landsat_scene_parser import landsat_parse_scene_id


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


def execute_step_function(scene_id, errors):
    state_machine = os.getenv("STATE_MACHINE")
    step_functions = boto3.client("stepfunctions")

    scene_meta = landsat_parse_scene_id(scene_id)
    s3_basepath = "collection02/level-1/standard/oli-tirs"
    year = scene_meta["acquisitionYear"]
    path = scene_meta["path"]
    row = scene_meta["row"]
    prefix = f"{s3_basepath}/{year}/{path}/{row}/{scene_id}"
    scene_meta["scheme"] = "s3"
    scene_meta["bucket"] = "usgs-landsat"
    scene_meta["prefix"] = prefix

    try:
        rand = randint(100, 999)
        input = json.dumps(scene_meta)
        step_functions.start_execution(
            stateMachineArn=state_machine,
            name=f"{scene_id}_{rand}",
            input=input,
        )
    except ClientError as ce:
        print(ce)
        errors.append(ce)


def handler(event, context):
    time = event["time"]
    invocation_date = datetime.datetime.strptime(time,"%Y-%m-%dT%H:%M:%SZ").date()
    retrieved_date = invocation_date - timedelta(2)
    formatted_retrieved_date = retrieved_date.strftime("%d/%m/%Y")
    q = (
        "SELECT scene_id FROM landsat_ac_log WHERE"
        + " DATE(ts) = TO_DATE(:retrieved_date::text,'DD/MM/YYYY');"
    )
    response = execute_statement(
        q,
        sql_parameters=[
            {"name": "retrieved_date", "value": {"stringValue":
                                                 formatted_retrieved_date}},
        ]
    )
    errors = []
    for record in response["records"]:
        scene_id = record[0]["stringValue"]
        execute_step_function(scene_id, errors)

    if len(errors) > 0:
        raise NameError("A step function execution error occurred")
