import os
import boto3
import json


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
    if "Cause" in event["jobinfo"].keys():
        try:
            jobinfo = json.loads(event["jobinfo"]["Cause"])
            jobinfostring = json.dumps(jobinfo)
        except ValueError:
            jobinfo = event["jobinfo"]["Cause"]
            jobinfostring = jobinfo
    else:
        jobinfo = event["jobinfo"]
        jobinfostring = json.dumps(event["jobinfo"])

    q = "INSERT INTO eventlog (event) VALUES (:event::jsonb);"
    execute_statement(
        q,
        sql_parameters=[{"name": "event", "value": {"stringValue": jobinfostring}}],
    )
    try:
        exitcode = jobinfo["Attempts"][0]["Container"]["ExitCode"]
    except KeyError:
        exitcode = "nocode"
    except TypeError:
        exitcode = "nocode"

    print(f"Exit Code is {exitcode}")
    return exitcode
