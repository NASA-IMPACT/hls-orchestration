#!/bin/bash
for file in `cat sentinel_test_granules.txt`; do echo ${file} && ./run_sentinel.sh $file; done

