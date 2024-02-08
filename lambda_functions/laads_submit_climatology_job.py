import datetime
import json
import os

import boto3

batch_client = boto3.client("batch")


jobQueue = os.getenv("JOB_QUEUE")
jobDefinition = os.getenv("JOB_DEFINITION")
lasrc_aux = os.getenv("LASRC_AUX_DIR")
laads_token = os.getenv("LAADS_TOKEN")
laads_bucket = os.getenv("LAADS_BUCKET")


def handler(event, context):
    current_date = datetime.datetime.now()
    response = batch_client.submit_job(
        jobName="laads_cron",
        jobQueue=jobQueue,
        jobDefinition=jobDefinition,
        containerOverrides={
            "environment": [
                {"name": "LASRC_AUX_DIR", "value": lasrc_aux},
                {"name": "LAADS_TOKEN", "value": laads_token},
                {"name": "LAADS_BUCKET", "value": laads_bucket},
                {"name": "CLIM_YEAR", "value": str(current_date.year)},
                {"name": "CLIM_MONTH", "value": str(current_date.month)},
            ],
            "command": ["./usr/local/climatologies.sh"],
        },
    )
    return response
