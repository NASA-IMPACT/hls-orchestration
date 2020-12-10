import pytest
import json
from unittest.mock import patch
from lambda_functions.usgs_landsat.index import handler

search_results = {
    "data": {
        "results": [
            {"summary": "scene: LC08_L1TP_138035_20201202_20201202_02_RT"}
        ]
    }
}

event = {
    "time": "2020-12-03T12:00:00Z"
}


@patch("lambda_functions.usgs_landsat.index.api")
@patch("lambda_functions.usgs_landsat.index.rds_client")
def test_handler_usgs(rds_client, api):
    api.login.return_value = {"data": "key"}
    api.search.return_value = search_results
    handler(event, {})
    api.login.assert_called()
    args, kwargs = api.search.call_args
    # Searches for previous day.
    assert kwargs["where"][20511] == "2020/12/02"

    args, kwargs = rds_client.batch_execute_statement.call_args
    parameter_set = [
        {"name": "path", "value": {"stringValue": "138"}},
        {"name": "row", "value": {"stringValue": "035"}},
        {"name": "acquisition", "value": {"stringValue": "2020-12-02"}},
        {"name": "scene_id", "value": {"stringValue": "LC08_L1TP_138035_20201202_20201202_02_RT"}},
    ]
    assert parameter_set in kwargs["parameterSets"]
