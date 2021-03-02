import pytest
import json
from unittest.mock import patch
from lambda_functions.execute_landsat_step_function import handler


@patch(
    "lambda_functions.execute_landsat_step_function.boto3.client"
)
def test_handler(client):
    """Test handler."""

    scene_meta = {
        "sensor": "C",
        "satellite": "08",
        "processingCorrectionLevel": "L1GT",
        "path": "127",
        "row": "010",
        "acquisitionYear": "2020",
        "acquisitionMonth": "05",
        "acquisitionDay": "27",
        "processingYear": "2020",
        "processingMonth": "05",
        "processingDay": "27",
        "collectionNumber": "01",
        "collectionCategory": "RT",
        "scene": "LC08_L1GT_127010_20200527_20200527_01_RT",
        "date": "2020-05-27",
        "scheme": "s3",
        "bucket": "usgs-landsat",
        "prefix": "collection02/level-1/standard/oli-tirs/LC08_L1GT_127010_20200527_20200527_01_RT",
    }
    expected_input = json.dumps(scene_meta)
    start_execution_response = {"executionArn": "arn", "startDate": 10}

    message = {
        "Records": [
            {
                "s3": {
                    "bucket": {
                        "name": "usgs-landsat"
                    },
                    "object": {
                        "key": "collection02/level-1/standard/oli-tirs/LC08_L1GT_127010_20200527_20200527_01_RT/index.html"
                    }
                }
            }
        ]
    }
    message = json.dumps(message)
    event = {
        "Records": [
            {
                "Sns": {
                    "Message": message
                }
            }
        ]
    }

    client.return_value.start_execution.return_value = start_execution_response
    handler(event, {})
    args, kwargs = client.return_value.start_execution.call_args
    assert kwargs["input"] == expected_input


@patch(
    "lambda_functions.execute_landsat_step_function.boto3.client"
)
def test_handler_non_RT(client):
    """Test handler."""
    message = {
        "Records": [
            {
                "s3": {
                    "bucket": {
                        "name": "usgs-landsat"
                    },
                    "object": {
                        "key":
                        "collection02/level-1/standard/oli-tirs/LC08_L1GT_127010_20200527_20200527_01_T1/index.html"
                    }
                }
            }
        ]
    }
    message = json.dumps(message)
    event = {
        "Records": [
            {
                "Sns": {
                    "Message": message
                }
            }
        ]
    }
    handler(event, {})
    client.return_value.start_execution.assert_not_called()
