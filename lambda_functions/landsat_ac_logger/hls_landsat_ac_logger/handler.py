import os
import boto3
import json


db_credentials_secrets_store_arn = os.getenv("HLS_SECRETS")
database_name = os.getenv("HLS_DB_NAME")
db_cluster_arn = os.getenv("HLS_DB_ARN")


def execute_statement(sql, sql_parameters=[]):
    rds_client = boto3.client("rds-data")
    response = rds_client.execute_statement(
        secretArn=db_credentials_secrets_store_arn,
        database=database_name,
        resourceArn=db_cluster_arn,
        sql=sql,
        parameters=sql_parameters,
    )
    return response


def handler(event, context):
    acquisition_date = (
        f'{event["acquisitionYear"]}-{event["acquisitionMonth"]}-{event["acquisitionDay"]}'
    )
    q = (
        "INSERT INTO landsat_ac_log (path, row, acquisition, jobid, jobinfo) VALUES"
        + "(:path::varchar(3), :row::varchar(3), :acquisition::date, :jobid::text, :jobinfo::jsonb)"
        + " ON CONFLICT ON CONSTRAINT no_dupe_pathrowdate"
        + " DO UPDATE SET jobid = excluded.jobid, jobinfo = excluded.jobinfo;"
    )
    try:
        jobid = event["jobinfo"]["JobId"]
        jobinfo = json.dumps(event["jobinfo"])
    except KeyError:
        cause = json.loads(event["jobinfo"]["Cause"])
        jobid = cause["JobId"]
        jobinfo = json.dumps(cause)
    execute_statement(
        q,
        sql_parameters=[
            {"name": "path", "value": {"stringValue": event["path"]}},
            {"name": "row", "value": {"stringValue": event["row"]}},
            {"name": "acquisition", "value": {"stringValue": acquisition_date}},
            {"name": "jobid", "value": {"stringValue": jobid},},
            {"name": "jobinfo", "value": {"stringValue": jobinfo}},
        ],
    )
    return event
