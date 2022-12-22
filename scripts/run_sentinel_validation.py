import os
import random
import sys

import boto3

client = boto3.client("batch")
jobqueue = os.getenv("HLSSTACK_SENTINELJOBQUEUEEXPORT")
jobdefinition = os.getenv("HLSSTACK_SENTINELJOBDEFINITION")
#  Short running granule
#  S2B_MSIL1C_20200806T173909_N0209_R098_T13TFN_20200806T195018

run_id = sys.argv[1]
input_bucket = sys.argv[2]
granules = sys.argv[3]


def submit_job(granule_id):
    response = client.submit_job(
        jobName=str(random.randint(1, 1000)),
        jobQueue=jobqueue,
        jobDefinition=jobdefinition,
        containerOverrides={
            "command": ["export && sentinel.sh"],
            "environment": [
                {"name": "GRANULE_LIST", "value": granule_id},
                {"name": "INPUT_BUCKET", "value": input_bucket},
                {"name": "LASRC_AUX_DIR", "value": "/var/lasrc_aux"},
                {"name": "DEBUG_BUCKET", "value": f"hls-debug-output/{run_id}"},
                {"name": "OMP_NUM_THREADS", "value": "2"},
                {"name": "REPLACE_EXISTING", "value": "replace"},
                {
                    "name": "GCC_ROLE_ARN",
                    "value": "arn:aws:iam::611670965994:role/hls-gcc-xaccount-s3-access",
                },
            ],
        },
    )
    print(response)


if os.path.isfile(granules):
    scenes = open(granules, "r").read().splitlines()
    for scene in scenes:
        granule_id = scene.split(".")[0]
        submit_job(granule_id)
else:
    submit_job(granules)
