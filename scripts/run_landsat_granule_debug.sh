#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
env_settings="$(dirname $DIR)/environment.sh"
source "$env_settings"

jobqueue=$HLSSTACK_LANDSATACJOBQUEUEEXPORT
jobdefinition=$HLSSTACK_LANDSATJOBDEFINITION
outputbucket=$HLS_LANDSAT_INTERMEDIATE_OUTPUT_BUCKET
gibsoutputbucket=$HLS_GIBS_OUTPUT_BUCKET
command=landsat.sh
granule=$1
prefix=$2
inputbucket=$3

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
        "name": "PREFIX",
        "value": "$prefix"
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
        "value": "$inputbucket"
      },
      {
        "name": "GIBS_OUTPUT_BUCKET",
        "value": "$gibsoutputbucket"
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
