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
    q = (
        "INSERT INTO landsat_ac_log (path, row, acquisition, jobid, jobinfo) VALUES"
        + "(:path::varchar(3), :row::varchar(3), :acquisition::date, :jobid::text, :jobinfo::jsonb)"
        + " ON CONFLICT ON CONSTRAINT no_dupe_pathrowdate"
        + " DO UPDATE SET jobid = excluded.jobid, jobinfo = excluded.jobinfo;"
    )
    if "Cause" in event["jobinfo"].keys():
        try:
            jobinfo = json.loads(event["jobinfo"]["Cause"])
            jobid = jobinfo["JobId"]
            jobinfostring = json.dumps(jobinfo)
        except ValueError:
            jobinfo = event["jobinfo"]["Cause"]
            jobid = jobinfo["JobId"]
            jobinfostring = jobinfo
    else:
        jobinfo = event["jobinfo"]
        jobid = jobinfo["JobId"]
        jobinfostring = json.dumps(event["jobinfo"])

    execute_statement(
        q,
        sql_parameters=[
            {"name": "path", "value": {"stringValue": event["path"]}},
            {"name": "row", "value": {"stringValue": event["row"]}},
            {"name": "acquisition", "value": {"stringValue": event["date"]}},
            {"name": "jobid", "value": {"stringValue": jobid},},
            {"name": "jobinfo", "value": {"stringValue": jobinfostring}},
        ],
    )
    try:
        exitcode = jobinfo["Attempts"][0]["Container"]["ExitCode"]
    except KeyError:
        exitcode = "nocode"
    except TypeError:
        exitcode = "nocode"

    print(f"Exit Code is {exitcode}")
    return exitcode
