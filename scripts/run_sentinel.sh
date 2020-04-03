#!/bin/bash
granule=$1
random=$RANDOM
aws stepfunctions start-execution --state-machine-arn=$HLSSTACK_SENTINELSTATEMACHINEEXPORT --name ${random} --input "{\"granule\":\"${1}\"}"
