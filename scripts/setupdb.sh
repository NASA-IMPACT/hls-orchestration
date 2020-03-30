#!/bin/bash
aws lambda invoke --function-name=$HLSSTACK_SETUPDBEXPORT response.json
rm response.json
