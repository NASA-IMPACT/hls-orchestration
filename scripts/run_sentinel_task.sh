#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
env_settings="$(dirname $DIR)/env.sh"
source "$env_settings"
granule=$1
random=$RANDOM
aws stepfunctions start-execution --state-machine-arn=$HLSSTACK_SENTINELSTATEMACHINEEXPORT --name ${random} --input "{\"granule\":\"${1}\"}"
