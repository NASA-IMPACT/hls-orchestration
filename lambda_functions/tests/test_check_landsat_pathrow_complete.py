import pytest
import json
from unittest.mock import patch
from lambda_functions.check_landsat_pathrow_complete import handler


event = {
    "date": "2021-01-02",
    "path": "090",
    "MGRS": "55GDN",
    "mgrs_metadata": {
        "pathrows": [
            "090089",
            "090090"
        ],
        "mgrs_ulx": "399960",
        "mgrs_uly": "5300020"
    }
}


@patch(
    "lambda_functions.check_landsat_pathrow_complete.rds_client"
)
def test_handler_convert(client):
    return_value = {
        "records": [
            [
                {"longValue": 1},
                {"longValue": 2},
                {"stringValue": "090"},
                {"stringValue": "089"},
            ]
        ]
    }
    client.execute_statement.return_value = return_value

    actual = handler(event, {})
    assert actual == "090089"


@patch(
    "lambda_functions.check_landsat_pathrow_complete.rds_client"
)
def test_handler_none(client):
    return_value = {
        "records": []
    }
    client.execute_statement.return_value = return_value
    actual = handler(event, {})
    assert actual is None
