#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
env_settings="$(dirname $DIR)/environment.sh"
source "$env_settings"
if [ -z $HLSSTACK_SENTINELSTATEMACHINEEXPORT ];
then
    echo "HLSSTACK_SENTINELSTATEMACHINEEXPORT variable must be set"
    echo "try running 'source env.sh' from base directory"
    exit 1
fi
SM=$HLSSTACK_SENTINELSTATEMACHINEEXPORT

for i in `aws stepfunctions list-executions --state-machine-arn=${SM} --status-filter=RUNNING | jq .executions[].executionArn`
do
aws stepfunctions stop-execution --execution-arn ${i//\"}
done
