import json
from unittest.mock import patch

import pytest

from lambda_functions.landsat_pathrow_status import handler


@patch(
    "lambda_functions.landsat_pathrow_status.rds_client"
)
def test_handler_ready(client):
    """Test handler."""
    event = {
        "date": "2020-05-28",
        "path": "182",
        "MGRS": "36VVK",
        "mgrs_metadata": {"pathrows": ["182019", "182020"],},
    }
    return_value = {"records": [{"row": "019"}, {"row": "020"},]}
    client.execute_statement.return_value = return_value
    actual = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    assert actual


@patch(
    "lambda_functions.landsat_pathrow_status.rds_client"
)
def test_handler_not_ready(client):
    """Test handler."""
    event = {
        "date": "2020-05-28",
        "path": "182",
        "MGRS": "36VVK",
        "mgrs_metadata": {"pathrows": ["182019", "182020"],},
    }
    return_value = {"records": [{"row": "019"},]}
    client.execute_statement.return_value = return_value
    actual = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    assert not actual
