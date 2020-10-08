batch_failed_event = {
    "Error": "States.TaskFailed",
    "Cause": '{"Attempts":[{"Container":{"ContainerInstanceArn":"arn:aws:ecs:us-west-2:018923174646:container-instance/cebc97a6-5c16-4987-9d24-27b96246dcdd","ExitCode":1,"LogStreamName":"LandsatTaskBatchJob1274-131d33be785ce5d/default/7c7cd09e-33c0-44f5-919a-2f66e0b8e995","NetworkInterfaces":[],"TaskArn":"arn:aws:ecs:us-west-2:018923174646:task/7c7cd09e-33c0-44f5-919a-2f66e0b8e995"},"StartedAt":1591403928719,"StatusReason":"Essential container in task exited","StoppedAt":1591403929450}],"Container":{"Command":["export && landsat.sh"],"ContainerInstanceArn":"arn:aws:ecs:us-west-2:018923174646:container-instance/cebc97a6-5c16-4987-9d24-27b96246dcdd","Environment":[{"Name":"PREFIX","Value":"x1/L8/127/010/LC08_L1GT_127010_20200527_20200527_01_RT"},{"Name":"GRANULE","Value":"LC08_L1GT_127010_20200527_20200527_01_RT"},{"Name":"OUTPUT_BUCKET","Value":"hls-development-landsat-intermediate-output"},{"Name":"LASRC_AUX_DIR","Value":"/var/lasrc_aux"},{"Name":"MANAGED_BY_AWS","Value":"STARTED_BY_STEP_FUNCTIONS"},{"Name":"INPUT_BUCKET","Value":"landsat-pds"},{"Name":"REPLACE_EXISTING","Value":"replace"}],"ExitCode":1,"Image":"018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-landsat:latest","JobRoleArn":"arn:aws:iam::018923174646:role/hls-development-LandsatTaskTaskRoleFD2391A2-440VUZKTYZ2O","LogStreamName":"LandsatTaskBatchJob1274-131d33be785ce5d/default/7c7cd09e-33c0-44f5-919a-2f66e0b8e995","Memory":12000,"MountPoints":[{"ContainerPath":"/var/lasrc_aux","ReadOnly":false,"SourceVolume":"volume"},{"ContainerPath":"/var/scratch","ReadOnly":false,"SourceVolume":"scratch_volume"}],"NetworkInterfaces":[],"ResourceRequirements":[],"TaskArn":"arn:aws:ecs:us-west-2:018923174646:task/7c7cd09e-33c0-44f5-919a-2f66e0b8e995","Ulimits":[],"Vcpus":2,"Volumes":[{"Host":{"SourcePath":"/mnt/efs"},"Name":"volume"},{"Host":{"SourcePath":"/scratch"},"Name":"scratch_volume"}]},"CreatedAt":1591403386307,"DependsOn":[],"JobDefinition":"arn:aws:batch:us-west-2:018923174646:job-definition/LandsatTaskBatchJob1274-131d33be785ce5d:2","JobId":"5ce9a71e-2f18-4dd1-b9ac-9d3618774d3f","JobName":"LandsatAcJob","JobQueue":"arn:aws:batch:us-west-2:018923174646:job-queue/BatchJobQueueFD3B0361-88c4344c33bfb4a","Parameters":{},"RetryStrategy":{"Attempts":1},"StartedAt":1591403928719,"Status":"FAILED","StatusReason":"Essential container in task exited","StoppedAt":1591403929450,"Timeout":{"AttemptDurationSeconds":5400}}',
}

