import sys

import boto3

image = sys.argv[1]
pr_number = sys.argv[2]

if image == "hls-laads":
    role_arn = "arn:aws:iam::018923174646:role/hls-development-LaadsTaskTaskRoleC8A42E20-2V99O0N3RMJ0"
if image == "hls-sentinel":
    role_arn = "arn:aws:iam::018923174646:role/hls-development-SentinelTaskTaskRoleEB97BB3F-1AIL1PXLA4JKJ"
if image == "hls-landsat-c2":
    role_arn = "arn:aws:iam::018923174646:role/hls-development-LandsatTaskTaskRoleFD2391A2-440VUZKTYZ2O"


client = boto3.client("batch")
response = client.register_job_definition(
    jobDefinitionName=f"{image}_{pr_number}",
    type="container",
    containerProperties={
        "image": f"018923174646.dkr.ecr.us-west-2.amazonaws.com/{image}:{pr_number}",
        "vcpus": 2,
        "memory": 10000,
        "command": [],
        "jobRoleArn": role_arn,
        "volumes": [
            {"host": {"sourcePath": "/mnt/efs"}, "name": "volume"},
            {"host": {"sourcePath": "/scratch"}, "name": "scratch_volume"},
        ],
        "mountPoints": [
            {
                "containerPath": "/var/lasrc_aux",
                "readOnly": False,
                "sourceVolume": "volume",
            },
            {
                "containerPath": "/var/scratch",
                "readOnly": False,
                "sourceVolume": "scratch_volume",
            },
        ],
    },
    timeout={"attemptDurationSeconds": 259200},
)
print(response["jobDefinitionArn"])
