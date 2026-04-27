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

from hls_lambda_layer.laads_utils import getyyyydoy, key_pattern_exists


def handler(event: dict, context: dict):
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
    vnp_pattern = f"lasrc_aux/LADS/{year}/VNP04ANC.A{ydoy}"
    print(f"------{bucket}    {vj_pattern} ------")

    available = key_pattern_exists(bucket, vj_pattern) or key_pattern_exists(
        bucket, vnp_pattern
    )
    return {
        "granule": date_str,
        "year": year,
        "doy": ydoy,
        "bucket": bucket,
        "pattern": f"{vj_pattern} {vnp_pattern}",
        "available": available,
    }