batch_succeeded_event = {
    "Attempts": [
        {
            "Container": {
                "ContainerInstanceArn": "arn:aws:ecs:us-west-2:018923174646:container-instance/5c5f7557-0718-41fc-a6c9-ce7e6890cba7",
                "ExitCode": 0,
                "LogStreamName": "SentinelTaskBatchJobDE3-581008467128b6c/default/0abee2be-68b1-4d15-a862-97ede019db95",
                "NetworkInterfaces": [],
                "TaskArn": "arn:aws:ecs:us-west-2:018923174646:task/0abee2be-68b1-4d15-a862-97ede019db95"
            },
            "StartedAt": 1601068570556,
            "StatusReason": "Essential container in task exited",
            "StoppedAt": 1601069627539
        }
    ],
    "Container": {
        "Command": [
            "export && sentinel.sh"
        ],
        "ContainerInstanceArn": "arn:aws:ecs:us-west-2:018923174646:container-instance/5c5f7557-0718-41fc-a6c9-ce7e6890cba7",
        "Environment": [
            {
                "Name": "GIBS_INTERMEDIATE_BUCKET",
                "Value": "hls-development-gibs-intermediate-output"
            },
            {
                "Name": "GRANULE_LIST",
                "Value": "S2A_MSIL1C_20200708T232851_N0209_R044_T58LEP_20200709T005119"
            },
            {
                "Name": "GIBS_OUTPUT_BUCKET",
                "Value": "hls-browse-imagery"
            },
            {
                "Name": "OUTPUT_BUCKET",
                "Value": "hls-global"
            },
            {
                "Name": "LASRC_AUX_DIR",
                "Value": "/var/lasrc_aux"
            },
            {
                "Name": "MANAGED_BY_AWS",
                "Value": "STARTED_BY_STEP_FUNCTIONS"
            },
            {
                "Name": "INPUT_BUCKET",
                "Value": "hls-development-sentinel-input-files"
            },
            {
                "Name": "GCC_ROLE_ARN",
                "Value": "wat"
            },
            {
                "Name": "REPLACE_EXISTING",
                "Value": "replace"
            },
            {
                "Name": "OMP_NUM_THREADS",
                "Value": "2"
            }
        ],
        "ExitCode": 0,
        "Image": "018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-sentinel:latest",
        "JobRoleArn": "wat",
        "LogStreamName": "SentinelTaskBatchJobDE3-581008467128b6c/default/0abee2be-68b1-4d15-a862-97ede019db95",
        "Memory": 15000,
        "MountPoints": [
            {
                "ContainerPath": "/var/lasrc_aux",
                "ReadOnly": False,
                "SourceVolume": "volume"
            },
            {
                "ContainerPath": "/var/scratch",
                "ReadOnly": False,
                "SourceVolume": "scratch_volume"
            }
        ],
        "NetworkInterfaces": [],
        "ResourceRequirements": [],
        "TaskArn": "arn:aws:ecs:us-west-2:018923174646:task/0abee2be-68b1-4d15-a862-97ede019db95",
        "Ulimits": [],
        "Vcpus": 2,
        "Volumes": [
            {
                "Host": {
                    "SourcePath": "/mnt/efs"
                },
                "Name": "volume"
            },
            {
                "Host": {
                    "SourcePath": "/scratch"
                },
                "Name": "scratch_volume"
            }
        ]
    },
    "CreatedAt": 1601068222687,
    "DependsOn": [],
    "JobDefinition": "arn:aws:batch:us-west-2:018923174646:job-definition/SentinelTaskBatchJobDE3-581008467128b6c:29",
    "JobId": "d5ce77ea-9d95-4bb9-bf2c-d78da2459e54",
    "JobName": "BatchJobNotification",
    "JobQueue": "arn:aws:batch:us-west-2:018923174646:job-queue/BatchSentinelJobQueue2E-146f7f3ea0ab1d8",
    "Parameters": {},
    "RetryStrategy": {
        "Attempts": 1
    },
    "StartedAt": 1601068570556,
    "Status": "SUCCEEDED",
    "StatusReason": "Essential container in task exited",
    "StoppedAt": 1601069627539,
    "Timeout": {
        "AttemptDurationSeconds": 7200
    }
}

batch_failed_event_string_cause = {
    "Error": "States.TaskFailed",
    "Cause": "A cause message",
}

