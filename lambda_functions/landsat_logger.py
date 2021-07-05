"""Update landsat_ac_log with new granule when it firsts enters the system."""
import os
import boto3
from operator import itemgetter

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
    """
    Update landsat_ac_log with new granule when it firsts enters the system.

    Parameters:
    event (dict) Event source from step function input.

    """
    sql_parameters = [
        {"name": "path", "value": {"stringValue": event["path"]}},
        {"name": "row", "value": {"stringValue": event["row"]}},
        {"name": "scene_id", "value": {"stringValue": event["scene"]}},
        {"name": "acquisition", "value": {"stringValue": event["date"]}},
        {"name": "run_count", "value": {"longValue": 0}},
    ]
    sql = (
        "INSERT INTO landsat_ac_log (path, row, scene_id, acquisition, run_count) VALUES"
        + "(:path::varchar(3), :row::varchar(3),"
        + " :scene_id::varchar(200), :acquisition::date, :run_count::integer)"
        + " ON CONFLICT ON CONSTRAINT no_dupe_pathrowdate"
        + " DO NOTHING"
    )
    execute_statement(
        sql,
        sql_parameters=sql_parameters,
    )
