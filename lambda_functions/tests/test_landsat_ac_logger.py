import json
from unittest.mock import patch

import pytest
from hls_lambda_layer.batch_test_events import (
    batch_failed_event,
    batch_failed_event_string_cause,
    batch_succeeded_event,
)

from lambda_functions.landsat_ac_logger import handler


@patch("lambda_functions.landsat_ac_logger.rds_client")
def test_handler_keyError(client):
    """Test handler."""
    event = {
        "satellite": "08",
        "path": "127",
        "row": "010",
        "date": "2020-05-27",
        "scene": "LC08_L1TP_127010_20200527_20200527_02_RT",
        "jobinfo": batch_failed_event,
    }
    cause = json.loads(event["jobinfo"]["Cause"])
    jobinfo = {"name": "jobinfo", "value": {"stringValue": json.dumps(cause)}}
    client.execute_statement.return_value = {}
    output = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    scene = {
        "name": "scene",
        "value": {"stringValue": "LC08_L1TP_127010_20200527_20200527_02_RT"},
    }
    assert jobinfo in kwargs["parameters"]
    assert scene in kwargs["parameters"]
    assert output == 1


@patch("lambda_functions.landsat_ac_logger.rds_client")
def test_handler(client):
    """Test handler."""
    event = {
        "path": "116",
        "row": "078",
        "date": "2020-05-30",
        "scene": "LC08_L1TP_127010_20200527_20200527_02_RT",
        "jobinfo": batch_succeeded_event,
    }
    client.execute_statement.return_value = {}
    output = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    jobinfo = {
        "name": "jobinfo",
        "value": {"stringValue": json.dumps(event["jobinfo"])},
    }

    scene = {
        "name": "scene",
        "value": {"stringValue": "LC08_L1TP_127010_20200527_20200527_02_RT"},
    }
    assert jobinfo in kwargs["parameters"]
    assert scene in kwargs["parameters"]
    assert output == 0


@patch("lambda_functions.landsat_ac_logger.rds_client")
def test_handler_no_jobid(client):
    """Test handler."""
    event = {
        "satellite": "08",
        "path": "127",
        "row": "010",
        "date": "2020-05-27",
        "scene": "LC08_L1TP_127010_20200527_20200527_02_RT",
        "jobinfo": batch_failed_event_string_cause,
    }
    client.execute_statement.return_value = {}
    output = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    scene = {
        "name": "scene",
        "value": {"stringValue": "LC08_L1TP_127010_20200527_20200527_02_RT"},
    }
    assert scene in kwargs["parameters"]
    assert len(kwargs["parameters"]) == 2
    assert output == "nocode"
