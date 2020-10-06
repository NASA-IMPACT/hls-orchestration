import pytest
import json
from unittest.mock import patch
from lambda_functions.check_sentinel_failures.hls_check_sentinel_failures.handler import (
    handler,
)


@patch(
    "lambda_functions.check_sentinel_failures.hls_check_sentinel_failures.handler.rds_client"
)
def test_handler_convert(client):
    return_value = {
        "records": [
            [
                {"longValue": 430},
                {"stringValue": "S2B_MSIL1C_20200214T200849_N0209_R042_T06KTF_20200214T211703"}
            ],
            [
                {"longValue": 463},
                {"stringValue": "S2B_MSIL1C_20200214T200849_N0209_R042_T06KTF_20200214T211703"}
            ],
        ]
    }
    record = {
        "id": 430,
        "granule": "S2B_MSIL1C_20200214T200849_N0209_R042_T06KTF_20200214T211703",
    }
    client.execute_statement.return_value = return_value
    actual = handler({}, {})
    assert len(actual) == 2
    assert record in actual
