#!/bin/bash
jobqueue=$HLSSTACK_JOBQUEUEEXPORT
jobdefinition=$HLSSTACK_SENTINELJOBDEFINITION
outputbucket=$HLS_SENTINEL_BUCKET
inputbucket=$HLSSTACK_SENTINELINPUTEXPORT
command=sentinel.sh
granulelist=$1

# If multiple granules are in the granulelist, create a jobname without the granule unique id.
IFS=',' # commma is set as delimiter
jobname=$RANDOM

# Create Batch job definition override
overrides=$(cat <<EOF
{
		"command": ["$command"],
		"memory": 10000,
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
