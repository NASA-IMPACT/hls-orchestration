import os
import boto3
import json
from operator import itemgetter
from hls_lambda_layer.hls_batch_utils import parse_jobinfo

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
    sql_parameters = [
        {"name": "mgrs", "value": {"stringValue": event["MGRS"]}},
        {"name": "path", "value": {"stringValue": event["path"]}},
        {"name": "acquisition", "value": {"stringValue": event["date"]}},
    ]
    try:
        parsed_info = parse_jobinfo("tilejobinfo", event)
        jobinfo, jobinfostring, exitcode = itemgetter(
            "jobinfo", "jobinfostring", "exitcode"
        )(parsed_info)
        q = (
            "UPDATE landsat_mgrs_log SET (jobinfo, run_count) ="
            + " (:jobinfo::jsonb, run_count +1)"
        )
        sql_parameters.append(
            {"name": "jobinfo", "value": {"stringValue": jobinfostring}}
        )
    except KeyError:
        q = "UPDATE landsat_mgrs_log SET run_count = run_count +1"
        exitcode = "nocode"

    sql = (
        q
        + " WHERE path = :path::varchar(3) AND"
        + " mgrs = :mgrs::varchar(5) AND acquisition = :acquisition::date;"
    )
    print(sql)
    execute_statement(
        sql,
        sql_parameters=sql_parameters,
    )

    print(f"Exit Code is {exitcode}")
    return exitcode
