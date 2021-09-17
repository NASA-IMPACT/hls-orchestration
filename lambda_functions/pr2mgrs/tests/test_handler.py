import pytest
from lambda_functions.pr2mgrs.hls_pr2mgrs.handler import handler


def test_handler_mgrs():
    """Test handler."""
    expected = {
        "mgrs": [
            "28XEQ",
            "29XMK"
        ],
        "count": 2,
    }

    handler({"path": "001", "row": "002"}, {}) == expected


def test_handler_pathrow():
    expected = {
        "pathrows": [
            "001086",
            "232086",
            "233086"
        ],
        "mgrs_ulx": "199980",
        "mgrs_uly": "5900020",
        "pathrows_string": "001086,232086,233086"
    }
    assert handler({"MGRS": "19HBU"}, {}) == expected


def test_handler_mgrs_empty():
    expected = {
        "mgrs": [],
        "count": 0
    }
    assert handler({"path": "001", "row": "001"}, {}) == expected
