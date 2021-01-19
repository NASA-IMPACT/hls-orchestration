#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
env_settings="$(dirname $DIR)/environment.sh"
source "$env_settings"

jobqueue=$HLSSTACK_SENTINELJOBQUEUEEXPORT
jobdefinition=$HLSSTACK_SENTINELJOBDEFINITION
outputbucket=$HLS_SENTINEL_OUTPUT_BUCKET
# inputbucket=$HLSSTACK_SENTINELINPUTEXPORT
gibsbucket=$HLSSTACK_GIBSINTERMEDIATEOUTPUT
gibsoutputbucket=$HLS_GIBS_OUTPUT_BUCKET
outputbucket_role_arn=$HLS_SENTINEL_BUCKET_ROLE_ARN
command=sentinel.sh
granulelist=$1
inputbucket=$2

# If multiple granules are in the granulelist, create a jobname without the granule unique id.
IFS=',' # commma is set as delimiter
jobname=$RANDOM

# Create Batch job definition override
overrides=$(cat <<EOF
{
    "command": ["printenv && df /var/scratch && $command"],
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
        "name": "GIBS_INTERMEDIATE_BUCKET",
        "value": "$gibsbucket"
      },
      {
        "name": "GIBS_OUTPUT_BUCKET",
        "value": "$gibsoutputbucket"
      },
      {
        "name": "GCC_ROLE_ARN",
        "value": "$outputbucket_role_arn"
      },
      {
        "name": "DEBUG_BUCKET",
        "value": "hls-debug-output"
      },
      {
        "name": "OMP_NUM_THREADS",
        "value": "2"
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
