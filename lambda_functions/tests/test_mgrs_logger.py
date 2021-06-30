import pytest
import json
from unittest.mock import patch, call
from lambda_functions.mgrs_logger import handler
from hls_lambda_layer.batch_test_events import (
    batch_failed_event,
    batch_succeeded_event,
    batch_failed_event_string_cause,
    batch_failed_event_no_exit
)


@patch(
    "lambda_functions.mgrs_logger.rds_client"
)
def test_handler(client):
    """Test handler."""
    event = {
        "date": "2020-07-19",
        "path": "210",
        "MGRS": "29VMJ",
        "tilejobinfo": batch_succeeded_event
    }
    client.execute_statement.return_value = {}
    expected = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    path = {"name": "path", "value": {"stringValue": "210"}}
    acquisition = {"name": "acquisition", "value": {"stringValue": "2020-07-19"}}
    mgrs = {"name": "mgrs", "value": {"stringValue": "29VMJ"}}
    jobinfo = {"name": "jobinfo", "value": {"stringValue":
                                            json.dumps(event["tilejobinfo"])}}
    assert path in kwargs["parameters"]
    assert mgrs in kwargs["parameters"]
    assert acquisition in kwargs["parameters"]
    assert jobinfo in kwargs["parameters"]
    assert expected == 0


@patch(
    "lambda_functions.mgrs_logger.rds_client"
)
def test_handler_error(client):
    """Test handler."""
    event = {
        "date": "2020-07-19",
        "path": "210",
        "MGRS": "29VMJ",
        "tilejobinfo": batch_failed_event
    }
    client.execute_statement.return_value = {}
    expected = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    cause = json.loads(event["tilejobinfo"]["Cause"])
    jobinfo = {"name": "jobinfo", "value": {"stringValue": json.dumps(cause)}}
    assert jobinfo in kwargs["parameters"]
    assert expected == 1


@patch(
    "lambda_functions.mgrs_logger.rds_client"
)
def test_handler_error_no_exit_code(client):
    """Test handler."""
    event = {
        "date": "2020-07-19",
        "path": "210",
        "MGRS": "29VMJ",
        "tilejobinfo": batch_failed_event_no_exit
    }
    client.execute_statement.return_value = {}
    expected = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    cause = json.loads(event["tilejobinfo"]["Cause"])
    jobinfo = {"name": "jobinfo", "value": {"stringValue": json.dumps(cause)}}
    assert jobinfo in kwargs["parameters"]
    assert expected == "nocode"


@patch(
    "lambda_functions.mgrs_logger.rds_client"
)
def test_handler_error_non_json(client):
    """Test handler."""
    event = {
        "date": "2020-07-19",
        "path": "210",
        "MGRS": "29VMJ",
        "tilejobinfo": batch_failed_event_string_cause
    }
    client.execute_statement.return_value = {}
    expected = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    jobinfo_value = {
        "cause": event["tilejobinfo"]["Cause"]
    }

    jobinfo = {
        "name": "jobinfo",
        "value": {
            "stringValue": json.dumps(jobinfo_value)
        }
    }
    assert jobinfo in kwargs["parameters"]
    assert expected == "nocode"
