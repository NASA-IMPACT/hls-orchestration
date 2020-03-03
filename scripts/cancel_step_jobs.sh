#!/bin/bash
# Cancels any currently running Step Jobs
if [ -z $HLSSTACK_SENTINELSTATEMACHINEEXPORT ];
then
    echo "HLSSTACK_SENTINELSTATEMACHINEEXPORT variable must be set"
    echo "try running 'source env.sh'"
    exit 1
fi
SM=$HLSSTACK_SENTINELSTATEMACHINEEXPORT

for i in `aws stepfunctions list-executions --state-machine-arn=${SM} --status-filter=RUNNING | jq .executions[].executionArn`
do
aws stepfunctions stop-execution --execution-arn ${i//\"}
done