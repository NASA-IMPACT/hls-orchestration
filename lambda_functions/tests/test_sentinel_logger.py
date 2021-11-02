import json
import os
from unittest.mock import patch

import pytest

from lambda_functions.sentinel_logger import handler


@patch("lambda_functions.sentinel_logger.rds_client")
def test_handler(client):
    """Test handler."""
    event = {
        "granule": "S2A_MSIL1C_20200708T232851_N0209_R044_T58LEP_20200709T005119",
    }
    client.execute_statement.return_value = {}
    handler(event, {})
    args, kwargs = client.execute_statement.call_args
    granule = {"name": "granule", "value": {"stringValue": event["granule"]}}
    assert granule in kwargs["parameters"]
    # Initial run_count should be 0.
    run_count = {"name": "run_count", "value": {"longValue": 0}}
    assert run_count in kwargs["parameters"]


@patch.dict(os.environ, {"HISTORIC": "historic"})
@patch("lambda_functions.sentinel_logger.rds_client")
def test_handler_historic(client):
    """Test handler."""
    event = {
        "granule": "S2A_MSIL1C_20200708T232851_N0209_R044_T58LEP_20200709T005119",
    }
    client.execute_statement.return_value = {}
    handler(event, {})
    args, kwargs = client.execute_statement.call_args

    historic = {"name": "historic", "value": {"booleanValue": True}}
    assert historic in kwargs["parameters"]
