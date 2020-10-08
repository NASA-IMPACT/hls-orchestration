import pytest
import json
from unittest.mock import patch
from lambda_functions.landsat_ac_logger.hls_landsat_ac_logger.handler import handler
from hls_lambda_layer.batch_test_events import (
    batch_failed_event,
    batch_succeeded_event,
    batch_failed_event_string_cause
)


@patch("lambda_functions.landsat_ac_logger.hls_landsat_ac_logger.handler.rds_client")
def test_handler_keyError(client):
    """Test handler."""
    event = {
        "satellite": "08",
        "path": "127",
        "row": "010",
        "date": "2020-05-27",
        "jobinfo": batch_failed_event
    }
    cause = json.loads(event["jobinfo"]["Cause"])
    jobinfo = {"name": "jobinfo", "value": {"stringValue": json.dumps(cause)}}
    client.execute_statement.return_value = {}
    output = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    path = {"name": "path", "value": {"stringValue": "127"}}
    row = {"name": "row", "value": {"stringValue": "010"}}
    acquisition = {"name": "acquisition", "value": {"stringValue": "2020-05-27"}}
    assert path in kwargs["parameters"]
    assert row in kwargs["parameters"]
    assert acquisition in kwargs["parameters"]
    assert jobinfo in kwargs["parameters"]
    assert output == 1


@patch("lambda_functions.landsat_ac_logger.hls_landsat_ac_logger.handler.rds_client")
def test_handler(client):
    """Test handler."""
    event = {
        "path": "116",
        "row": "078",
        "date": "2020-05-30",
        "jobinfo": batch_succeeded_event
    }
    client.execute_statement.return_value = {}
    output = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    path = {"name": "path", "value": {"stringValue": "116"}}
    row = {"name": "row", "value": {"stringValue": "078"}}
    acquisition = {"name": "acquisition", "value": {"stringValue": "2020-05-30"}}
    jobinfo = {"name": "jobinfo", "value": {"stringValue":
                                            json.dumps(event["jobinfo"])}}
    assert path in kwargs["parameters"]
    assert row in kwargs["parameters"]
    assert acquisition in kwargs["parameters"]
    assert jobinfo in kwargs["parameters"]
    assert output == 0
