import os
import boto3
import json

rds_client = boto3.client("rds-data")

db_credentials_secrets_store_arn = os.getenv("HLS_SECRETS")
database_name = os.getenv("HLS_DB_NAME")
db_cluster_arn = os.getenv("HLS_DB_ARN")


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
    q = (
        "UPDATE landsat_mgrs_log SET jobinfo = :jobinfo::jsonb"
        + " WHERE path = :path::varchar(3) AND"
        + " mgrs = :mgrs::varchar(5) AND acquisition = :acquisition::date;"
    )
    if "Cause" in event["tilejobinfo"].keys():
        cause = json.loads(event["tilejobinfo"]["Cause"])
        jobinfo = json.dumps(cause)
    else:
        jobinfo = json.dumps(event["tilejobinfo"])
    execute_statement(
        q,
        sql_parameters=[
            {"name": "mgrs", "value": {"stringValue": event["MGRS"]}},
            {"name": "path", "value": {"stringValue": event["path"]}},
            {"name": "acquisition", "value": {"stringValue": event["date"]}},
            {"name": "jobinfo", "value": {"stringValue": jobinfo}}
        ],
    )
    return event
