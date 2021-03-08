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
        "path": "197",
        "row": "119",
        "acquisitionYear": "2021",
        "acquisitionMonth": "02",
        "acquisitionDay": "01",
        "processingYear": "2021",
        "processingMonth": "03",
        "processingDay": "02",
        "collectionNumber": "02",
        "collectionCategory": "RT",
        "scene":"LC08_L1GT_197119_20210201_20210302_02_RT",
        "date": "2021-02-01",
        "scheme": "s3",
        "bucket": "usgs-landsat",
        "prefix": "collection02/level-1/standard/oli-tirs/2021/197/119/LC08_L1GT_197119_20210201_20210302_02_RT"
    }
    expected_input = json.dumps(scene_meta)
    start_execution_response = {"executionArn": "arn", "startDate": 10}
    message = {
        "landsat_product_id": "LC08_L1GT_197119_20210201_20210302_02_RT",
        "s3_location": "s3://usgs-landsat/collection02/level-1/standard/oli-tirs/2021/197/119/LC08_L1GT_197119_20210201_20210302_02_RT/"
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
        "landsat_product_id": "LC08_L1GT_197119_20210201_20210302_02_T2",
        "s3_location":
        "s3://usgs-landsat/collection02/level-1/standard/oli-tirs/2021/197/119/LC08_L1GT_197119_20210201_20210302_02_T2/"
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


@patch(
    "lambda_functions.execute_landsat_step_function.boto3.client"
)
def test_handler_non_08(client):
    """Test handler."""
    message = {
        "landsat_product_id": "LE07_L1GT_184023_20210302_20210303_02_RT",
        "s3_location": "s3://usgs-landsat/collection02/level-1/standard/etm/2021/184/023/LE07_L1GT_184023_20210302_20210303_02_RT"
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
