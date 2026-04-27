from unittest.mock import MagicMock

import pytest

from hls_lambda_layer.laads_utils import getyyyydoy
from lambda_functions.laads_available import handler


def test_getyyyydoy():

    assert getyyyydoy("2020-01-01") == ("2020001", "2020")
    assert getyyyydoy("2020-001") == ("2020001", "2020")
    assert getyyyydoy("2020001") == ("2020001", "2020")
    assert getyyyydoy("20200101") == ("2020001", "2020")
    assert getyyyydoy("2020-02-01") == ("2020032", "2020")
    assert getyyyydoy("LC08_L1TP_170071_20190303_20190309_01_T1") == ("2019062", "2019")
    assert getyyyydoy(
        "S2B_MSIL1C_20190301T075849_N0207_R035_T35HKD_20190301T121820"
    ) == ("2019060", "2019")


def test_handler_keyError():
    expected = "Missing Date Parameter"
    with pytest.raises(Exception) as e:
        handler({}, {})
        assert expected in str(e.value)


def test_handler(monkeypatch):
    monkeypatch.setenv("LAADS_BUCKET", "test")

    mock_s3 = MagicMock()
    mock_s3.list_objects_v2.return_value = {"Contents": ["a key"]}
    monkeypatch.setattr("hls_lambda_layer.laads_utils.s3", mock_s3)

    granule = "S2A_MSIL1C_20191001T201241_N0208_R028_T09WXT_20191001T220736A"
    event = {"granule": granule}
    expected = {
        "granule": granule,
        "year": "2019",
        "doy": "2019274",
        "bucket": "test",
        "pattern": "lasrc_aux/LADS/2019/VJ104ANC.A2019274 lasrc_aux/LADS/2019/VNP04ANC.A2019274",
        "available": True,
    }

    assert handler(event, {}) == expected
