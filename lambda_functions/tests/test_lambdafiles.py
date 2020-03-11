import pytest
from typing import List, Dict
import json


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    monkeypatch.setenv("HLS_SECRETS", "secrets")
    monkeypatch.setenv("HLS_DB_NAME", "dbname")
    monkeypatch.setenv("HLS_DB_ARN", "dbarn")
    monkeypatch.setenv("SENTINEL_INPUT_BUCKET", "sentinelinput")


def test_logger(monkeypatch):
    from lambda_functions.logger import (
        rds_client,
        handler,
        db_credentials_secrets_store_arn,
        database_name,
        db_cluster_arn,
    )

    assert db_credentials_secrets_store_arn == "secrets"
    assert database_name == "dbname"
    assert db_cluster_arn == "dbarn"

    def execute_statement(
        secretArn: str,
        database: str,
        resourceArn: str,
        sql: str,
        parameters: List[Dict],
    ):
        return True

    monkeypatch.setattr(rds_client, "execute_statement", execute_statement)

    event_success = {"Hello": True}
    event_failure = {"Cause": json.dumps(event_success)}

    assert handler(event_success, {}) == event_success
    assert handler(event_failure, {}) == event_success


def test_setupdb(monkeypatch):
    from lambda_functions.setupdb import (
        rds_client,
        handler,
        db_credentials_secrets_store_arn,
        database_name,
        db_cluster_arn,
    )

    assert db_credentials_secrets_store_arn == "secrets"
    assert database_name == "dbname"
    assert db_cluster_arn == "dbarn"

    def execute_statement(
        secretArn: str,
        database: str,
        resourceArn: str,
        sql: str,
        parameters: List[Dict],
    ):
        return True

    monkeypatch.setattr(rds_client, "execute_statement", execute_statement)

    event_success = {"Hello": True}

    assert handler(event_success, {}) == event_success


def test_twin_granules(monkeypatch):
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
