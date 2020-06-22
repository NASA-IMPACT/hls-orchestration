import pytest
import json
from unittest.mock import patch
from lambda_functions.landsat_ac_logger.hls_landsat_ac_logger.handler import handler


@patch("lambda_functions.landsat_ac_logger.hls_landsat_ac_logger.handler.rds_client")
def test_handler_keyError(client):
    """Test handler."""
    event = {
        "sensor": "C",
        "satellite": "08",
        "processingCorrectionLevel": "L1GT",
        "path": "127",
        "row": "010",
        "acquisitionYear": "2020",
        "acquisitionMonth": "05",
        "acquisitionDay": "27",
        "processingYear": "2020",
        "processingMonth": "05",
        "processingDay": "27",
        "collectionNumber": "01",
        "collectionCategory": "RT",
        "scene": "LC08_L1GT_127010_20200527_20200527_01_RT",
        "date": "2020-05-27",
        "scheme": "s3",
        "bucket": "landsat-pds",
        "prefix": "x1/L8/127/010/LC08_L1GT_127010_20200527_20200527_01_RT",
        "taskresult": {
            "granule": "LC08_L1GT_127010_20200527_20200527_01_RT",
            "year": "2020",
            "doy": "2020148",
            "bucket": "hls-development-laads-bucket",
            "key": "lasrc_aux/LADS/2020/L8ANC2020148.hdf_fused",
            "available": True,
        },
        "mgrsvalues": {
            "mgrs": [
                "51WXU",
                "51WXV",
                "52WDC",
                "52WDD",
                "52WDE",
                "52WEC",
                "52WED",
                "52WEE",
                "52WFC",
                "52WFD",
                "52WFE",
                "53WMU",
                "53WMV",
            ],
            "count": 13,
        },
        "jobinfo": {
            "Error": "States.TaskFailed",
            "Cause": '{"Attempts":[{"Container":{"ContainerInstanceArn":"arn:aws:ecs:us-west-2:018923174646:container-instance/cebc97a6-5c16-4987-9d24-27b96246dcdd","ExitCode":1,"LogStreamName":"LandsatTaskBatchJob1274-131d33be785ce5d/default/7c7cd09e-33c0-44f5-919a-2f66e0b8e995","NetworkInterfaces":[],"TaskArn":"arn:aws:ecs:us-west-2:018923174646:task/7c7cd09e-33c0-44f5-919a-2f66e0b8e995"},"StartedAt":1591403928719,"StatusReason":"Essential container in task exited","StoppedAt":1591403929450}],"Container":{"Command":["export && landsat.sh"],"ContainerInstanceArn":"arn:aws:ecs:us-west-2:018923174646:container-instance/cebc97a6-5c16-4987-9d24-27b96246dcdd","Environment":[{"Name":"PREFIX","Value":"x1/L8/127/010/LC08_L1GT_127010_20200527_20200527_01_RT"},{"Name":"GRANULE","Value":"LC08_L1GT_127010_20200527_20200527_01_RT"},{"Name":"OUTPUT_BUCKET","Value":"hls-development-landsat-intermediate-output"},{"Name":"LASRC_AUX_DIR","Value":"/var/lasrc_aux"},{"Name":"MANAGED_BY_AWS","Value":"STARTED_BY_STEP_FUNCTIONS"},{"Name":"INPUT_BUCKET","Value":"landsat-pds"},{"Name":"REPLACE_EXISTING","Value":"replace"}],"ExitCode":1,"Image":"018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-landsat:latest","JobRoleArn":"arn:aws:iam::018923174646:role/hls-development-LandsatTaskTaskRoleFD2391A2-440VUZKTYZ2O","LogStreamName":"LandsatTaskBatchJob1274-131d33be785ce5d/default/7c7cd09e-33c0-44f5-919a-2f66e0b8e995","Memory":12000,"MountPoints":[{"ContainerPath":"/var/lasrc_aux","ReadOnly":false,"SourceVolume":"volume"},{"ContainerPath":"/var/scratch","ReadOnly":false,"SourceVolume":"scratch_volume"}],"NetworkInterfaces":[],"ResourceRequirements":[],"TaskArn":"arn:aws:ecs:us-west-2:018923174646:task/7c7cd09e-33c0-44f5-919a-2f66e0b8e995","Ulimits":[],"Vcpus":2,"Volumes":[{"Host":{"SourcePath":"/mnt/efs"},"Name":"volume"},{"Host":{"SourcePath":"/scratch"},"Name":"scratch_volume"}]},"CreatedAt":1591403386307,"DependsOn":[],"JobDefinition":"arn:aws:batch:us-west-2:018923174646:job-definition/LandsatTaskBatchJob1274-131d33be785ce5d:2","JobId":"5ce9a71e-2f18-4dd1-b9ac-9d3618774d3f","JobName":"LandsatAcJob","JobQueue":"arn:aws:batch:us-west-2:018923174646:job-queue/BatchJobQueueFD3B0361-88c4344c33bfb4a","Parameters":{},"RetryStrategy":{"Attempts":1},"StartedAt":1591403928719,"Status":"FAILED","StatusReason":"Essential container in task exited","StoppedAt":1591403929450,"Timeout":{"AttemptDurationSeconds":5400}}',
        },
    }
    client.execute_statement.return_value = {}
    handler(event, {})
    args, kwargs = client.execute_statement.call_args
    path = {"name": "path", "value": {"stringValue": "127"}}
    row = {"name": "row", "value": {"stringValue": "010"}}
    acquisition = {"name": "acquisition", "value": {"stringValue": "2020-05-27"}}
    assert path in kwargs["parameters"]
    assert row in kwargs["parameters"]
    assert acquisition in kwargs["parameters"]


