import os
import random

import boto3

client = boto3.client('batch')
jobqueue = os.getenv("HLSSTACK_LANDSATTILEJOBQUEUEEXPORT")
jobdefinition = os.getenv("HLSSTACK_LANDSATTILEJOBDEFINITION")


response = client.submit_job(
    jobName=str(random.randint(1, 200)),
    jobQueue=jobqueue,
    jobDefinition=jobdefinition,
    containerOverrides={
        'memory': 10000,
        'command': ['export && landsat-tile.sh'],
        'environment': [
            {
                "name": "PATHROW_LIST",
                "value": "003067"
            },
            {
                "name": "OUTPUT_BUCKET",
                "value": "hls-debug-output"
            },
            {
                "name": "DEBUG_BUCKET",
                "value": "hls-debug-output"
            },
            {
                "name": "INPUT_BUCKET",
                "value": "hls-debug-output"
            },
            {
                "name": "DATE",
                "value": "2020-08-26"
            },
            {
                "name": "MGRS",
                "value": "19LBJ"
            },
            {
                "name": "LANDSAT_PATH",
                "value": "003"
            },
            {
                "name": "MGRS_ULX",
                "value": "199980"
            },
            {
                "name": "MGRS_ULY",
                "value": "8900020"
            },
        ],
    }
)
print(response)
