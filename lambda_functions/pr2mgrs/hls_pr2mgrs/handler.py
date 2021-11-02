"""
HLS: Landsat 8 PathRow to Sentinel 2 Tiles.

Find the L8 scenes that apparently overlap with the given S2 tileid,  based on
the pre-computed relationship between Sentinel-2 tile and Landsat pathrow.

ref: https://github.com/NASA-IMPACT/hls.v1.5/blob/d7fdaf2cc3745ce434f77fb0506b9eeb26acdc35/L8/sr_tile/script/run_sr_tile.sh#L126
"""
import os
from typing import Dict

# We put this outside the function so it can be cached
lookup_file = os.path.join(os.path.dirname(__file__), "data", "HLS.L8S2overlap.txt")
with open(lookup_file, "r") as f:
    lookupTable = list(map(lambda x: x.split(" "), f.read().splitlines()))


def handler(event: Dict, context: Dict):
    """AWS Lambda handler."""
    if event.get("row"):
        pathrow = f"{event['path']}{event['row']}"
        listS2 = list(filter(lambda x: x[0] == pathrow, lookupTable))
        # Do we want to raise an error when no grid is found ?
        mgrs = [s2[1] for s2 in listS2]
        mgrs_values = {"mgrs": mgrs, "count": len(mgrs)}
        return mgrs_values

    elif event.get("MGRS"):
        listL8 = list(filter(lambda x: x[1] == str(event.get("MGRS")), lookupTable))
        pathrows = [l8[0] for l8 in listL8]
        mgrs_ulx = None
        mgrs_uly = None
        if len(listL8) > 0:
            mgrs_ulx = listL8[0][2]
            mgrs_uly = listL8[0][3]
        if event.get("path"):
            pathrows = [
                pathrow
                for pathrow in pathrows
                if pathrow[0:3] == str(event.get("path"))
            ]
        # Do we want to raise an error when no grid is found ?
        pathrows_string = ",".join(pathrows)
        mgrs_metadata = {
            "pathrows": pathrows,
            "mgrs_ulx": mgrs_ulx,
            "mgrs_uly": mgrs_uly,
            "pathrows_string": pathrows_string,
        }
        return mgrs_metadata

    else:
        raise Exception("Missing PATHROW or MGRS")
