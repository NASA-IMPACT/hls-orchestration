import pytest
from unittest.mock import patch
from lambda_functions.execute_step_function.hls_execute_step_function.handler import (
    handler,
)


def test_handler_keyError(capsys):
    expected = "Message body does not contain key\n"
    handler({}, {})
    out, err = capsys.readouterr()
    assert out == expected


@patch(
    "lambda_functions.execute_step_function.hls_execute_step_function.handler.boto3.client"
)
def test_handler(client):
    """Test handler."""
    expected_input = (
        '{"granule": "S2A_MSIL1C_20191001T201241_N0208_R028_T09WXT_20191001T220736A"}'
    )
    start_execution_response = {"executionArn": "arn", "startDate": 10}
    event = {
        "Records": [
            {
                "s3": {
                    "object": {
                        "key": "S2A_MSIL1C_20191001T201241_N0208_R028_T09WXT_20191001T220736A.zip"
                    }
                }
            }
        ]
    }
    client.return_value.start_execution.return_value = start_execution_response
    handler(event, {})
    args, kwargs = client.return_value.start_execution.call_args
    assert kwargs["input"] == expected_input
