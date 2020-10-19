import pytest
from typing import List, Dict
import json


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    monkeypatch.setenv("SENTINEL_INPUT_BUCKET", "sentinelinput")


def test_twin_granule(monkeypatch):
    from lambda_functions.twin_granule import (
        s3,
        handler,
    )

    def test_lo(
        Bucket: str, Prefix: str,
    ):
        response = {"Contents": [{"Key": "one.zip"}]}
        if Prefix == "one":
            return response
        if Prefix == "two":
            response["Contents"].append({"Key": "two.zip"})
            return response
        else:
            return {}

    monkeypatch.setattr(s3, "list_objects_v2", test_lo)

    assert handler({"granule": "one123456"}, {}) == {"granule": "one"}
    assert handler({"granule": "two123456"}, {}) == {"granule": "one,two"}
    with pytest.raises(KeyError):
        handler({"granule": "bogus123456"}, {})
