import json
import os
from unittest.mock import patch

import pytest

from lambda_functions.process_landsat_mgrs_incompletes import handler

event = {
    "time": "2021-01-30T12:00:00Z"
}


@patch("lambda_functions.process_landsat_mgrs_incompletes.step_function_client")
@patch("lambda_functions.process_landsat_mgrs_incompletes.rds_client")
@patch.dict(os.environ, {"DAYS_PRIOR": "4"})
@patch.dict(os.environ, {"RETRY_LIMIT": "3"})
@patch.dict(os.environ, {"HISTORIC": "historic"})
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
    delta = {"name": "delta", "value": {"stringValue": "26/01/2021"}}
    retry_limit = {"name": "retry_limit", "value": {"longValue": 3}}
    historic_value = {"name": "historic_value", "value": {"booleanValue": True}}
    assert delta in kwargs["parameters"]
    assert retry_limit in kwargs["parameters"]
    assert historic_value in kwargs["parameters"]
    assert "TO_DATE" in kwargs["sql"]


@patch("lambda_functions.process_landsat_mgrs_incompletes.step_function_client")
@patch("lambda_functions.process_landsat_mgrs_incompletes.rds_client")
@patch.dict(os.environ, {"HOURS_PRIOR": "6"})
@patch.dict(os.environ, {"RETRY_LIMIT": "3"})
@patch.dict(os.environ, {"HISTORIC": "historic"})
def test_handler_hours(rds_client, step_function_client):
    records = [
        [
            {"stringValue": "15UUT"},
            {"stringValue": "030"},
            {"stringValue": "2021-01-26"}
        ] for i in range(1)
    ]
    response = {
        "records": records
    }
    rds_client.execute_statement.return_value = response
    handler(event, {})

    args, kwargs = rds_client.execute_statement.call_args
    delta = {"name": "delta", "value": {"stringValue": "30-01-2021 06:00:00"}}
    assert delta in kwargs["parameters"]
    assert "TO_TIMESTAMP" in kwargs["sql"]