@patch("lambda_functions.landsat_ac_logger.hls_landsat_ac_logger.handler.rds_client")
def test_handler(client):
    """Test handler."""
    event = {
        "sensor": "C",
        "satellite": "08",
        "processingCorrectionLevel": "L1TP",
        "path": "116",
        "row": "078",
        "acquisitionYear": "2020",
        "acquisitionMonth": "05",
        "acquisitionDay": "30",
        "processingYear": "2020",
        "processingMonth": "06",
        "processingDay": "08",
        "collectionNumber": "01",
        "collectionCategory": "T1",
        "scene": "LC08_L1TP_116078_20200530_20200608_01_T1",
        "date": "2020-05-30",
        "scheme": "s3",
        "bucket": "landsat-pds",
        "prefix": "c1/L8/116/078/LC08_L1TP_116078_20200530_20200608_01_T1",
        "taskresult": {
            "granule": "LC08_L1TP_116078_20200530_20200608_01_T1",
            "year": "2020",
            "doy": "2020151",
            "bucket": "hls-development-laads-bucket",
            "key": "lasrc_aux/LADS/2020/L8ANC2020151.hdf_fused",
            "available": True,
        },
        "mgrsvalues": {
            "mgrs": [
                "49JDL",
                "49JDM",
                "49JEL",
                "49JEM",
                "49JEN",
                "49JFL",
                "49JFM",
                "49JFN",
            ],
            "count": 8,
        },
        "jobinfo": {
            "Attempts": [
                {
                    "Container": {
                        "ContainerInstanceArn": "arn:aws:ecs:us-west-2:018923174646:container-instance/12299235-2d73-4d5a-834a-b430bfc322f0",
                        "ExitCode": 0,
                        "LogStreamName": "LandsatTaskBatchJob1274-131d33be785ce5d/default/9ff13470-d69d-43ad-91c1-3c152b7d9b71",
                        "NetworkInterfaces": [],
                        "TaskArn": "arn:aws:ecs:us-west-2:018923174646:task/9ff13470-d69d-43ad-91c1-3c152b7d9b71",
                    },
                    "StartedAt": 1591642847276,
                    "StatusReason": "Essential container in task exited",
                    "StoppedAt": 1591643191409,
                }
            ],
            "Container": {
                "Command": ["export && landsat.sh"],
                "ContainerInstanceArn": "arn:aws:ecs:us-west-2:018923174646:container-instance/12299235-2d73-4d5a-834a-b430bfc322f0",
                "Environment": [
                    {
                        "Name": "PREFIX",
                        "Value": "c1/L8/116/078/LC08_L1TP_116078_20200530_20200608_01_T1",
                    },
                    {
                        "Name": "GRANULE",
                        "Value": "LC08_L1TP_116078_20200530_20200608_01_T1",
                    },
                    {
                        "Name": "OUTPUT_BUCKET",
                        "Value": "hls-development-landsat-intermediate-output",
                    },
                    {"Name": "LASRC_AUX_DIR", "Value": "/var/lasrc_aux"},
                    {"Name": "MANAGED_BY_AWS", "Value": "STARTED_BY_STEP_FUNCTIONS"},
                    {"Name": "INPUT_BUCKET", "Value": "landsat-pds"},
                    {"Name": "REPLACE_EXISTING", "Value": "replace"},
                ],
                "ExitCode": 0,
                "Image": "018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-landsat:latest",
                "JobRoleArn": "arn:aws:iam::018923174646:role/hls-development-LandsatTaskTaskRoleFD2391A2-440VUZKTYZ2O",
                "LogStreamName": "LandsatTaskBatchJob1274-131d33be785ce5d/default/9ff13470-d69d-43ad-91c1-3c152b7d9b71",
                "Memory": 12000,
                "MountPoints": [
                    {
                        "ContainerPath": "/var/lasrc_aux",
                        "ReadOnly": False,
                        "SourceVolume": "volume",
                    },
                    {
                        "ContainerPath": "/var/scratch",
                        "ReadOnly": False,
                        "SourceVolume": "scratch_volume",
                    },
                ],
                "NetworkInterfaces": [],
                "ResourceRequirements": [],
                "TaskArn": "arn:aws:ecs:us-west-2:018923174646:task/9ff13470-d69d-43ad-91c1-3c152b7d9b71",
                "Ulimits": [],
                "Vcpus": 2,
                "Volumes": [
                    {"Host": {"SourcePath": "/mnt/efs"}, "Name": "volume"},
                    {"Host": {"SourcePath": "/scratch"}, "Name": "scratch_volume"},
                ],
            },
            "CreatedAt": 1591642241533,
            "DependsOn": [],
            "JobDefinition": "arn:aws:batch:us-west-2:018923174646:job-definition/LandsatTaskBatchJob1274-131d33be785ce5d:2",
            "JobId": "4943679f-2c59-49d3-b048-c1945196851e",
            "JobName": "LandsatAcJob",
            "JobQueue": "arn:aws:batch:us-west-2:018923174646:job-queue/BatchJobQueueFD3B0361-88c4344c33bfb4a",
            "Parameters": {},
            "RetryStrategy": {"Attempts": 1},
            "StartedAt": 1591642847276,
            "Status": "SUCCEEDED",
            "StatusReason": "Essential container in task exited",
            "StoppedAt": 1591643191409,
            "Timeout": {"AttemptDurationSeconds": 5400},
        },
    }
    client.execute_statement.return_value = {}
    handler(event, {})
    args, kwargs = client.execute_statement.call_args
    path = {"name": "path", "value": {"stringValue": "116"}}
    row = {"name": "row", "value": {"stringValue": "078"}}
    acquisition = {"name": "acquisition", "value": {"stringValue": "2020-05-30"}}
    assert path in kwargs["parameters"]
    assert row in kwargs["parameters"]
    assert acquisition in kwargs["parameters"]
