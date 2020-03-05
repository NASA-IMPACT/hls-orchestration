import pytest
from typing import List, Dict
import json


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    monkeypatch.setenv("HLS_SECRETS", "secrets")
    monkeypatch.setenv("HLS_DB_NAME", "dbname")
    monkeypatch.setenv("HLS_DB_ARN", "dbarn")


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
