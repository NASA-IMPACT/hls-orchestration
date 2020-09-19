import pytest
import json
from unittest.mock import patch
from lambda_functions.landsat_ac_logger.hls_landsat_ac_logger.handler import handler


@patch("lambda_functions.landsat_ac_logger.hls_landsat_ac_logger.handler.rds_client")
def test_handler_keyError(client):
    """Test handler."""
    event = {
        "satellite": "08",
        "path": "127",
        "row": "010",
        "date": "2020-05-27",
        "jobinfo": {
            "Error": "States.TaskFailed",
            "Cause": '{\"JobId\":\"69c9d58d-c9d2-4e49-8b00-f2f2728f8252\","Attempts":[{"Container":{"ContainerInstanceArn":"arn:aws:ecs:us-west-2:018923174646:container-instance/cebc97a6-5c16-4987-9d24-27b96246dcdd","ExitCode":1,"LogStreamName":"LandsatTaskBatchJob1274-131d33be785ce5d/default/7c7cd09e-33c0-44f5-919a-2f66e0b8e995","NetworkInterfaces":[],"TaskArn":"arn:aws:ecs:us-west-2:018923174646:task/7c7cd09e-33c0-44f5-919a-2f66e0b8e995"},"StartedAt":1591403928719,"StatusReason":"Essential container in task exited","StoppedAt":1591403929450}],"Container":{"Command":["export && landsat.sh"],"ContainerInstanceArn":"arn:aws:ecs:us-west-2:018923174646:container-instance/cebc97a6-5c16-4987-9d24-27b96246dcdd","Environment":[{"Name":"PREFIX","Value":"x1/L8/127/010/LC08_L1GT_127010_20200527_20200527_01_RT"},{"Name":"GRANULE","Value":"LC08_L1GT_127010_20200527_20200527_01_RT"},{"Name":"OUTPUT_BUCKET","Value":"hls-development-landsat-intermediate-output"},{"Name":"LASRC_AUX_DIR","Value":"/var/lasrc_aux"},{"Name":"MANAGED_BY_AWS","Value":"STARTED_BY_STEP_FUNCTIONS"},{"Name":"INPUT_BUCKET","Value":"landsat-pds"},{"Name":"REPLACE_EXISTING","Value":"replace"}],"ExitCode":1,"Image":"018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-landsat:latest","JobRoleArn":"arn:aws:iam::018923174646:role/hls-development-LandsatTaskTaskRoleFD2391A2-440VUZKTYZ2O","LogStreamName":"LandsatTaskBatchJob1274-131d33be785ce5d/default/7c7cd09e-33c0-44f5-919a-2f66e0b8e995","Memory":12000,"MountPoints":[{"ContainerPath":"/var/lasrc_aux","ReadOnly":false,"SourceVolume":"volume"},{"ContainerPath":"/var/scratch","ReadOnly":false,"SourceVolume":"scratch_volume"}],"NetworkInterfaces":[],"ResourceRequirements":[],"TaskArn":"arn:aws:ecs:us-west-2:018923174646:task/7c7cd09e-33c0-44f5-919a-2f66e0b8e995","Ulimits":[],"Vcpus":2,"Volumes":[{"Host":{"SourcePath":"/mnt/efs"},"Name":"volume"},{"Host":{"SourcePath":"/scratch"},"Name":"scratch_volume"}]},"CreatedAt":1591403386307,"DependsOn":[],"JobDefinition":"arn:aws:batch:us-west-2:018923174646:job-definition/LandsatTaskBatchJob1274-131d33be785ce5d:2","JobId":"5ce9a71e-2f18-4dd1-b9ac-9d3618774d3f","JobName":"LandsatAcJob","JobQueue":"arn:aws:batch:us-west-2:018923174646:job-queue/BatchJobQueueFD3B0361-88c4344c33bfb4a","Parameters":{},"RetryStrategy":{"Attempts":1},"StartedAt":1591403928719,"Status":"FAILED","StatusReason":"Essential container in task exited","StoppedAt":1591403929450,"Timeout":{"AttemptDurationSeconds":5400}}',
        },
    }
    cause = json.loads(event["jobinfo"]["Cause"])
    jobinfo = {"name": "jobinfo", "value": {"stringValue": json.dumps(cause)}}
    client.execute_statement.return_value = {}
    output = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    path = {"name": "path", "value": {"stringValue": "127"}}
    row = {"name": "row", "value": {"stringValue": "010"}}
    acquisition = {"name": "acquisition", "value": {"stringValue": "2020-05-27"}}
    assert path in kwargs["parameters"]
    assert row in kwargs["parameters"]
    assert acquisition in kwargs["parameters"]
    assert jobinfo in kwargs["parameters"]
    assert output == 1


@patch("lambda_functions.landsat_ac_logger.hls_landsat_ac_logger.handler.rds_client")
def test_handler(client):
    """Test handler."""
    event = {
        "path": "116",
        "row": "078",
        "date": "2020-05-30",
        "jobinfo": {
            "JobId": "69c9d58d-c9d2-4e49-8b00-f2f2728f8252"
        },
    }
    client.execute_statement.return_value = {}
    output = handler(event, {})
    args, kwargs = client.execute_statement.call_args
    path = {"name": "path", "value": {"stringValue": "116"}}
    row = {"name": "row", "value": {"stringValue": "078"}}
    acquisition = {"name": "acquisition", "value": {"stringValue": "2020-05-30"}}
    jobinfo = {"name": "jobinfo", "value": {"stringValue":
                                            json.dumps(event["jobinfo"])}}
    assert path in kwargs["parameters"]
    assert row in kwargs["parameters"]
    assert acquisition in kwargs["parameters"]
    assert jobinfo in kwargs["parameters"]
    assert output == "nocode"
