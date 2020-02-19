"""
HLS: LaSRC LAADS Auxilary Data Available

Check if LaSRC LAADS Auxiliary Data is available
Takes a single date parameter that is parsed with the following patterns
date as yyyy-mm-dd
doy as yyyydoy
landsat as LC08_L1TP_170071_20190303_20190309_01_T1
sentinel as S2B_MSIL1C_20190301T075849_N0207_R035_T35HKD_20190301T121820
"""
from typing import Dict
import os
import re
import boto3
from botocore.errorfactory import ClientError
from datetime import date
import json

s3 = boto3.client("s3")
bucket = os.getenv("LAADS_BUCKET", None)
if bucket is None:
    raise Exception("No Bucket set")


def key_exists(bucket: str, key: str):
    try:
        s3.head_object(Bucket=bucket, Key=key)
    except ClientError as e:
        print(e)
        if e.response["Error"]["Code"] == "404":
            return False
    return True


def getyyyydoy(date_str: str):
    # Setup regular expressions for getting date
    dmy = re.compile("(20[0-9][0-9])-?([0-9][0-9])-?([0-9][0-9])")
    ydoy = re.compile("(20[0-9][0-9])-?([0-9][0-9][0-9])$")
    matches = dmy.search(date_str)
    if matches is not None:
        year = int(matches[1])
        month = int(matches[2])
        day = int(matches[3])
        d = date(year, month, day)
        return d.strftime("%Y%j"), str(year)
    else:
        matches = ydoy.search(date_str)
        year = matches[1]
        doy = matches[2]
        print(doy)
        return f"{year}{doy}", str(year)


def handler(event: Dict, context: Dict):
    """AWS Lambda handler."""
    # Get date from direct call or from query parameters via gateway call

    date_str = event.get("date", None)
    if date_str is None:
        date_str = event.get("granule")
    if event.get("queryStringParameters") is not None:
        params = event.get("queryStringParameters")
    if date_str is None:
        date_str = params.get("date")
    if date_str is None:
        date_str = params.get("granule")

    if date_str is None:
        raise Exception("Missing Date Parameter")

    ydoy, year = getyyyydoy(date_str)
    key = f"lasrc_aux/LADS/{year}/L8ANC{ydoy}.hdf_fused"
    print(f"------{bucket}    {key} ------")
    exists = key_exists(bucket, key)
    output = {
        "granule": date_str,
        "year": year,
        "doy": ydoy,
        "bucket": bucket,
        "key": key,
        "available": False,
    }
    if exists:
        output["available"] = True
        return output
    return output
