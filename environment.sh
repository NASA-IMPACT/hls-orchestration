#!/bin/bash

# Make sure that necessary executables are installed
for b in jq aws
do
    command -v $b >/dev/null 2>&1 || { echo >&2 "I require $b but it's not installed.  Aborting."; exit 1; }
done

# Set allexport mode, all variables defined in this block will get exported
set -a
# Name of the stack being created
: ${HLS_STACKNAME:=hls}


# Schedule to use for updating Laads data
HLS_LAADS_CRON="cron(0 0/12 * * ? *)"

# Bucket used for Sentinel output
HLS_SENTINEL_OUTPUT_BUCKET=hls-global

# Bucket used for Landsat output
HLS_LANDSAT_OUTPUT_BUCKET=hls-global

# Landsat SNS topic
HLS_LANDSAT_SNS_TOPIC=arn:aws:sns:us-west-2:274514004127:NewSceneHTML

# Bucket for merged GIBS tile output.
HLS_GIBS_OUTPUT_BUCKET=hls-browse-imagery

# Max vcpus for Batch compute environment
HLS_MAXV_CPUS=1000

# Replace existing output in S3 buckets.
HLS_REPLACE_EXISTING=true

# ssh keyname for use with Batch instance debugging.
HLS_SSH_KEYNAME=hls-mount

# end of allexport mode
set +a

# Set environment variables for all outputs set up in cloud formation
stack_info=$(aws cloudformation describe-stacks --stack-name ${HLS_STACKNAME} --output json)
if [[ "$stack_info" =~ "OutputKey" ]]; then
    l=$(echo "$stack_info" | jq ".Stacks[].Outputs | length")
    for ((i=0;i<$l;++i)); do
        key=$(echo "$stack_info" | jq ".Stacks[].Outputs[$i].OutputKey" | sed -e 's/^"//'  -e 's/"$//')
        keyupper=$(echo "$key" | awk '{print toupper($0)}')
        val=$(echo "$stack_info" | jq ".Stacks[].Outputs[$i].OutputValue" | sed -e 's/^"//'  -e 's/"$//')
        export "HLSSTACK_$keyupper"="$val"
    done
fi
