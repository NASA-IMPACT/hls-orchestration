import os
import boto3
import json
from functools import reduce


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


def handler(event, context):
    pathrows = event["mgrs_metadata"]["pathrows"]
    rowlist = reduce((lambda agg, row: agg + "'" + row[-3:] + "'" + ","), pathrows, "")
    rowlist = rowlist.rstrip(",")
    rowlistquery = " AND row IN (" + rowlist + ")"
    q = (
        "SELECT * FROM landsat_ac_log WHERE"
        + " path = :path AND acquisition = :acquisition::date AND jobinfo->>'Status' = 'SUCCEEDED'"
        + rowlistquery
    )
    response = execute_statement(
        q,
        sql_parameters=[
            {"name": "path", "value": {"stringValue": event["path"]}},
            {"name": "acquisition", "value": {"stringValue": event["date"]}},
        ],
    )
    if len(response["records"]) == len(pathrows):
        ready_for_tiling = True
    else:
        ready_for_tiling = False

    return ready_for_tiling
