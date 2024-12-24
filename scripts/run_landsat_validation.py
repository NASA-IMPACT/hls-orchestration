import argparse
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

tile_jobqueue = os.getenv("HLSSTACK_LANDSATTILEJOBQUEUEEXPORT")
# tile_jobdefinition = os.getenv("HLSSTACK_LANDSATTILEJOBDEFINITION")
tile_jobdefinition = "arn:aws:batch:us-west-2:018923174646:job-definition/LandsatTaskBatchJob1274-673e2c2a2411740:6"
inputbucket = "usgs-landsat"
s3_basepath = "collection02/level-1/standard/oli-tirs"

parser = argparse.ArgumentParser()
parser.add_argument("--run_id", help="Output bucket key")
parser.add_argument("--granules", help="Granule or list of granules")
parser.add_argument("--ignore", help="Upstream Landsat granules to ignore")
parser.add_argument("--ac_jobdefinition", help="AC Job Definition")
parser.add_argument("--use_viirs", help="Use viirs")

args = parser.parse_args()
run_id = args.run_id
granules = args.granules

if args.ignore:
    ignore = args.ignore
else:
    ignore = []
if args.ac_jobdefinition:
    ac_jobdefinition = args.ac_jobdefinition
else:
    ac_jobdefinition = os.getenv("HLSSTACK_LANDSATJOBDEFINITION")
if args.use_viirs:
    aux_dir = "/var/lasrc_aux/viirs"
else:
    aux_dir = "/var/lasrc_aux"

ac_jobids = {}


def submit_ac_job(scene_id, path, row, year, run_id):
    prefix = f"{s3_basepath}/{year}/{path}/{row}/{scene_id}"
    print(ac_jobdefinition)
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
                {"name": "LASRC_AUX_DIR", "value": aux_dir},
                {"name": "OUTPUT_BUCKET", "value": f"hls-debug-output/{run_id}"},
                {"name": "INPUT_BUCKET", "value": inputbucket},
                {"name": "OMP_NUM_THREADS", "value": "2"},
                {"name": "REPLACE_EXISTING", "value": "replace"},
                {"name": "USE_ORIG_AERO", "value": "--use_orig_aero"},
            ],
        },
    )
    return response


def submit_tile_job(
    valid_pathrows,
    mgrs_tile,
    mgrs_result,
    landsat_path,
    ac_job_dependencies,
    date,
    run_id,
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


def process_mgrs(mgrs_tile, date, ignore, run_id):
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
                if scene_id not in ignore:
                    print(scene_id)
                    valid_pathrows.append(pathrow)
                    date_pathrow = f"{date}_{pathrow}"
                    if date_pathrow not in ac_jobids:
                        batch_response = submit_ac_job(
                            scene_id, path, row, year, run_id
                        )
                        ac_jobids[date_pathrow] = batch_response.get("jobId")
                    ac_job_dependencies.append(
                        {"jobId": ac_jobids[date_pathrow], "type": "N_TO_N"}
                    )
                else:
                    print(f"Skipping {scene_id}")

    print(valid_pathrows)
    landsat_path = valid_pathrows[0][:3]
    submit_tile_job(
        valid_pathrows,
        mgrs_tile,
        mgrs_result,
        landsat_path,
        ac_job_dependencies,
        date,
        run_id,
    )


directory = "/Users/seanharkins/Downloads/missing_S30/missing/"
files = os.listdir(directory)

for file in files[35:40]:
    print(file)
    file_path = os.path.join(directory, file)

    if os.path.isfile(file_path):
        scenes = open(file_path, "r").read().splitlines()
        for line in scenes:
            components = line.split(",")
            # path = components[0][0:3]
            # row = components[0][3:6]
            mgrs = components[0]
            date = components[1]
            print(mgrs, date)
            # result = handler.handler({"path": path, "row": row}, {})
            # process_mgrs(result["mgrs"][0], date)
            id = file.split(".")[0]
            process_mgrs(mgrs, date, ignore, f"hansen/{id}")

    else:
        components = granules.split("_")
        path = components[2][0:3]
        row = components[2][3:6]
        date = components[3]
        result = handler.handler({"path": path, "row": row}, {})
        process_mgrs(result["mgrs"][0], date, ignore)
