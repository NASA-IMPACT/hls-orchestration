import pytest
from hls_lambda_layer.hls_batch_utils import parse_jobinfo
from hls_lambda_layer.batch_test_events import (
    batch_failed_event,
    batch_succeeded_event,
    batch_failed_event_string_cause,
    batch_failed_event_no_exit
)


def test_parse_jobinfo_keyError():
    key = "jobinfo"
    event = {
        key: batch_failed_event
    }
    parsed_info = parse_jobinfo(key, event)
    assert parsed_info["jobid"] == "5ce9a71e-2f18-4dd1-b9ac-9d3618774d3f"
    assert parsed_info["exitcode"] == 1
    assert len(parsed_info["jobinfo"]["Attempts"]) == 1


def test_parse_jobinfo_success():
    key = "jobinfo"
    event = {
        key: batch_succeeded_event
    }
    parsed_info = parse_jobinfo(key, event)
    assert parsed_info["jobid"] == "d5ce77ea-9d95-4bb9-bf2c-d78da2459e54"
    assert parsed_info["exitcode"] == 0
    assert len(parsed_info["jobinfo"]["Attempts"]) == 1


def test_parse_jobinfo_valueError():
    key = "jobinfo"
    event = {
        key: batch_failed_event_string_cause
    }
    parsed_info = parse_jobinfo(key, event)
    assert parsed_info["jobid"] is None
    assert parsed_info["jobinfo"] == "A cause message"
    assert parsed_info["exitcode"] == "nocode"


def test_parse_jobinfo_no_exit():
    key = "tilejobinfo"
    event = {
        key: batch_failed_event_string_cause
    }
    parsed_info = parse_jobinfo(key, event)
    assert parsed_info["exitcode"] == "nocode"
