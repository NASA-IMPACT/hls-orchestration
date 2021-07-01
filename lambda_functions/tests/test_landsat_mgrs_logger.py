import pytest
import json
from unittest.mock import patch, call
from lambda_functions.landsat_mgrs_logger import handler


@patch(
    "lambda_functions.landsat_mgrs_logger.rds_client"
)
def test_handler(client):
    """Test handler."""
    event = {
        "sensor": "C",
        "satellite": "08",
        "processingCorrectionLevel": "L1GT",
        "path": "127",
        "row": "010",
        "acquisitionYear": "2020",
        "acquisitionMonth": "05",
        "acquisitionDay": "27",
        "processingYear": "2020",
        "processingMonth": "05",
        "processingDay": "27",
        "collectionNumber": "01",
        "collectionCategory": "RT",
        "scene": "LC08_L1GT_127010_20200527_20200527_01_RT",
        "date": "2020-05-27",
        "scheme": "s3",
        "bucket": "landsat-pds",
        "prefix": "x1/L8/127/010/LC08_L1GT_127010_20200527_20200527_01_RT",
        "taskresult": {
            "granule": "LC08_L1GT_127010_20200527_20200527_01_RT",
            "year": "2020",
            "doy": "2020148",
            "bucket": "hls-development-laads-bucket",
            "key": "lasrc_aux/LADS/2020/L8ANC2020148.hdf_fused",
            "available": True,
        },
        "mgrsvalues": {
            "mgrs": [
                "51WXU",
                "51WXV",
                "52WDC",
                "52WDD",
                "52WDE",
                "52WEC",
                "52WED",
                "52WEE",
                "52WFC",
                "52WFD",
                "52WFE",
                "53WMU",
                "53WMV",
            ],
            "count": 13,
        },
    }
    client.execute_statement.return_value = {}
    handler(event, {})
    path = {"name": "path", "value": {"stringValue": "127"}}
    acquisition = {"name": "acquisition", "value": {"stringValue": "2020-05-27"}}
    sql = (
        "INSERT INTO landsat_mgrs_log (path, mgrs, acquisition, run_count)"
        + " VALUES (:path::varchar(3), :mgrs::varchar(5), :acquisition::date, :run_count::integer)"
        + " ON CONFLICT DO NOTHING;"
    )
    expected_calls = []
    for mgrs in event["mgrsvalues"]["mgrs"]:
        sql_parameters = [
            path,
            {"name": "mgrs", "value": {"stringValue": mgrs}},
            acquisition,
            {"name": "run_count", "value": {"longValue": 0}}
        ]
        insert_call = call(
            sql=sql,
            parameters=sql_parameters,
            database=None,
            resourceArn=None,
            secretArn=None,
        )
        expected_calls.append(insert_call)

    client.execute_statement.assert_has_calls(expected_calls)
