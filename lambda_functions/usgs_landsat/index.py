import boto3
import os
import json
from datetime import datetime, timedelta

from usgs import api
from hls_lambda_layer.landsat_scene_parser import landsat_parse_scene_id

db_credentials_secrets_store_arn = os.getenv("HLS_SECRETS")
database_name = os.getenv("HLS_DB_NAME")
db_cluster_arn = os.getenv("HLS_DB_ARN")
rds_client = boto3.client("rds-data")


def get_metdata(results):
    for result in results:
        scene = result["summary"]
        fields = scene.split(",")
        sceneId = fields[0].split(":")[1].strip()
        meta = landsat_parse_scene_id(sceneId)
        yield meta


def batch_execute_statement(parameterSets):
    sql = (
        "INSERT INTO landsat_ac_log (path, row, acquisition, scene_id) VALUES"
        + "(:path::varchar(3), :row::varchar(3), :acquisition::date, :scene_id::varchar(200))"
        + " ON CONFLICT ON CONSTRAINT no_dupe_pathrowdate"
        + " DO NOTHING"
    )
    response = rds_client.batch_execute_statement(
        secretArn=db_credentials_secrets_store_arn,
        database=database_name,
        resourceArn=db_cluster_arn,
        sql=sql,
        parameterSets=parameterSets,
    )
    return response


def add_sql_parameter(parameter_sets, scene):
    sql_parameters = [
        {"name": "path", "value": {"stringValue": scene["path"]}},
        {"name": "row", "value": {"stringValue": scene["row"]}},
        {"name": "acquisition", "value": {"stringValue": scene["date"]}},
        {"name": "scene_id", "value": {"stringValue": scene["scene"]}},
    ]
    parameter_sets.append(sql_parameters)


def handler(event, context):
    time = event["time"]
    invocation_date = datetime.strptime(time,"%Y-%m-%dT%H:%M:%SZ").date()
    modified_date = invocation_date - timedelta(1)
    where = {
        20510: "RT",
        20517: "L1TP",
        20511: modified_date.strftime("%Y/%m/%d")
    }
    username = os.environ["USERNAME"]
    password = os.environ["PASSWORD"]
    api_key = api.login(username, password, save=False)["data"]
    search_results = api.search("LANDSAT_OT_C2_L1", "EE", where=where, api_key=api_key)
    scenes = get_metdata(search_results["data"]["results"])
    sql_parameter_sets = []
    for scene in scenes:
        if len(sql_parameter_sets) == 10:
            batch_execute_statement(sql_parameter_sets)
            sql_parameter_sets = []
        else:
            add_sql_parameter(sql_parameter_sets, scene)
    # Load remaining batch of scenes
    batch_execute_statement(sql_parameter_sets)
    return event
