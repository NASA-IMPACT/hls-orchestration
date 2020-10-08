import pytest
import json
from unittest.mock import patch
from lambda_functions.sentinel_logger.hls_sentinel_logger.handler import handler
from hls_lambda_layer.batch_test_events import (
    batch_failed_event,
    batch_succeeded_event,
    batch_failed_event_string_cause
)


@patch("lambda_functions.sentinel_logger.hls_sentinel_logger.handler.rds_client")
def test_handler_keyError(client):
    """Test handler."""
    event = {
        "jobinfo": batch_failed_event
    }
    cause = json.loads(event["jobinfo"]["Cause"])
    jobinfo = {"name": "event", "value": {"stringValue": json.dumps(cause)}}
    client.execute_statement.return_value = {}
    output = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    assert jobinfo in kwargs["parameters"]
    assert output == 1


@patch("lambda_functions.sentinel_logger.hls_sentinel_logger.handler.rds_client")
def test_handler(client):
    """Test handler."""
    event = {
        "jobinfo": batch_succeeded_event
    }
    client.execute_statement.return_value = {}
    output = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    jobinfo = {"name": "event", "value": {"stringValue":
                                          json.dumps(event["jobinfo"])}}
    assert jobinfo in kwargs["parameters"]
    assert output == 0


@patch("lambda_functions.sentinel_logger.hls_sentinel_logger.handler.rds_client")
def test_handler_valueError(client):
    """Test handler."""
    event = {
        "jobinfo": batch_failed_event_string_cause
    }
    cause = event["jobinfo"]["Cause"]
    jobinfo = {"name": "event", "value": {"stringValue": cause}}
    client.execute_statement.return_value = {}
    output = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    assert jobinfo in kwargs["parameters"]
    assert output == "nocode"
