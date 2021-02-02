import os
import boto3
import random

from pathlib import Path
from hls_lambda_layer.landsat_scene_parser import landsat_parse_scene_id

client = boto3.client('batch')
jobqueue = os.getenv("HLSSTACK_LANDSATACJOBQUEUEEXPORT")
jobdefinition = os.getenv("HLSSTACK_LANDSATJOBDEFINITION")
inputbucket = "usgs-landsat"

path = Path(__file__).parent
landsat_validation = os.path.join(path, "landsat_validation.txt")
granule_list = open(landsat_validation, "r")

for scene in granule_list:
    scene_id = scene.rstrip()
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
                    "name": "DEBUG_BUCKET",
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
