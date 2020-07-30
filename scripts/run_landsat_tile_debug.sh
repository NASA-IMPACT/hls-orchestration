#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
env_settings="$(dirname $DIR)/env.sh"
source "$env_settings"

jobqueue=$HLSSTACK_JOBQUEUEEXPORT
jobdefinition=$HLSSTACK_LANDSATTILEJOBDEFINITION
inputbucket=$HLSSTACK_LANDSATINTERMEDIATEOUTPUT
command=landsat-tile.sh
pathrowlist=$1
date=$2
mgrs=$3
landsat_path=$4
mgrs_ulx=$5
mgrs_uly=$6

# If multiple granules are in the granulelist, create a jobname without the granule unique id.
IFS=',' # commma is set as delimiter
jobname=$RANDOM

# Create Batch job definition override
overrides=$(cat <<EOF
{
    "command": ["df /var/scratch && $command"],
    "memory": 15000,
    "environment": [
      {
        "name": "PATHROW_LIST",
        "value": "$pathrowlist"
      },
      {
        "name": "INPUT_BUCKET",
        "value": "$inputbucket"
      },
      {
        "name": "DATE",
        "value": "$date"
      },
      {
        "name": "MGRS",
        "value": "$mgrs"
      },
      {
        "name": "LANDSAT_PATH",
        "value": "$landsat_path"
      },
      {
        "name": "MGRS_ULX",
        "value": "$mgrs_ulx"
      },
      {
        "name": "MGRS_ULY",
        "value": "$mgrs_uly"
      },
      {
        "name": "DEBUG_BUCKET",
        "value": "hls-debug-output"
      }
    ]
}
EOF
)
echo "$overrides" > ./overrides.json

# Submit the job
aws batch submit-job --container-overrides file://overrides.json --job-definition "$jobdefinition" \
--job-name "$jobname"  --job-queue "$jobqueue"
rm ./overrides.json
