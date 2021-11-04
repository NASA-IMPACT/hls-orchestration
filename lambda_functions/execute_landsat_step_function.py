import json
import os
from typing import Dict
from urllib.parse import urlparse

import boto3
from botocore.errorfactory import ClientError
from hls_lambda_layer.landsat_scene_parser import landsat_parse_scene_id


def handler(event: Dict, context: Dict):
    print(event)
    step_functions = boto3.client("stepfunctions")
    state_machine = os.getenv("STATE_MACHINE")
    historic_value = os.getenv("HISTORIC")
    try:
        message = event["Records"][0]["Sns"]["Message"]
        parsed_message = json.loads(message)
        scene_id = parsed_message["landsat_product_id"]
        location = parsed_message["s3_location"]

    except KeyError:
        print("Message body does not contain key")

    url_components = urlparse(location)
    scene_meta = landsat_parse_scene_id(scene_id)
    scene_meta["scheme"] = url_components.scheme
    scene_meta["bucket"] = url_components.netloc
    scene_meta["prefix"] = url_components.path.strip("/")
    print(scene_meta)
    # Skip unless real-time (RT) collection
    if (
        scene_meta["collectionCategory"] == "RT"
        and scene_meta["satellite"] == "08"
        and scene_meta["processingCorrectionLevel"] == "L1TP"
    ) or historic_value == "historic":
        try:
            input = json.dumps(scene_meta)
            step_functions.start_execution(
                stateMachineArn=state_machine,
                input=input,
            )
        except ClientError as ce:
            print(ce)
    return event
