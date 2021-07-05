import pytest
import json
import os
from unittest.mock import patch
from lambda_functions.process_sentinel_errors import handler


@patch("lambda_functions.process_sentinel_errors.step_function_client")
@patch("lambda_functions.process_sentinel_errors.rds_client")
@patch.dict(os.environ, {"RETRY_LIMIT": "1"})
def test_handler_chunking(rds_client, step_function_client):
    records = [[{"longValue": 1}, {"stringValue": "granule"}] for i in range(350)]
    response = {
        "records": records
    }
    rds_client.execute_statement.return_value = response
    handler({}, {})
    assert step_function_client.start_execution.call_count == 4
    args, kwargs = step_function_client.start_execution.call_args_list[3]
    input = json.loads(kwargs["input"])
    assert input["errors"][0] == {"id": 1, "granule": "granule"}
