#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
env_settings="$(dirname $DIR)/env.sh"
source "$env_settings"

jobqueue=$HLSSTACK_JOBQUEUEEXPORT
jobdefinition=$HLSSTACK_LANDSATJOBDEFINITION
outputbucket=$HLS_LANDSAT_INTERMEDIATE_OUTPUT_BUCKET
command=landsat.sh
granule=$1

# If multiple granules are in the granulelist, create a jobname without the granule unique id.
IFS=',' # commma is set as delimiter
jobname=$RANDOM

# Create Batch job definition override
overrides=$(cat <<EOF
{
    "command": ["df /var/scratch && $command"],
    "memory": 10000,
    "environment": [
      {
        "name": "GRANULE",
        "value": "$granule"
      },
      {
        "name": "OUTPUT_BUCKET",
        "value": "$outputbucket"
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
        "value": "hls-landsat-input"
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
