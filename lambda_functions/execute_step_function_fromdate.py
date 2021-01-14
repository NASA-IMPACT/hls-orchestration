import os
import boto3
from typing import Dict
from botocore.errorfactory import ClientError
from datetime import datetime, timedelta


def handler(event: Dict, context: Dict):
    date_delta = int(os.getenv("DAYS_PRIOR"))
    state_machine = os.getenv("STATE_MACHINE")
    step_functions = boto3.client("stepfunctions")
    event_time = datetime.strptime(event["time"], '%Y-%m-%dT%H:%M:%SZ')
    fromdate = (event_time - timedelta(days=date_delta)).strftime('%d/%m/%Y')
    step_input = '{{"fromdate": "{0}"}}'.format(fromdate)
    print(step_input)
    try:
        step_functions.start_execution(
            stateMachineArn=state_machine,
            input=step_input,
        )
        return event
    except ClientError as ce:
        print(ce)
