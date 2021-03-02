import os
import boto3
import json
from typing import Dict
from botocore.errorfactory import ClientError
from hls_lambda_layer.landsat_scene_parser import landsat_parse_scene_id


def handler(event: Dict, context: Dict):
    print(event)
    step_functions = boto3.client("stepfunctions")
    state_machine = os.getenv("STATE_MACHINE")
    try:
        message = event["Records"][0]["Sns"]["Message"]
        parsed_message = json.loads(message)
        key = parsed_message["Records"][0]["s3"]["object"]["key"]
        bucket_name = parsed_message["Records"][0]["s3"]["bucket"]["name"]

    except KeyError:
        print("Message body does not contain key")

    head, tail = os.path.split(key)
    scene_id = key.split("/")[-2]
    scene_meta = landsat_parse_scene_id(scene_id)
    scene_meta["scheme"] = "s3"
    scene_meta["bucket"] = bucket_name
    scene_meta["prefix"] = head
    print(scene_meta)
    # Skip unless real-time (RT) collection
    if scene_meta["collectionCategory"] == "RT":
        try:
            input = json.dumps(scene_meta)
            step_functions.start_execution(
                stateMachineArn=state_machine,
                name=scene_meta['scene'],
                input=input,
            )
        except ClientError as ce:
            print(ce)
    return event
