import pytest
from lambda_functions.pr2mgrs.hls_pr2mgrs.handler import handler


def test_handler():
    """Test handler."""
    expected = [
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
    ]
    assert handler({"Path": "001", "Row": "001"}, {}) == expected

    expected = [
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
    ]
    assert handler({"MGRS": "29XNK"}, {}) == expected

    expected = [
        "003001",
        "003002",
    ]
    assert handler({"MGRS": "29XNK", "Path": "003"}, {}) == expected
    with pytest.raises(Exception):
        handler({}, {})
