import pytest
import json
from unittest.mock import patch
from lambda_functions.process_landsat_day import handler

event = {
    "time": "2020-12-03T12:00:00Z"
}


@patch("lambda_functions.process_landsat_day.rds_client")
def test_handler_date(rds_client):
    handler(event, {})
    args, kwargs = rds_client.execute_statement.call_args
    retrieved_date = {
        "name": "retrieved_date",
        "value": {"stringValue": "01/12/2020"}
    }
    assert retrieved_date in kwargs["parameters"]
