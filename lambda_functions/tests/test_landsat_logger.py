import pytest
import os
import json
from unittest.mock import patch
from lambda_functions.landsat_logger import handler


@patch("lambda_functions.landsat_logger.rds_client")
def test_handler(client):
    """Test handler."""

    event = {
        "path": "202",
        "row": "114",
        "date": "2021-03-08",
        "scene": "LC08_L1GT_202114_20210308_20210308_02_RT"
    }
    client.execute_statement.return_value = {}
    handler(event, {})
    args, kwargs = client.execute_statement.call_args
    acquisition = {
        "name": "acquisition",
        "value": {
            "stringValue": event["date"]
        }
    }
    assert acquisition in kwargs["parameters"]
    scene_id = {
        "name": "scene_id",
        "value": {
            "stringValue": event["scene"]
        }
    }
    assert scene_id in kwargs["parameters"]
    # Initial run_count should be 0.
    run_count = {
        "name": "run_count",
        "value": {
            "longValue": 0
        }
    }
    assert run_count in kwargs["parameters"]


@patch.dict(os.environ, {"HISTORIC": "historic"})
@patch("lambda_functions.landsat_logger.rds_client")
def test_handler_historic(client):
    """Test handler."""

    event = {
        "path": "202",
        "row": "114",
        "date": "2021-03-08",
        "scene": "LC08_L1GT_202114_20210308_20210308_02_RT"
    }
    client.execute_statement.return_value = {}
    handler(event, {})
    args, kwargs = client.execute_statement.call_args

    historic = {
        "name": "historic",
        "value": {
            "booleanValue": True
        }
    }
    assert historic in kwargs["parameters"]
