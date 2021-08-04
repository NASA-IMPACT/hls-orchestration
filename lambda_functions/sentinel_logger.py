"""Update sentinel_log with new granule when it firsts enters the system."""
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


def handler(event, context):
    """
    Update sentinel_log with new granule when it firsts enters the system.

    Parameters:
    event (dict) Event source of the lambda trigger

    """
    #  Initial run_count is 0 before processing
    sql_parameters = [
        {"name": "granule", "value": {"stringValue": event["granule"]}},
        {"name": "run_count", "value": {"longValue": 0}},
    ]
    historic = os.getenv("HISTORIC")
    if historic == "historic":
        historic_value = True
    else:
        historic_value = False
    historic_parameter = {"name": "historic", "value": historic_value}
    sql_parameters.append(historic_parameter)

    sql = (
        "INSERT INTO sentinel_log (granule, run_count, historic) VALUES"
        + "(:granule::varchar, :run_count::integer, :historic::boolean)"
    )
    execute_statement(
        sql,
        sql_parameters=sql_parameters,
    )
    return event
