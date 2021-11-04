import os
import random
import sys

import boto3

client = boto3.client("stepfunctions")
s3 = boto3.resource("s3")
input_bucket = "hls-sentinel-validation-scenes"
bucket = s3.Bucket(input_bucket)
statemachinearn = os.getenv("HLSSTACK_SENTINELSTATEMACHINEEXPORT")


def submit_task(granule_id):
    response = client.start_execution(
        stateMachineArn=statemachinearn,
        name=str(random.randint(1, 10000)),
        input=f'{{"granule":"{granule_id}"}}',
    )
    print(response)


if len(sys.argv) > 1:
    submit_task(sys.argv[1])
else:
    granule_list = bucket.objects.filter(Delimiter="/", Prefix="cloud_free_google/")
    for granule in granule_list:
        granule_id = os.path.splitext(granule.key.split("/")[1])[0]
        submit_task(granule_id)
