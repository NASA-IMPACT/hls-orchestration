import os
import random
import sys
from pathlib import Path

import boto3
from hls_lambda_layer.landsat_scene_parser import landsat_parse_scene_id

client = boto3.client('batch')
jobqueue = os.getenv("HLSSTACK_LANDSATACJOBQUEUEEXPORT")
jobdefinition = os.getenv("HLSSTACK_LANDSATJOBDEFINITION")
inputbucket = "usgs-landsat"


def submit_job(scene_id):
    scene_meta = landsat_parse_scene_id(scene_id)
    s3_basepath = "collection02/level-1/standard/oli-tirs"
    year = scene_meta["acquisitionYear"]
    path = scene_meta["path"]
    row = scene_meta["row"]
    prefix = f"{s3_basepath}/{year}/{path}/{row}/{scene_id}"
    print(prefix)
    response = client.submit_job(
        jobName=str(random.randint(1, 200)),
        jobQueue=jobqueue,
        jobDefinition=jobdefinition,
        containerOverrides={
            'memory': 10000,
            'command': ['export && landsat.sh'],
            'environment': [
                {
                    "name": "GRANULE",
                    "value": scene_id
                },
                {
                    "name": "PREFIX",
                    "value": prefix
                },
                {
                    "name": "LASRC_AUX_DIR",
                    "value": "/var/lasrc_aux"
                },
                {
                    "name": "OUTPUT_BUCKET",
                    "value": "hls-debug-output"
                },
                {
                    "name": "INPUT_BUCKET",
                    "value": inputbucket
                },
                {
                    "name": "OMP_NUM_THREADS",
                    "value": "2"
                },
                {
                    "name": "REPLACE_EXISTING",
                    "value": "replace"
                },
            ],
        }
    )
    print(response)


if len(sys.argv) > 1:
    submit_job(sys.argv[1])
else:
    path = Path(__file__).parent
    landsat_validation = os.path.join(path, "landsat_validation.txt")
    granule_list = open(landsat_validation, "r")
    for scene in granule_list:
        scene_id = scene.rstrip()
        submit_job(scene_id)