batch_failed_event_no_exit = {
    "Error": "States.TaskFailed",
    "Cause": "{\"Attempts\":[{\"Container\":{\"ContainerInstanceArn\":\"arn:aws:ecs:us-west-2:018923174646:container-instance/1dae44b8-6760-4ded-b1e8-28e486d3fb27\",\"LogStreamName\":\"LandsatTileTaskBatchJob-b28764e72fd8fa9/default/2b098699-be60-4a6d-9799-34d9ad2fff95\",\"NetworkInterfaces\":[],\"Reason\":\"CannotInspectContainerError: Could not transition to inspecting; timed out after waiting 30s\",\"TaskArn\":\"arn:aws:ecs:us-west-2:018923174646:task/2b098699-be60-4a6d-9799-34d9ad2fff95\"},\"StartedAt\":1601908336075,\"StatusReason\":\"Essential container in task exited\",\"StoppedAt\":1601908513034}],\"Container\":{\"Command\":[\"export && landsat-tile.sh\"],\"ContainerInstanceArn\":\"arn:aws:ecs:us-west-2:018923174646:container-instance/1dae44b8-6760-4ded-b1e8-28e486d3fb27\",\"Environment\":[{\"Name\":\"DATE\",\"Value\":\"2020-10-02\"},{\"Name\":\"LANDSAT_PATH\",\"Value\":\"127\"},{\"Name\":\"PATHROW_LIST\",\"Value\":\"127025\"},{\"Name\":\"OUTPUT_BUCKET\",\"Value\":\"hls-global\"},{\"Name\":\"MANAGED_BY_AWS\",\"Value\":\"STARTED_BY_STEP_FUNCTIONS\"},{\"Name\":\"INPUT_BUCKET\",\"Value\":\"hls-development-landsat-intermediate-output\"},{\"Name\":\"MGRS_ULX\",\"Value\":\"399960\"},{\"Name\":\"GCC_ROLE_ARN\",\"Value\":\"arn:aws:iam::611670965994:role/gcc-S3Test\"},{\"Name\":\"MGRS_ULY\",\"Value\":\"5600040\"},{\"Name\":\"REPLACE_EXISTING\",\"Value\":\"replace\"},{\"Name\":\"MGRS\",\"Value\":\"50UMA\"}],\"Image\":\"018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-landsat-tile:v1.4\",\"JobRoleArn\":\"arn:aws:iam::018923174646:role/hls-development-LandsatTileTaskTaskRoleB5DB01A1-1J87WOWZF2WUI\",\"LogStreamName\":\"LandsatTileTaskBatchJob-b28764e72fd8fa9/default/2b098699-be60-4a6d-9799-34d9ad2fff95\",\"Memory\":16000,\"MountPoints\":[{\"ContainerPath\":\"/efs\",\"ReadOnly\":false,\"SourceVolume\":\"volume\"},{\"ContainerPath\":\"/var/scratch\",\"ReadOnly\":false,\"SourceVolume\":\"scratch_volume\"}],\"NetworkInterfaces\":[],\"Reason\":\"CannotInspectContainerError: Could not transition to inspecting; timed out after waiting 30s\",\"ResourceRequirements\":[],\"TaskArn\":\"arn:aws:ecs:us-west-2:018923174646:task/2b098699-be60-4a6d-9799-34d9ad2fff95\",\"Ulimits\":[],\"Vcpus\":2,\"Volumes\":[{\"Host\":{\"SourcePath\":\"/mnt/efs\"},\"Name\":\"volume\"},{\"Host\":{\"SourcePath\":\"/scratch\"},\"Name\":\"scratch_volume\"}]},\"CreatedAt\":1601907727127,\"DependsOn\":[],\"JobDefinition\":\"arn:aws:batch:us-west-2:018923174646:job-definition/LandsatTileTaskBatchJob-b28764e72fd8fa9:6\",\"JobId\":\"1cd8414e-676b-4bd7-9aac-ab8788c4e850\",\"JobName\":\"LandsatTileJob\",\"JobQueue\":\"arn:aws:batch:us-west-2:018923174646:job-queue/BatchLandsatTileJobQueu-511e85f94f2b479\",\"Parameters\":{},\"RetryStrategy\":{\"Attempts\":1},\"StartedAt\":1601908336075,\"Status\":\"FAILED\",\"StatusReason\":\"Essential container in task exited\",\"StoppedAt\":1601908513034,\"Timeout\":{\"AttemptDurationSeconds\":5400}}"
}
