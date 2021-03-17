import os
import boto3
from typing import Dict
from datetime import datetime, timezone, timedelta


db_credentials_secrets_store_arn = os.getenv("HLS_SECRETS")
database_name = os.getenv("HLS_DB_NAME")
db_cluster_arn = os.getenv("HLS_DB_ARN")

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


def handler(event: Dict, context: Dict):
    job_id = os.getenv("JOB_ID")
    table_name = os.getenv("TABLE_NAME")
    metric_namespace = "hls"
    from_statement = f" FROM {table_name} WHERE"
    query = (
        "SELECT COALESCE(jobinfo->'Container'->>'ExitCode', 'null_value')"
        + "as exit_code, count(*)"
        + from_statement
        + " job_stopped > to_timestamp(:from_ts, 'yyyy-mm-dd hh24:mi:ss')"
        + " group by COALESCE(jobinfo->'Container'->>'ExitCode', 'null_value');"
    )

    from_ts = str(datetime.now(timezone.utc) - timedelta(hours=1))
    sql_parameters = [
        {"name": "from_ts", "value": {"stringValue": from_ts}}
    ]
    query_response = execute_statement(
        query,
        sql_parameters=sql_parameters
    )

    updated_metrics = [
        {
            "MetricName": f"{job_id}-exit_code_{record[0]['stringValue']}",
            "Timestamp": datetime.now(timezone.utc),
            "Value": record[1]["longValue"],
            "Unit": "Count",
        }
        for record in query_response["records"]
    ]

    updated_metric_names = [
        f"{job_id}-exit_code_{record[0]['stringValue']}"
        for record in query_response["records"]
    ]

    list_metrics_response = cw_client.list_metrics(Namespace=metric_namespace)

    metric_names = [
        metric["MetricName"] for metric in list_metrics_response["Metrics"]
        if metric["MetricName"].startswith(job_id)
    ]

    not_updated_metric_names = list(set(metric_names) - set(updated_metric_names))

    not_updated_metrics = [
        {
            "MetricName": metric_name,
            "Timestamp": datetime.now(timezone.utc),
            "Value": 0,
            "Unit": "Count",
        }
        for metric_name in not_updated_metric_names
    ]

    metric_data = updated_metrics + not_updated_metrics
    cw_client.put_metric_data(
        Namespace=metric_namespace,
        MetricData=metric_data
    )
