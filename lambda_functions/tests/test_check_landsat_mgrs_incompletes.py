import pytest
import json
from unittest.mock import patch
from lambda_functions.check_landsat_mgrs_incompletes import handler


@patch(
    "lambda_functions.check_landsat_mgrs_incompletes.rds_client"
)
def test_handler_convert(client):
    return_value = {
        "records": [
            [
                {"stringValue": "15UUT"},
                {"stringValue": "030"},
                {"stringValue": "2020-12-29"}
            ]
        ]
    }
    record = {
        "MGRS": "15UUT",
        "path": "030",
        "date": "2020-12-29"
    }
    client.execute_statement.return_value = return_value
    event = {
        "fromdate": "14/09/2020"
    }
    actual = handler(event, {})
    assert len(actual) == 1
    assert record in actual
