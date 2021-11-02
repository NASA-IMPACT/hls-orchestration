import json
import os
from unittest.mock import call, patch

import pytest

from lambda_functions.process_landsat_ac_errors import convert_records, handler


def test_convert_records():
    record = [
        {"longValue": 1},
        {"stringValue": "LC08_L1TP_111070_20210701_20210701_02_RT"}
    ]
    converted = convert_records(record)
    assert converted["prefix"] == "collection02/level-1/standard/oli-tirs/2021/111/070/LC08_L1TP_111070_20210701_20210701_02_RT"
    assert converted["id"] == 1


@patch("lambda_functions.process_landsat_ac_errors.step_function_client")
@patch("lambda_functions.process_landsat_ac_errors.rds_client")
@patch.dict(os.environ, {"RETRY_LIMIT": "3"})
def test_handler_chunking(rds_client, step_function_client):
    records = [
        [
            {"longValue": 1},
            {"stringValue": "LC08_L1TP_111070_20210701_20210701_02_RT"},
        ] for i in range(350)
    ]
    response = {
        "records": records
    }
    rds_client.execute_statement.return_value = response
    handler({}, {})
    assert step_function_client.start_execution.call_count == 4
    args, kwargs = step_function_client.start_execution.call_args_list[3]
    input = json.loads(kwargs["input"])
    assert input["errors"][0] == {
        "id": 1,
        "scene_id": "LC08_L1TP_111070_20210701_20210701_02_RT",
        "scheme": "s3",
        "bucket": "usgs-landsat",
        "prefix": "collection02/level-1/standard/oli-tirs/2021/111/070/LC08_L1TP_111070_20210701_20210701_02_RT",
        "sensor": "C",
        "satellite": "08",
        "processingCorrectionLevel": "L1TP",
        "path": "111",
        "row": "070",
        "acquisitionYear": "2021",
        "acquisitionMonth": "07",
        "acquisitionDay": "01",
        "processingYear": "2021",
        "processingMonth": "07",
        "processingDay": "01",
        "collectionNumber": "02",
        "collectionCategory": "RT",
        "scene": "LC08_L1TP_111070_20210701_20210701_02_RT",
        "date": "2021-07-01"
    }

    args, kwargs = rds_client.execute_statement.call_args
    retry_limit = {"name": "retry_limit", "value": {"longValue": 3}}
    assert retry_limit in kwargs["parameters"]
