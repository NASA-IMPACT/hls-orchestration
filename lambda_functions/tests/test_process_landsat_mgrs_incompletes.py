import pytest
import json
import os
from unittest.mock import patch
from lambda_functions.process_landsat_mgrs_incompletes import handler

event = {
    "time": "2021-01-30T12:00:00Z"
}


@patch("lambda_functions.process_landsat_mgrs_incompletes.step_function_client")
@patch("lambda_functions.process_landsat_mgrs_incompletes.rds_client")
@patch.dict(os.environ, {"DAYS_PRIOR": "4"})
@patch.dict(os.environ, {"RETRY_LIMIT": "3"})
def test_handler_chunking(rds_client, step_function_client):
    records = [
        [
            {"stringValue": "15UUT"},
            {"stringValue": "030"},
            {"stringValue": "2021-01-26"}
        ] for i in range(350)
    ]
    response = {
        "records": records
    }
    rds_client.execute_statement.return_value = response
    handler(event, {})
    assert step_function_client.start_execution.call_count == 4
    args, kwargs = step_function_client.start_execution.call_args_list[3]
    input = json.loads(kwargs["input"])
    assert input["incompletes"][0] == {
        "MGRS": "15UUT",
        "path": "030",
        "date": "2021-01-26"
    }
    assert input["fromdate"] == "26/01/2021"

    args, kwargs = rds_client.execute_statement.call_args
    fromdate = {"name": "fromdate", "value": {"stringValue": "26/01/2021"}}
    retry_limit = {"name": "retry_limit", "value": {"longValue": 3}}
    assert fromdate in kwargs["parameters"]
    assert retry_limit in kwargs["parameters"]
