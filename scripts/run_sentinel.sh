#!/bin/bash
export STATE_MACHINE=$HLSSTACK_SENTI
granule=$1
aws stepfunctions start-execution --state-machine-arn=$STATE_MACHINE --name ${1}_$(date '+%Y%m%dT%H%M%S') --input "{\"granule\":\"${1}\"}"
