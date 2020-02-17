#!/bin/bash
granule=$1
aws stepfunctions start-execution --state-machine-arn=$STATE_MACHINE --name sentinel_step_${1} --input "{\"granule\":\"${1}\"}"
