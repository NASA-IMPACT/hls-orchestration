import pytest
import json
from unittest.mock import patch
from lambda_functions.execute_landsat_step_function import handler


@patch(
    "lambda_functions.execute_landsat_step_function.boto3.client"
)
def test_handler(client):
    scene_meta = {
        "sensor": "C",
        "satellite": "08",
        "processingCorrectionLevel": "L1TP",
        "path": "231",
        "row": "089",
        "acquisitionYear": "2020",
        "acquisitionMonth": "08",
        "acquisitionDay": "07",
        "processingYear": "2020",
        "processingMonth": "08",
        "processingDay": "08",
        "collectionNumber": "02",
        "collectionCategory": "RT",
        "scene": "LC08_L1TP_231089_20200807_20200808_02_RT",
        "date": "2020-08-07",
        "scheme": "s3",
        "bucket": "usgs-landsat",
        "prefix": "collection02/level-1/standard/oli-tirs/2020/231/089/LC08_L1TP_231089_20200807_20200808_02_RT"
    }

    message = {
        "Records": [{
            "s3": {
                "bucket": {
                    "name": "usgs-landsat"
                },
                "object": {
                    "key": "collection02/level-1/standard/oli-tirs/2020/231/089/LC08_L1TP_231089_20200807_20200808_02_RT/LC08_L1TP_231089_20200807_20200808_02_RT_stac.json"
                }
            }
        }]
    }
    messagestring = json.dumps(message)
    event = {
        "Records": [
            {
                "Sns": {
                    "Message": messagestring
                }
            }
        ]
    }

    start_execution_response = {"executionArn": "arn", "startDate": 10}
    client.return_value.start_execution.return_value = start_execution_response
    handler(event, {})
    args, kwargs = client.return_value.start_execution.call_args
    expected_input = json.dumps(scene_meta)
    assert kwargs["input"] == expected_input


@patch(
    "lambda_functions.execute_landsat_step_function.boto3.client"
)
def test_handler_non_RT(client):
    message = {
        "Records": [{
            "s3": {
                "bucket": {
                    "name": "usgs-landsat"
                },
                "object": {
                    "key": "collection02/level-1/standard/oli-tirs/2020/231/089/LC08_L1TP_231089_20200807_20200808_02_T1/LC08_L1TP_231089_20200807_20200808_02_T1_stac.json"
                }
            }
        }]
    }
    messagestring = json.dumps(message)
    event = {
        "Records": [
            {
                "Sns": {
                    "Message": messagestring
                }
            }
        ]
    }

    handler(event, {})
    client.return_value.start_execution.assert_not_called()
