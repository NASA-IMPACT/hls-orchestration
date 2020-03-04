import pytest
from botocore.errorfactory import ClientError


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    monkeypatch.setenv("LAADS_BUCKET", "test")


def test_getyyyydoy():
    from lambda_functions.laads_available.hls_laads_available.handler import getyyyydoy

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
    from lambda_functions.laads_available.hls_laads_available import handler

    expected = "Missing Date Parameter"
    with pytest.raises(Exception) as e:
        handler.handler({}, {})
        assert expected in str(e.value)


def test_handler(monkeypatch):
    from lambda_functions.laads_available.hls_laads_available import handler

    granule = "S2A_MSIL1C_20191001T201241_N0208_R028_T09WXT_20191001T220736A"
    event = {"granule": granule}
    response = {
        "granule": granule,
        "year": "2019",
        "doy": "2019274",
        "bucket": "test",
        "key": "lasrc_aux/LADS/2019/L8ANC2019274.hdf_fused",
        "available": True,
    }

    def head_object_exists(Bucket, Key):
        return ""

    monkeypatch.setattr(handler.s3, "head_object", head_object_exists)
    ret = handler.handler(event, {})
    assert ret == response

    def head_object_notexists(Bucket, Key):
        raise ClientError(
            error_response={"Error": {"Code": "404"}}, operation_name="head_obj"
        )

    monkeypatch.setattr(handler.s3, "head_object", head_object_notexists)
    ret = handler.handler(event, {})
    response["available"] = False
    assert ret == response

    def head_object_exception(Bucket, Key):
        raise ClientError(
            error_response={"Error": {"Code": "403"}}, operation_name="head_obj"
        )

    monkeypatch.setattr(handler.s3, "head_object", head_object_exception)

    with pytest.raises(Exception):
        ret = handler.handler(event, {})
        assert ret == response
