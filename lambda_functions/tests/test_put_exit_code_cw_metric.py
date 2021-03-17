import pytest
import json
import os
from unittest.mock import patch
from lambda_functions.put_exit_code_cw_metric import handler


@patch("lambda_functions.put_exit_code_cw_metric.cw_client")
@patch("lambda_functions.put_exit_code_cw_metric.rds_client")
@patch.dict(os.environ, {"JOB_ID": "id", "TABLE_NAME": "landsat_ac_granule_log"})
def test_handler(rds_client, cw_client):
    records = [
        [
            {
                "stringValue": "0",
            },
            {
                "longValue": 10,
            }
        ],
        [
            {
                "stringValue": "1",
            },
            {
                "longValue": 20,
            }
        ]
    ]
    response = {
        "records": records
    }
    list_metrics_response = {
        "Metrics": [
            {
                "MetricName": "id-exit_code_0"
            },
            {
                "MetricName": "id-exit_code_1"
            }
        ]

    }
    cw_client.list_metrics.return_value = list_metrics_response
    rds_client.execute_statement.return_value = response
    handler({}, {})
    args, kwargs = cw_client.put_metric_data.call_args_list[0]
    assert kwargs["MetricData"][0]["MetricName"] == "id-exit_code_0"
    assert kwargs["MetricData"][0]["Value"] == 10

    assert kwargs["MetricData"][1]["MetricName"] == "id-exit_code_1"
    assert kwargs["MetricData"][1]["Value"] == 20


@patch("lambda_functions.put_exit_code_cw_metric.cw_client")
@patch("lambda_functions.put_exit_code_cw_metric.rds_client")
@patch.dict(os.environ, {"JOB_ID": "id", "TABLE_NAME": "landsat_ac_granule_log"})
def test_handler_not_updated(rds_client, cw_client):
    records = [
        [
            {
                "stringValue": "0",
            },
            {
                "longValue": 10,
            }
        ],
        [
            {
                "stringValue": "1",
            },
            {
                "longValue": 20,
            }
        ]
    ]
    response = {
        "records": records
    }
    list_metrics_response = {
        "Metrics": [
            {
                "MetricName": "id-exit_code_0"
            },
            {
                "MetricName": "id-exit_code_1"
            },
            {
                "MetricName": "id-exit_code_3"
            }
        ]

    }
    cw_client.list_metrics.return_value = list_metrics_response
    rds_client.execute_statement.return_value = response
    handler({}, {})
    args, kwargs = cw_client.put_metric_data.call_args_list[0]
    assert kwargs["MetricData"][0]["MetricName"] == "id-exit_code_0"
    assert kwargs["MetricData"][0]["Value"] == 10

    assert kwargs["MetricData"][1]["MetricName"] == "id-exit_code_1"
    assert kwargs["MetricData"][1]["Value"] == 20

    # Sets Value to 0 for metrics which have not been updated.
    assert kwargs["MetricData"][2]["MetricName"] == "id-exit_code_3"
    assert kwargs["MetricData"][2]["Value"] == 0
