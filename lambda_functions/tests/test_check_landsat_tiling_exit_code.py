import pytest
from lambda_functions.check_landsat_tiling_exit_code import handler


def test_handler_no_errors():
    event = [0,3]
    actual = handler(event, {})
    assert actual


def test_handler_exit_code_1():
    event = [0,3,1]
    actual = handler(event, {})
    assert not actual


def test_handler_exit_code_nocode():
    event = [0,3,"nocode"]
    actual = handler(event, {})
    assert not actual
