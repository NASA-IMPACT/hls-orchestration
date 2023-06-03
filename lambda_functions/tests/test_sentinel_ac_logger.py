import json
from unittest.mock import patch

import pytest
from hls_lambda_layer.batch_test_events import (
    batch_expected_failed_event,
    batch_failed_event,
    batch_failed_event_string_cause,
    batch_succeeded_event,
)

from lambda_functions.sentinel_ac_logger import handler


@patch("lambda_functions.sentinel_ac_logger.rds_client")
def test_handler_keyError(client):
    """Test handler."""
    event = {
        "granule": "S2A_MSIL1C_20200708T232851_N0209_R044_T58LEP_20200709T005119",
        "jobinfo": batch_failed_event,
    }
    cause = json.loads(event["jobinfo"]["Cause"])
    jobinfo = {"name": "jobinfo", "value": {"stringValue": json.dumps(cause)}}
    granule = {"name": "granule", "value": {"stringValue": event["granule"]}}
    succeeded = {"name": "succeeded", "value": {"booleanValue": False}}
    expected_error = {"name": "expected_error", "value": {"booleanValue": False}}
    unexpected_error = {"name": "unexpected_error", "value": {"booleanValue": True}}
    client.execute_statement.return_value = {}
    output = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    assert jobinfo in kwargs["parameters"]
    assert granule in kwargs["parameters"]
    assert succeeded in kwargs["parameters"]
    assert expected_error in kwargs["parameters"]
    assert unexpected_error in kwargs["parameters"]
    assert output == 1


@patch("lambda_functions.sentinel_ac_logger.rds_client")
def test_handler_expected_keyError(client):
    """Test handler."""
    event = {
        "granule": "S2A_MSIL1C_20200708T232851_N0209_R044_T58LEP_20200709T005119",
        "jobinfo": batch_expected_failed_event,
    }
    cause = json.loads(event["jobinfo"]["Cause"])
    jobinfo = {"name": "jobinfo", "value": {"stringValue": json.dumps(cause)}}
    granule = {"name": "granule", "value": {"stringValue": event["granule"]}}
    succeeded = {"name": "succeeded", "value": {"booleanValue": False}}
    expected_error = {"name": "expected_error", "value": {"booleanValue": True}}
    unexpected_error = {"name": "unexpected_error", "value": {"booleanValue": False}}
    client.execute_statement.return_value = {}
    output = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    assert jobinfo in kwargs["parameters"]
    assert granule in kwargs["parameters"]
    assert succeeded in kwargs["parameters"]
    assert expected_error in kwargs["parameters"]
    assert unexpected_error in kwargs["parameters"]
    assert output == 137


@patch("lambda_functions.sentinel_ac_logger.rds_client")
def test_handler(client):
    """Test handler."""
    event = {
        "granule": "S2A_MSIL1C_20200708T232851_N0209_R044_T58LEP_20200709T005119",
        "jobinfo": batch_succeeded_event,
    }
    client.execute_statement.return_value = {}
    output = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    jobinfo = {
        "name": "jobinfo",
        "value": {"stringValue": json.dumps(event["jobinfo"])},
    }
    succeeded = {"name": "succeeded", "value": {"booleanValue": True}}
    expected_error = {"name": "expected_error", "value": {"booleanValue": False}}
    unexpected_error = {"name": "unexpected_error", "value": {"booleanValue": False}}
    assert jobinfo in kwargs["parameters"]
    assert succeeded in kwargs["parameters"]
    assert expected_error in kwargs["parameters"]
    assert unexpected_error in kwargs["parameters"]
    assert output == 0


@patch("lambda_functions.sentinel_ac_logger.rds_client")
def test_handler_valueError(client):
    """Test handler."""
    event = {
        "granule": "S2A_MSIL1C_20200708T232851_N0209_R044_T58LEP_20200709T005119",
        "jobinfo": batch_failed_event_string_cause,
    }

    jobinfo_value = {"cause": event["jobinfo"]["Cause"]}

    jobinfo = {"name": "jobinfo", "value": {"stringValue": json.dumps(jobinfo_value)}}
    succeeded = {"name": "succeeded", "value": {"booleanValue": False}}
    expected_error = {"name": "expected_error", "value": {"booleanValue": False}}
    unexpected_error = {"name": "unexpected_error", "value": {"booleanValue": True}}
    client.execute_statement.return_value = {}
    output = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    assert jobinfo in kwargs["parameters"]
    assert succeeded in kwargs["parameters"]
    assert expected_error in kwargs["parameters"]
    assert unexpected_error in kwargs["parameters"]
    assert output == "nocode"
