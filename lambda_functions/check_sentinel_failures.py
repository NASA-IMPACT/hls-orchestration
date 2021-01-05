import os
import boto3


db_credentials_secrets_store_arn = os.getenv("HLS_SECRETS")
database_name = os.getenv("HLS_DB_NAME")
db_cluster_arn = os.getenv("HLS_DB_ARN")


rds_client = boto3.client("rds-data")


def execute_statement(sql, sql_parameters=[]):
    response = rds_client.execute_statement(
        secretArn=db_credentials_secrets_store_arn,
        database=database_name,
        resourceArn=db_cluster_arn,
        sql=sql,
        parameters=sql_parameters,
    )
    return response


def convert_records(record):
    converted = {
        "id": record[0]["longValue"],
        "granule": record[1]["stringValue"]
    }
    return converted


def handler(event, context):
    q = (
        "SELECT id, granule from granule_log WHERE"
        + " event->'Container'->>'ExitCode' = '1'"
        + " AND DATE(ts) = TO_DATE(:fromdate::text,'DD/MM/YYYY');"
    )
    response = execute_statement(
        q,
        sql_parameters=[
            {"name": "fromdate", "value": {"stringValue": event["fromdate"]}},
        ]
    )
    records = map(convert_records, response["records"])
    return list(records)
