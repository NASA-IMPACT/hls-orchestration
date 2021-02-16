import pytest
import json
from unittest.mock import patch
from lambda_functions.process_landsat_mgrs_incompletes import handler


@patch("lambda_functions.process_landsat_mgrs_incompletes.step_function_client")
@patch("lambda_functions.process_landsat_mgrs_incompletes.rds_client")
def test_handler_chunking(rds_client, step_function_client):
    event = {
        "fromdate": "26/12/2020"
    }
    records = [
        [
            {"stringValue": "15UUT"},
            {"stringValue": "030"},
            {"stringValue": "2020-12-25"}
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
        "date": "2020-12-25"
    }
    assert input["fromdate"] == event["fromdate"]
