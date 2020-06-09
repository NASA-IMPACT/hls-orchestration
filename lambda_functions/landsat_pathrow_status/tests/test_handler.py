import pytest
import json
from unittest.mock import patch
from lambda_functions.landsat_pathrow_status.hls_landsat_pathrow_status.handler import (
    handler,
)


@patch(
    "lambda_functions.landsat_pathrow_status.hls_landsat_pathrow_status.handler.boto3.client"
)
def test_handler(client):
    """Test handler."""
    event = (
        {
            "date": "2020-05-28",
            "path": "182",
            "MGRS": "36VVK",
            "pathrow": [
                "182019",
                "182020"
            ]
        }
    )
    client.return_value.execute_statement.return_value = {}
    handler(event, {})
    args, kwargs = client.return_value.execute_statement.call_args
    assert True
