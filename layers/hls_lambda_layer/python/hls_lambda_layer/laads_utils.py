"""
HLS: LaSRC LAADS Auxiliary Data utilities

Shared helpers for checking whether LAADS auxiliary data is present in S3.
Used by both the per-granule availability checker (laads_available Lambda)
and the scheduled availability alerter (laads_alert Lambda).
"""

import re
from datetime import date

import boto3
from botocore.exceptions import ClientError

s3 = boto3.client("s3")

_DMY_RE = re.compile("(20[0-9][0-9])-?([0-9][0-9])-?([0-9][0-9])")
_YDOY_RE = re.compile("(20[0-9][0-9])-?([0-9][0-9][0-9])$")


def getyyyydoy(date_str: str) -> tuple[str, str]:
    """Parse a date string into (yyyydoy, year).

    Accepts:
      - yyyy-mm-dd
      - yyyydoy
      - Landsat scene ID  (LC08_L1TP_170071_20190303_...)
      - Sentinel scene ID (S2B_MSIL1C_20190301T075849_...)
    """
    matches = _DMY_RE.search(date_str)
    if matches is not None:
        year = int(matches[1])
        month = int(matches[2])
        day = int(matches[3])
        d = date(year, month, day)
        return d.strftime("%Y%j"), str(year)
    else:
        matches = _YDOY_RE.search(date_str)
        year = matches[1]
        doy = matches[2]
        return f"{year}{doy}", str(year)


def key_pattern_exists(bucket: str, key_pattern: str) -> bool:
    """Return True if any S3 objects exist under the given key prefix."""
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=key_pattern)
        return "Contents" in response
    except ClientError as e:
        print(e)
        return False


def check_laads_for_date(bucket: str, date_str: str) -> tuple[bool, str]:
    """Check whether LAADS auxiliary data exists in S3 for the given date.

    Returns:
        (available, ydoy) where available is True if either the VJ or VNP
        auxiliary file prefix exists, and ydoy is the resolved year-doy string.
    """
    ydoy, year = getyyyydoy(date_str)
    vj_pattern = f"lasrc_aux/LADS/{year}/VJ104ANC.A{ydoy}"
    vnp_pattern = f"lasrc_aux/LADS/{year}/VNP04ANC.A{ydoy}"
    available = key_pattern_exists(bucket, vj_pattern) or key_pattern_exists(
        bucket, vnp_pattern
    )
    return available, ydoy
