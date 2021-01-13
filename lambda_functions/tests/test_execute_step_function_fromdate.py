import pytest
import os
from unittest.mock import patch
from lambda_functions.execute_step_function_fromdate import handler


@patch(
    "lambda_functions.execute_step_function_fromdate.boto3.client"
)
@patch.dict(os.environ, {"DAYS_PRIOR": "4"})
def test_handler(client):
    """Test handler."""
    expected_input = (
        '{"fromdate": "09/01/2021"}'
    )
    start_execution_response = {"executionArn": "arn", "startDate": 10}
    event = {
        "time": "2021-01-13T12:00:00Z"
    }
    client.return_value.start_execution.return_value = start_execution_response
    handler(event, {})
    args, kwargs = client.return_value.start_execution.call_args
    assert kwargs["input"] == expected_input
