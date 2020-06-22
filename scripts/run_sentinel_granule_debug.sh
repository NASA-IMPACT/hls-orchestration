#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
env_settings="$(dirname $DIR)/env.sh"
source "$env_settings"

jobqueue=$HLSSTACK_JOBQUEUEEXPORT
jobdefinition=$HLSSTACK_SENTINELJOBDEFINITION
outputbucket=$HLS_SENTINEL_OUTPUT_BUCKET
inputbucket=$HLSSTACK_SENTINELINPUTEXPORT
gibsbucket=$HLS_GIBS_INTERMEDIATE_OUTPUT_BUCKET
command=sentinel.sh
granulelist=$1

# If multiple granules are in the granulelist, create a jobname without the granule unique id.
IFS=',' # commma is set as delimiter
jobname=$RANDOM

# Create Batch job definition override
overrides=$(cat <<EOF
{
    "command": ["df /var/scratch && $command"],
    "environment": [
      {
        "name": "GRANULE_LIST",
        "value": "$granulelist"
      },
      {
        "name": "OUTPUT_BUCKET",
        "value": "$outputbucket"
      },
      {
        "name": "INPUT_BUCKET",
        "value": "$inputbucket"
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
        "name": "GIBS_INTERMEDIATE_BUCKET",
        "value": "$gibsbucket"
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
