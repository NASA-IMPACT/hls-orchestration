import pytest
from unittest.mock import patch
from lambda_functions.process_sentinel_errors_by_date import handler


@patch("lambda_functions.process_sentinel_errors_by_date.step_function_client")
@patch("lambda_functions.process_sentinel_errors_by_date.rds_client")
def test_handler_chunking(rds_client, step_function_client):
    event = {
        "fromdate": "30/01/2021"
    }
    records = [[{"longValue": 1}, {"stringValue": "granule"}] for i in range(350)]
    response = {
        "records": records
    }
    rds_client.execute_statement.return_value = response
    handler(event, {})
    assert step_function_client.start_execution.call_count == 4
    args, kwargs = step_function_client.start_execution.call_args_list[3]
    assert kwargs["input"]["errors"][0] == {"id": 1, "granule": "granule"}
    assert kwargs["input"]["fromdate"] == event["fromdate"]
