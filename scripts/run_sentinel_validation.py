import argparse
import os
import random
import sys

import boto3

client = boto3.client("batch")
jobqueue = os.getenv("HLSSTACK_SENTINELJOBQUEUEEXPORT")
#  Short running granule
#  S2B_MSIL1C_20200806T173909_N0209_R098_T13TFN_20200806T195018

run_id = sys.argv[1]
input_bucket = sys.argv[2]
granules = sys.argv[3]

if len(sys.argv) >= 5:
    jobdefinition = sys.argv[4]
else:
    jobdefinition = os.getenv("HLSSTACK_SENTINELJOBDEFINITION")

if len(sys.argv) == 6:
    aux_dir = "/var/lasrc_aux/viirs"
else:
    aux_dir = "/var/lasrc_aux"


parser = argparse.ArgumentParser()
parser.add_argument("--run_id", help="Output bucket key")
parser.add_argument("--granules", help="Granule or list of granules")
parser.add_argument("--jobdefinition", help="Job Definition")
parser.add_argument("--use_viirs", help="Use viirs")

args = parser.parse_args()
run_id = args.run_id
granules = args.granules

if args.jobdefinition:
    jobdefinition = args.jobdefinition
else:
    jobdefinition = os.getenv("HLSSTACK_SENTINELJOBDEFINITION")
if args.use_viirs:
    aux_dir = "/var/lasrc_aux/viirs"
else:
    aux_dir = "/var/lasrc_aux"


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
                {"name": "LASRC_AUX_DIR", "value": aux_dir},
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
