"""
HLS: LaSRC LAADS Auxilary Data Available

Check if LaSRC LAADS Auxiliary Data is available
Takes a single date parameter that is parsed with the following patterns
date as yyyy-mm-dd
doy as yyyydoy
landsat as LC08_L1TP_170071_20190303_20190309_01_T1
sentinel as S2B_MSIL1C_20190301T075849_N0207_R035_T35HKD_20190301T121820
"""
import os
import re
from datetime import date
from typing import Dict

import boto3
from botocore.errorfactory import ClientError

s3 = boto3.client("s3")


def key_pattern_exists(bucket: str, key_pattern: str):
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=key_pattern)
        if "Contents" in response:
            return True
        else:
            return False
    except ClientError as e:
        print(e)


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

    if date_str is None:
        raise Exception("Missing Date Parameter")

    bucket = os.getenv("LAADS_BUCKET", None)
    if bucket is None:
        raise Exception("No Bucket set")
    ydoy, year = getyyyydoy(date_str)
    vj_pattern = f"lasrc_aux/LADS/{year}/VJ104ANC.A{ydoy}"
    print(f"------{bucket}    {vj_pattern} ------")
    vj_exists = key_pattern_exists(bucket, vj_pattern)
    vnp_pattern = f"lasrc_aux/LADS/{year}/VNP04ANC.A{ydoy}"
    vnp_exists = key_pattern_exists(bucket, vnp_pattern)
    if vj_exists or vnp_exists:
        exists = True
    else:
        exists = False
    output = {
        "granule": date_str,
        "year": year,
        "doy": ydoy,
        "bucket": bucket,
        "pattern": f"{vj_pattern} {vnp_pattern}",
        "available": False,
    }
    if exists:
        output["available"] = True
        return output
    return output
