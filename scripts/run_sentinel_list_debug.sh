#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
while read p; do
  sh ./run_sentinel_granule_debug.sh $p
done
