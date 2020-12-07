import boto3
import os
import json
import re
from typing import Dict, Any
from datetime import datetime, timedelta

from usgs import api

db_credentials_secrets_store_arn = os.getenv("HLS_SECRETS")
database_name = os.getenv("HLS_DB_NAME")
db_cluster_arn = os.getenv("HLS_DB_ARN")
rds_client = boto3.client("rds-data")


def landsat_parse_scene_id(sceneid):
    """
    Parse Landsat-8 scene id.
    Author @perrygeo - http://www.perrygeo.com
    Attributes
    ----------
        sceneid : str
            Landsat sceneid.
    Returns
    -------
        out : dict
            dictionary with metadata constructed from the sceneid.
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


def get_metdata(results):
    for result in results:
        scene = result["summary"]
        fields = scene.split(",")
        sceneId = fields[0].split(":")[1].strip()
        meta = landsat_parse_scene_id(sceneId)
        yield meta


def batch_execute_statement(parameters):
    sql = (
        "INSERT INTO landsat_ac_log (path, row, acquisition, scene_id) VALUES"
        + "(:path::varchar(3), :row::varchar(3), :acquisition::date, :scene_id:text)"
        + " ON CONFLICT ON CONSTRAINT no_dupe_pathrowdate"
        + " DO NOTHING"
    )
    response = rds_client.batch_execute_statement(
        secretArn=db_credentials_secrets_store_arn,
        database=database_name,
        resourceArn=db_cluster_arn,
        sql=sql,
        parameters=parameters,
    )
    return response


def add_sql_parameter(sql_parameters, scene):
    sql_parameter = [
        {"name": "path", "value": {"stringValue": scene["path"]}},
        {"name": "row", "value": {"stringValue": scene["row"]}},
        {"name": "acquisition", "value": {"stringValue": scene["date"]}},
        {"name": "scene_id", "value": {"stringValue": scene["scene"]}},
    ],
    sql_parameters.append(sql_parameter)


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
    sql_parameters = []
    for scene in scenes:
        if len(sql_parameters) == 10:
            batch_execute_statement(sql_parameters)
            sql_parameters = []
        else:
            add_sql_parameter(sql_parameters, scene)
    # Load remaining batch of scenes
    batch_execute_statement(sql_parameters)

# handler({"time": "2020-12-04T12:00:00Z"}, {})
