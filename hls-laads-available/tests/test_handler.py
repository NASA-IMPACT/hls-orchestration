"""test handler."""

import pytest


from hls_laads_available.handler import getyyyydoy, handler


def test_getyyyydoy():
    """Test handler."""
    assert getyyyydoy("2020-01-01") == ("2020001", "2020")
    assert getyyyydoy("2020-001") == ("2020001", "2020")
    assert getyyyydoy("2020001") == ("2020001", "2020")
    assert getyyyydoy("20200101") == ("2020001", "2020")
    assert getyyyydoy("2020-02-01") == ("2020032", "2020")
    assert getyyyydoy("LC08_L1TP_170071_20190303_20190309_01_T1") == ("2019062", "2019")
    assert getyyyydoy("S2B_MSIL1C_20190301T075849_N0207_R035_T35HKD_20190301T121820") == ("2019060", "2019")

    with pytest.raises(Exception):
        handler({}, {})
