"""Update landsat_mgrs_log with intersecting MGRS grid values when a landsat granule enter the system"""
import json
import os

import boto3

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
    """
    Update landsat_mgrs_log with new intersecting MGRS values.

    Parameters:
    event (dict) Event source from step function input.

    Returns:
    event (dict)

    """
    historic = os.getenv("HISTORIC")
    sql = (
        "INSERT INTO landsat_mgrs_log (path, mgrs, acquisition, run_count, historic)"
        + " VALUES (:path::varchar(3), :mgrs::varchar(5), :acquisition::date,"
        + " :run_count::integer, :historic::boolean)"
        + " ON CONFLICT DO NOTHING;"
    )
    for mgrs_grid in event["mgrsvalues"]["mgrs"]:
        sql_parameters = [
            {"name": "path", "value": {"stringValue": event["path"]}},
            {"name": "mgrs", "value": {"stringValue": mgrs_grid}},
            {"name": "acquisition", "value": {"stringValue": event["date"]}},
            {"name": "run_count", "value": {"longValue": 0}}
        ]

        if historic == "historic":
            historic_value = True
        else:
            historic_value = False
        historic_parameter = {"name": "historic", "value": {"booleanValue": historic_value}}
        sql_parameters.append(historic_parameter)

        execute_statement(
            sql,
            sql_parameters=sql_parameters,
        )
    return event
