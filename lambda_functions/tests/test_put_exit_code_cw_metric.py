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
    rds_client.execute_statement.return_value = response
    handler({}, {})

    args, kwargs = cw_client.put_metric_data.call_args_list[0]
    assert kwargs["MetricData"][0]["MetricName"] == "id-exit_code_0"
    assert kwargs["MetricData"][0]["Value"] == 10

    args, kwargs = cw_client.put_metric_data.call_args_list[1]
    assert kwargs["MetricData"][0]["MetricName"] == "id-exit_code_1"
    assert kwargs["MetricData"][0]["Value"] == 20
