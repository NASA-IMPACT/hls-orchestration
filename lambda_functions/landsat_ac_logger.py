import os
import boto3
import json
from operator import itemgetter
from hls_lambda_layer.hls_batch_utils import parse_jobinfo


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
    parsed_info = parse_jobinfo("jobinfo", event)
    jobinfo, jobinfostring, exitcode, jobid = itemgetter(
        "jobinfo", "jobinfostring", "exitcode", "jobid"
    )(parsed_info)
    q = (
        "UPDATE landsat_ac_log SET (jobid, jobinfo) ="
        + " (:jobid::text, :jobinfo::jsonb)"
        + " WHERE scene_id = :scene::text"
    )
    execute_statement(
        q,
        sql_parameters=[
            {"name": "jobid", "value": {"stringValue": jobid},},
            {"name": "jobinfo", "value": {"stringValue": jobinfostring}},
            {"name": "scene", "value": {"stringValue": event["scene"]}}
        ],
    )

    print(f"Exit Code is {exitcode}")
    return exitcode
