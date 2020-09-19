#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
listresult=$(aws s3 ls hls-sentinel-validation-scenes)
scenes=$(echo "$listresult" | awk '{print $4}')
for scene in $scenes; do
  if [ "${scene:0:1}" != "_" ]; then
    granule=$(basename "$scene" .zip)
    sh "${DIR}/run_sentinel_granule_debug.sh" "$granule"
  fi
done
