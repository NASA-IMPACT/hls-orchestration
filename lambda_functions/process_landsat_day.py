import os
import boto3
from typing import Dict, Any
from botocore.errorfactory import ClientError
from random import randint
import json
import re
import datetime


db_credentials_secrets_store_arn = os.getenv("HLS_SECRETS")
database_name = os.getenv("HLS_DB_NAME")
db_cluster_arn = os.getenv("HLS_DB_ARN")


rds_client = boto3.client("rds-data")


def landsat_parse_scene_id(sceneid):
    """
    Parse Landsat-8 scene id.
    Author @perrygeo - http://www.perrygeo.com
    """

    precollection_pattern = (
        r"^L"
        r"(?P<sensor>\w{1})"
        r"(?P<satellite>\w{1})"
        r"(?P<path>[0-9]{3})"
        r"(?P<row>[0-9]{3})"
        r"(?P<acquisitionYear>[0-9]{4})"
        r"(?P<acquisitionJulianDay>[0-9]{3})"
        r"(?P<groundStationIdentifier>\w{3})"
        r"(?P<archiveVersion>[0-9]{2})$"
    )

    collection_pattern = (
        r"^L"
        r"(?P<sensor>\w{1})"
        r"(?P<satellite>\w{2})"
        r"_"
        r"(?P<processingCorrectionLevel>\w{4})"
        r"_"
        r"(?P<path>[0-9]{3})"
        r"(?P<row>[0-9]{3})"
        r"_"
        r"(?P<acquisitionYear>[0-9]{4})"
        r"(?P<acquisitionMonth>[0-9]{2})"
        r"(?P<acquisitionDay>[0-9]{2})"
        r"_"
        r"(?P<processingYear>[0-9]{4})"
        r"(?P<processingMonth>[0-9]{2})"
        r"(?P<processingDay>[0-9]{2})"
        r"_"
        r"(?P<collectionNumber>\w{2})"
        r"_"
        r"(?P<collectionCategory>\w{2})$"
    )

    for pattern in [collection_pattern, precollection_pattern]:
        match = re.match(pattern, sceneid, re.IGNORECASE)
        if match:
            meta: Dict[str, Any] = match.groupdict()
            break

    meta["scene"] = sceneid
    if meta.get("acquisitionJulianDay"):
        date = datetime.datetime(
            int(meta["acquisitionYear"]), 1, 1
        ) + datetime.timedelta(int(meta["acquisitionJulianDay"]) - 1)

        meta["date"] = date.strftime("%Y-%m-%d")
    else:
        meta["date"] = "{}-{}-{}".format(
            meta["acquisitionYear"],
            meta["acquisitionMonth"],
            meta["acquisitionDay"]
        )

    collection = meta.get("collectionNumber", "")
    if collection != "":
        collection = "c{}".format(int(collection))

    return meta


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
    q = (
        "SELECT scene_id FROM landsat_ac_log WHERE"
        + " DATE(ts) = TO_DATE(:retrieved_date::text,'DD/MM/YYYY');"
    )
    response = execute_statement(
        q,
        sql_parameters=[
            {"name": "retrieved_date", "value": {"stringValue":
                                                 event["retrieved_date"]}},
        ]
    )
    errors = []
    for record in response["records"]:
        scene_id = record[0]["stringValue"]
        execute_step_function(scene_id, errors)

    if len(errors) > 0:
        raise NameError("A step function execution error occurred")
