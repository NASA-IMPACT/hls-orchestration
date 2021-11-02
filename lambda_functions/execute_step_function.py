import os
from pathlib import Path
from random import randint
from typing import Dict

import boto3
from botocore.errorfactory import ClientError


def handler(event: Dict, context: Dict):
    state_machine = os.getenv("STATE_MACHINE")
    step_functions = boto3.client("stepfunctions")
    prefix = randint(100, 999)
    try:
        # print(event['detail']['requestParameters']['key'])
        # key = event['detail']['requestParameters']['key']
        print(event["Records"][0]["s3"]["object"]["key"])
        key = event["Records"][0]["s3"]["object"]["key"]
        keyroot = Path(key).stem
        try:
            step_functions.start_execution(
                stateMachineArn=state_machine,
                name=f"{prefix}_{keyroot}",
                input='{"granule": "' + keyroot + '"}',
            )
            return event
        except ClientError as ce:
            print(ce)

    except KeyError:
        print("Message body does not contain key")
