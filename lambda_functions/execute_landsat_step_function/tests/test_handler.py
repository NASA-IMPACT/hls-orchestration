import pytest
import json
from unittest.mock import patch
from lambda_functions.execute_landsat_step_function.hls_execute_landsat_step_function.handler import (
    handler,
)


@patch(
    "lambda_functions.execute_landsat_step_function.hls_execute_landsat_step_function.handler.boto3.client"
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
        "collectionCategory": "T1",
        "scene": "LC08_L1GT_127010_20200527_20200527_01_T1",
        "date": "2020-05-27",
        "scheme": "s3",
        "bucket": "landsat-pds",
        "prefix": "c1/L8/127/010/LC08_L1GT_127010_20200527_20200527_01_T1",
    }
    expected_input = json.dumps(scene_meta)
    start_execution_response = {"executionArn": "arn", "startDate": 10}
    event = {
        "Records": [
            {
                "Sns": {
                    "Message":
                    '{"Records":[{"eventVersion":"2.0","eventSource":"aws:s3","awsRegion":"us-west-2","eventTime":"2016-01-16T01:36:55.014Z","eventName":"ObjectCreated:Put","userIdentity":{"principalId":"AWS:AIDAILHHXPNIKSGVUGOZK"},"requestParameters":{"sourceIPAddress":"52.27.39.85"},"responseElements":{"x-amz-request-id":"078952E6C7CC52B4","x-amz-id-2":"Xboo1ULzd7PxY27iIaGXjUStV8TmG52JAbiWQpiRJWuRqfaBhLcc0XMUKNmXgd5fbIfRd1IcrgE="},"s3":{"s3SchemaVersion":"1.0","configurationId":"NewHTML","bucket":{"name":"landsat-pds","ownerIdentity":{"principalId":"A3LZTVCZQ87CNW"},"arn":"arn:aws:s3:::landsat-pds"},"object":{"key":"c1/L8/127/010/LC08_L1GT_127010_20200527_20200527_01_T1/index.html","size":3780,"eTag":"736e4e5a36cb8a1c6cbfc58659126ff1","sequencer":"0056999EB6F8BDBB8D"}}}]}',
                }
            }
        ]
    }

    client.return_value.start_execution.return_value = start_execution_response
    handler(event, {})
    args, kwargs = client.return_value.start_execution.call_args
    assert kwargs["input"] == expected_input


# @patch(
    # "lambda_functions.execute_landsat_step_function.hls_execute_landsat_step_function.handler.boto3.client"
# )
# def test_handler_non_RT(client):
    # """Test handler."""

    # event = {
        # "Records": [
            # {
                # "Sns": {
                    # "Message": '{"Records":[{"eventVersion":"2.0","eventSource":"aws:s3","awsRegion":"us-west-2","eventTime":"2016-01-16T01:36:55.014Z","eventName":"ObjectCreated:Put","userIdentity":{"principalId":"AWS:AIDAILHHXPNIKSGVUGOZK"},"requestParameters":{"sourceIPAddress":"52.27.39.85"},"responseElements":{"x-amz-request-id":"078952E6C7CC52B4","x-amz-id-2":"Xboo1ULzd7PxY27iIaGXjUStV8TmG52JAbiWQpiRJWuRqfaBhLcc0XMUKNmXgd5fbIfRd1IcrgE="},"s3":{"s3SchemaVersion":"1.0","configurationId":"NewHTML","bucket":{"name":"landsat-pds","ownerIdentity":{"principalId":"A3LZTVCZQ87CNW"},"arn":"arn:aws:s3:::landsat-pds"},"object":{"key":"/c1/L8/139/045/LC08_L1TP_139045_20170304_20170316_01_T1/index.html","size":3780,"eTag":"736e4e5a36cb8a1c6cbfc58659126ff1","sequencer":"0056999EB6F8BDBB8D"}}}]}',
                # }
            # }
        # ]
    # }

    # handler(event, {})
    # client.return_value.start_execution.assert_not_called()
