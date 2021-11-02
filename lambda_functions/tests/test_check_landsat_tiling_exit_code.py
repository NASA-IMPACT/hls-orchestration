import pytest

from lambda_functions.check_landsat_tiling_exit_code import handler


def test_handler_no_errors():
    event = [0,5]
    actual = handler(event, {})
    assert actual


def test_handler_no_errors_with_dict():
    dict_value = {
        "date": "2021-01-17",
        "path": "083",
        "MGRS": "58KEB",
        "mgrs_metadata": {
            "pathrows": [
                "083074",
                "083075"
            ],
            "mgrs_ulx": "499980",
            "mgrs_uly": "7700020",
            "pathrows_string": "083074,083075"
        },
        "ready_for_tiling": False
    }
    event = [0, dict_value]
    actual = handler(event, {})
    assert actual


def test_handler_exit_code_1():
    event = [0,5,1]
    actual = handler(event, {})
    assert not actual


def test_handler_exit_code_nocode():
    event = [0,"nocode"]
    actual = handler(event, {})
    assert not actual
