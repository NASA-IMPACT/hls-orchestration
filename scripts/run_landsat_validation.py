import itertools
import os
import random
import sys
from datetime import datetime
from pathlib import Path

import boto3

from lambda_functions.pr2mgrs.hls_pr2mgrs import handler

#  mgrs_tiles = ["29RPP", "29RQP", "29RQQ", "29SQT", "29SQU", "30STC", "30STD", "30SUD"]
#  date = "20210112"
#  mgrs_tiles = ["10SFE"]

s3_client = boto3.client("s3")
batch_client = boto3.client("batch")

ac_jobqueue = os.getenv("HLSSTACK_LANDSATACJOBQUEUEEXPORT")
ac_jobdefinition = os.getenv("HLSSTACK_LANDSATJOBDEFINITION")
tile_jobqueue = os.getenv("HLSSTACK_LANDSATTILEJOBQUEUEEXPORT")
tile_jobdefinition = os.getenv("HLSSTACK_LANDSATTILEJOBDEFINITION")
inputbucket = "usgs-landsat"
s3_basepath = "collection02/level-1/standard/oli-tirs"

run_id = sys.argv[1]
granules = sys.argv[2]

ac_jobids = {}


def submit_ac_job(scene_id, path, row, year):
    prefix = f"{s3_basepath}/{year}/{path}/{row}/{scene_id}"
    response = batch_client.submit_job(
        jobName=str(random.randint(1, 200)),
        jobQueue=ac_jobqueue,
        jobDefinition=ac_jobdefinition,
        containerOverrides={
            "memory": 10000,
            "command": ["export && landsat.sh"],
            "environment": [
                {"name": "GRANULE", "value": scene_id},
                {"name": "PREFIX", "value": prefix},
                {"name": "LASRC_AUX_DIR", "value": "/var/lasrc_aux"},
                {"name": "OUTPUT_BUCKET", "value": f"hls-debug-output/{run_id}"},
                {"name": "INPUT_BUCKET", "value": inputbucket},
                {"name": "OMP_NUM_THREADS", "value": "2"},
                {"name": "REPLACE_EXISTING", "value": "replace"},
            ],
        },
    )
    return response


def submit_tile_job(
    valid_pathrows, mgrs_tile, mgrs_result, landsat_path, ac_job_dependencies, date
):
    separated_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
    response = batch_client.submit_job(
        jobName=str(random.randint(1, 200)),
        jobQueue=tile_jobqueue,
        jobDefinition=tile_jobdefinition,
        dependsOn=ac_job_dependencies,
        containerOverrides={
            "memory": 10000,
            "command": ["export && landsat-tile.sh"],
            "environment": [
                {"name": "PATHROW_LIST", "value": ",".join(valid_pathrows)},
                {"name": "OUTPUT_BUCKET", "value": f"hls-debug-output/{run_id}"},
                {"name": "DEBUG_BUCKET", "value": f"hls-debug-output/{run_id}"},
                {"name": "INPUT_BUCKET", "value": f"hls-debug-output/{run_id}"},
                {"name": "DATE", "value": separated_date},
                {"name": "MGRS", "value": mgrs_tile},
                {"name": "LANDSAT_PATH", "value": landsat_path},
                {"name": "MGRS_ULX", "value": mgrs_result.get("mgrs_ulx")},
                {"name": "MGRS_ULY", "value": mgrs_result.get("mgrs_uly")},
            ],
        },
    )
    print(mgrs_tile)
    print(response.get("jobId"))
    return response


def process_mgrs(mgrs_tile, date):
    print(mgrs_tile)
    event = {"MGRS": mgrs_tile}
    mgrs_result = handler.handler(event, {})

    year = date[:4]

    ac_job_dependencies = []
    valid_pathrows = []

    for pathrow in mgrs_result["pathrows"]:
        path = pathrow[:3]
        row = pathrow[3:]
        prefix = f"{s3_basepath}/{year}/{path}/{row}/"
        list_result = s3_client.list_objects_v2(
            Bucket=inputbucket, Prefix=prefix, RequestPayer="requester", Delimiter="/"
        )
        common_prefixes = list_result.get("CommonPrefixes")
        if common_prefixes:
            updated_key = [
                prefix["Prefix"]
                for prefix in common_prefixes
                if prefix["Prefix"].split("_")[3] == date
            ]
            if len(updated_key) > 0:
                scene_id = updated_key[0].split("/")[-2]
                print(scene_id)
                valid_pathrows.append(pathrow)
                date_pathrow = f"{date}_{pathrow}"
                if date_pathrow not in ac_jobids:
                    batch_response = submit_ac_job(scene_id, path, row, year)
                    ac_jobids[date_pathrow] = batch_response.get("jobId")
                ac_job_dependencies.append(
                    {"jobId": ac_jobids[date_pathrow], "type": "N_TO_N"}
                )

    landsat_path = valid_pathrows[0][:3]
    print(valid_pathrows)
    submit_tile_job(
        valid_pathrows, mgrs_tile, mgrs_result, landsat_path, ac_job_dependencies, date
    )


if os.path.isfile(granules):
    scenes = open(granules, "r").read().splitlines()
    for line in scenes:
        components = line.split("_")
        tile = components[5][1:]
        date = components[2][0:8]
        process_mgrs(tile, date)
else:
    components = granules.split("_")
    tile = components[5][1:]
    date = components[2][0:8]
    process_mgrs(tile, date)
