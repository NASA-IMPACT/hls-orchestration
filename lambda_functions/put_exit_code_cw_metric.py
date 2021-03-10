import os
import boto3
from typing import Dict
from datetime import datetime, timezone, timedelta


db_credentials_secrets_store_arn = os.getenv("HLS_SECRETS")
database_name = os.getenv("HLS_DB_NAME")
db_cluster_arn = os.getenv("HLS_DB_ARN")
job_id = os.getenv("JOB_ID")
table_name = os.getenv("TABLE_NAME")

rds_client = boto3.client("rds-data")
cw_client = boto3.client("cloudwatch")


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
        "exit_code": record[0]["stringValue"],
        "count": record[1]["longValue"],
    }
    return converted


def put_metric(record):
    exit_code = record["exit_code"]
    cw_client.put_metric_data(
        Namespace="hls",
        MetricData=[
            {
                "MetricName": f"{job_id}-exit_code_{exit_code}",
                "Timestamp": datetime.now(timezone.utc),
                "Value": record["count"],
                "Unit": "Count",
            },
        ]
    )


def handler(event: Dict, context: Dict):
    from_statement = f" FROM {table_name} WHERE"
    query = (
        "SELECT COALESCE(jobinfo->'Container'->>'ExitCode', 'null_value')"
        + "as exit_code, count(*)"
        + from_statement
        + " job_stopped > to_timestamp(:from_ts, 'yyyy-mm-dd hh24:mi:ss')"
        + " group by COALESCE(jobinfo->'Container'->>'ExitCode', 'null_value');"
    )

    from_ts = str(datetime.now(timezone.utc) - timedelta(days=25))
    sql_parameters = [
        {"name": "from_ts", "value": {"stringValue": from_ts}}
    ]
    response = execute_statement(
        query,
        sql_parameters=sql_parameters
    )
    records = map(convert_records, response["records"])
    for record in records:
        put_metric(record)
