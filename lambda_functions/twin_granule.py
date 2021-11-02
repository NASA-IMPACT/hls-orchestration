"""
HLS: Check if Twin Granule Exists
"""
import os
import re
from datetime import date
from typing import Dict

import boto3
from botocore.errorfactory import ClientError

s3 = boto3.client("s3")
bucket = os.getenv("SENTINEL_INPUT_BUCKET", None)
print(bucket)
if bucket is None:
    raise Exception("No Input Bucket set")


def handler(event: Dict, context: Dict):
    """AWS Lambda handler."""
    granule = event.get("granule")
    prefix = granule[0:-6]
    print(prefix)
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix,)
    print(response)
    granules = []
    contents = response["Contents"]
    for obj in contents:
        granules.append(obj["Key"][0:-4])

    granule_str = ",".join(granules)

    output = {
        "granule": granule_str,
    }
    return output
