import os
import boto3
import json
from pathlib import Path
from typing import Dict
from botocore.errorfactory import ClientError
from random import randint
import re
import datetime
from typing import Any


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
            meta["acquisitionYear"], meta["acquisitionMonth"], meta["acquisitionDay"]
        )

    collection = meta.get("collectionNumber", "")
    if collection != "":
        collection = "c{}".format(int(collection))

    meta["scheme"] = "s3"
    meta["bucket"] = "landsat-pds"
    meta["prefix"] = os.path.join(collection, "L8", meta["path"], meta["row"], sceneid)

    return meta


def handler(event: Dict, context: Dict):
    state_machine = os.getenv("STATE_MACHINE")
    step_functions = boto3.client("stepfunctions")
    prefix = randint(100, 999)
    try:
        message = event["Records"][0]["Sns"]["Message"]
        parsed_message = json.loads(message)
        key = parsed_message["Records"][0]["s3"]["object"]["key"]

    except KeyError:
        print("Message body does not contain key")

    scene_id = key.split("/")[-2]
    scene_meta = landsat_parse_scene_id(scene_id)
    # Skip unless real-time (RT) collection
    if scene_meta["collectionCategory"] == "RT":
        try:
            input = json.dumps(scene_meta)
            step_functions.start_execution(
                stateMachineArn=state_machine,
                name=f"{prefix}_{scene_meta['scene']}",
                input=input,
            )
        except ClientError as ce:
            print(ce)
    return event
