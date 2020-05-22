"""
HLS: Landsat 8 PathRow to Sentinel 2 Tiles.

Find the L8 scenes that apparently overlap with the given S2 tileid,  based on
the pre-computed relationship between Sentinel-2 tile and Landsat pathrow.

ref: https://github.com/NASA-IMPACT/hls.v1.5/blob/d7fdaf2cc3745ce434f77fb0506b9eeb26acdc35/L8/sr_tile/script/run_sr_tile.sh#L126
"""
from typing import Dict

import os

# We put this outside the function so it can be cached
lookup_file = os.path.join(os.path.dirname(__file__), "data", "L8S2overlap.txt")
with open(lookup_file, "r") as f:
    lookupTable = list(map(lambda x: x.split(" "), f.read().splitlines()))


def handler(event: Dict, context: Dict):
    """AWS Lambda handler."""
    if event.get("PATHROW"):
        listS2 = list(filter(lambda x: x[0] == str(event.get("PATHROW")), lookupTable))
        # Do we want to raise an error when no grid is found ?
        return [s2[1] for s2 in listS2]

    elif event.get("MGRS"):
        listL8 = list(filter(lambda x: x[1] == str(event.get("MGRS")), lookupTable))
        pathrows = [l8[0] for l8 in listL8]
        if event.get("PATH"):
            pathrows = [
                pathrow
                for pathrow in pathrows
                if pathrow[0:3] == str(event.get("PATH"))
            ]
        # Do we want to raise an error when no grid is found ?
        return pathrows

    else:
        raise Exception("Missing PATHROW or MGRS")
