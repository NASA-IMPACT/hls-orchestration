import pytest
from lambda_functions.pr2mgrs.hls_pr2mgrs.handler import handler


def test_handler():
    """Test handler."""
    expected = {
        "mgrs": [
            "29XNK",
            "29XNL",
            "30XVQ",
            "30XVR",
            "30XWP",
            "30XWQ",
            "30XWR",
            "31XDJ",
            "31XDK",
            "31XDL",
            "31XEJ",
            "31XEK",
            "31XEL",
        ],
        "count": 13,
    }
    assert handler({"path": "001", "row": "001"}, {}) == expected

    expected = {
        "pathrows": [
            "001001",
            "001002",
            "002001",
            "002002",
            "003001",
            "003002",
            "004001",
            "004002",
            "005001",
            "005002",
            "006001",
            "006002",
            "007001",
            "007002",
            "008001",
            "009001",
            "010001",
            "011001",
            "229003",
            "230002",
            "230003",
            "231002",
            "232002",
            "233002",
            "233003",
        ],
        "mgrs_ulx": "499980",
        "mgrs_uly": "9000000",
    }
    assert handler({"MGRS": "29XNK"}, {}) == expected

    expected = {
        "pathrows": ["003001", "003002",],
        "mgrs_ulx": "499980",
        "mgrs_uly": "9000000",
    }
    assert handler({"MGRS": "29XNK", "path": "003"}, {}) == expected
    with pytest.raises(Exception):
        handler({}, {})
