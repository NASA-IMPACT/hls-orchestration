import os
import boto3
from pathlib import Path
from typing import Dict
from botocore.errorfactory import ClientError
from random import randint

step_functions = boto3.client('stepfunctions')
state_machine = os.getenv("STATE_MACHINE")


def handler(event: Dict, context: Dict):
    prefix = randint(100, 999)
    # print(event['detail']['requestParameters']['key'])
    # key = event['detail']['requestParameters']['key']
    print(event['Records'][0]['s3']['object']['key'])
    key = event['Records'][0]['s3']['object']['key']
    keyroot = Path(key).stem
    try:
        step_functions.start_execution(
            stateMachineArn=state_machine,
            name=f"{prefix}_{keyroot}",
            input="{\"granule\": \"" + keyroot + "\"}"
        )
    except ClientError as e:
        print(e)

    return event
