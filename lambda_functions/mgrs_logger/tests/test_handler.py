import pytest
import json
from unittest.mock import patch, call
from lambda_functions.mgrs_logger.hls_mgrs_logger.handler import handler


@patch(
    "lambda_functions.mgrs_logger.hls_mgrs_logger.handler.rds_client"
)
def test_handler(client):
    """Test handler."""
    event = {
        "date": "2020-07-19",
        "path": "210",
        "MGRS": "29VMJ",
        "tilejobinfo": {
            "Attempts": [
                {
                    "Container": {
                        "ExitCode": 0
                    },
                    "StartedAt": 1595336905229,
                    "StatusReason": "Essential container in task exited",
                    "StoppedAt": 1595336905412
                }
            ],
            "Container": {
            }
        }
    }
    client.execute_statement.return_value = {}
    expected = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    q = (
        "UPDATE landsat_mgrs_log SET jobinfo = :jobinfo::jsonb"
        + " WHERE path = :path::varchar(3) AND"
        + " mgrs = :mgrs::varchar(5) AND acquisition = :acquisition::date;"
    )
    path = {"name": "path", "value": {"stringValue": "210"}}
    acquisition = {"name": "acquisition", "value": {"stringValue": "2020-07-19"}}
    mgrs = {"name": "mgrs", "value": {"stringValue": "29VMJ"}}
    jobinfo = {"name": "jobinfo", "value": {"stringValue":
                                            json.dumps(event["tilejobinfo"])}}
    assert q == kwargs["sql"]
    assert path in kwargs["parameters"]
    assert mgrs in kwargs["parameters"]
    assert acquisition in kwargs["parameters"]
    assert jobinfo in kwargs["parameters"]
    assert expected == 0


@patch(
    "lambda_functions.mgrs_logger.hls_mgrs_logger.handler.rds_client"
)
def test_handler_error(client):
    """Test handler."""
    event = {
        "date": "2020-07-19",
        "path": "210",
        "MGRS": "29VMJ",
        "tilejobinfo": {
            "Cause": "{\"Attempts\":[{\"Container\":{\"ExitCode\": 1}}]}"
        }
    }
    client.execute_statement.return_value = {}
    expected = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    q = (
        "UPDATE landsat_mgrs_log SET jobinfo = :jobinfo::jsonb"
        + " WHERE path = :path::varchar(3) AND"
        + " mgrs = :mgrs::varchar(5) AND acquisition = :acquisition::date;"
    )
    path = {"name": "path", "value": {"stringValue": "210"}}
    acquisition = {"name": "acquisition", "value": {"stringValue": "2020-07-19"}}
    mgrs = {"name": "mgrs", "value": {"stringValue": "29VMJ"}}
    cause = json.loads(event["tilejobinfo"]["Cause"])
    jobinfo = {"name": "jobinfo", "value": {"stringValue": json.dumps(cause)}}
    assert q == kwargs["sql"]
    assert path in kwargs["parameters"]
    assert mgrs in kwargs["parameters"]
    assert acquisition in kwargs["parameters"]
    assert jobinfo in kwargs["parameters"]
    assert expected == 1


@patch(
    "lambda_functions.mgrs_logger.hls_mgrs_logger.handler.rds_client"
)
def test_handler_error_no_exit_code(client):
    """Test handler."""
    event = {
        "date": "2020-07-19",
        "path": "210",
        "MGRS": "29VMJ",
        "tilejobinfo": {
            "Cause": "{\"Attempts\":[{\"Container\":{}}]}"
        }
    }
    client.execute_statement.return_value = {}
    expected = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    q = (
        "UPDATE landsat_mgrs_log SET jobinfo = :jobinfo::jsonb"
        + " WHERE path = :path::varchar(3) AND"
        + " mgrs = :mgrs::varchar(5) AND acquisition = :acquisition::date;"
    )
    path = {"name": "path", "value": {"stringValue": "210"}}
    acquisition = {"name": "acquisition", "value": {"stringValue": "2020-07-19"}}
    mgrs = {"name": "mgrs", "value": {"stringValue": "29VMJ"}}
    cause = json.loads(event["tilejobinfo"]["Cause"])
    jobinfo = {"name": "jobinfo", "value": {"stringValue": json.dumps(cause)}}
    assert q == kwargs["sql"]
    assert path in kwargs["parameters"]
    assert mgrs in kwargs["parameters"]
    assert acquisition in kwargs["parameters"]
    assert jobinfo in kwargs["parameters"]
    assert expected == "nocode"


@patch(
    "lambda_functions.mgrs_logger.hls_mgrs_logger.handler.rds_client"
)
def test_handler_error_non_json(client):
    """Test handler."""
    event = {
        "date": "2020-07-19",
        "path": "210",
        "MGRS": "29VMJ",
        "tilejobinfo": {
            "Cause": "jobdefinition error"
        }
    }
    client.execute_statement.return_value = {}
    expected = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    q = (
        "UPDATE landsat_mgrs_log SET jobinfo = :jobinfo::jsonb"
        + " WHERE path = :path::varchar(3) AND"
        + " mgrs = :mgrs::varchar(5) AND acquisition = :acquisition::date;"
    )
    path = {"name": "path", "value": {"stringValue": "210"}}
    acquisition = {"name": "acquisition", "value": {"stringValue": "2020-07-19"}}
    mgrs = {"name": "mgrs", "value": {"stringValue": "29VMJ"}}
    cause = event["tilejobinfo"]["Cause"]
    jobinfo = {"name": "jobinfo", "value": {"stringValue": cause}}
    assert q == kwargs["sql"]
    assert path in kwargs["parameters"]
    assert mgrs in kwargs["parameters"]
    assert acquisition in kwargs["parameters"]
    assert jobinfo in kwargs["parameters"]
    assert expected == "nocode"



