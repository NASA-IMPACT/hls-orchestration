import pytest
from lambda_functions.check_exit_code. \
    hls_check_exit_code.handler import (
        handler
    )


def test_handler_no_errors():
    event = 3
    actual = handler(event, {})
    assert actual


def test_handler_exit_code_1():
    event = 1
    actual = handler(event, {})
    assert not actual


def test_handler_exit_code_nocode():
    event = "nocode"
    actual = handler(event, {})
    assert not actual
