import os
import json
from aws_cdk import core, aws_stepfunctions, aws_iam
from constructs.network import Network
from constructs.s3 import S3
from constructs.efs import Efs
from constructs.docker_batchjob import DockerBatchJob
from constructs.batch import Batch
from constructs.lambdafunc import Lambda
from constructs.batch_event import BatchCron
from constructs.dummy_lambda import Dummy

STACKNAME = os.getenv("STACKNAME", "hls")
LAADS_BUCKET = os.getenv("LAADS_BUCKET", f"{STACKNAME}-bucket")
LAADS_TOKEN = os.getenv("LAADS_TOKEN", None)
LAADS_CRON = os.getenv("LAADS_CRON", "cron(0 0/12 * * ? *)")


if LAADS_TOKEN is None:
    raise Exception("LAADS_TOKEN Env Var must be set")


class HlsStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.role = aws_iam.Role(
            self,
            "StackRole",
            assumed_by=aws_iam.OrganizationPrincipal(
                organization_id=core.Aws.ACCOUNT_ID
            )
        )
        self.role.grant_pass_role(aws_iam.ServicePrincipal("batch.amazonaws.com"))

        self.network = Network(self, "Network")

        self.laads_bucket = S3(self, "S3", bucket_name=LAADS_BUCKET, role=self.role)

        self.efs = Efs(self, "Efs", network=self.network, role=self.role)

        self.batch = Batch(
            self,
            "Batch",
            network=self.network,
            role=self.role,
            efs=self.efs.filesystem,
        )

        self.laads_task = DockerBatchJob(
            self,
            "LaadsTask",
            role=self.role,
            dockerdir="hls-laads",
            bucket=self.laads_bucket.bucket,
            mountpath="/var/lasrc_aux",
            timeout=259200,
            memory=10000,
            vcpus=4,
        )

        self.pr2mgrs_lambda = Lambda(
            self, "Pr2Mgrs", role=self.role, asset_dir="hls-pr2mgrs/hls_pr2mgrs"
        )

        self.laads_available = Lambda(
            self,
            "LaadsAvailable",
            role=self.role,
            asset_dir="hls-laads-available/hls_laads_available",
            env={"LAADS_BUCKET": LAADS_BUCKET},
        )

        self.laads_cron = BatchCron(
            self,
            "LaadsAvailableCron",
            role=self.role,
            cron_str=LAADS_CRON,
            batch=self.batch,
            job=self.laads_task,
            env={
                "LAADS_BUCKET": LAADS_BUCKET,
                "L8_AUX_DIR": "/var/lasrc_aux",
                "LAADS_TOKEN": LAADS_TOKEN,
            },
        )

        self.process_sentinel = Dummy(
            self,
            'ProcessSentinelTask',
            role=self.role
        )

        sentinel_state_definition = {
            "Comment": "Sentinel Step Function",
            "StartAt": "CheckLaads",
            "States": {
                "CheckLaads": {
                    "Type": "Task",
                    "Resource": self.laads_available.lambdaFn.function_arn,
                    "ResultPath": "$.available",
                    "Next": "LaadsAvailable",
                    "Retry": [
                        {
                        "ErrorEquals": ["States.ALL"],
                        "IntervalSeconds": 1,
                        "MaxAttempts": 3,
                        "BackoffRate": 2
                        }
                    ]
                },
                "LaadsAvailable": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.available",
                            "BooleanEquals": True,
                            "Next": "ProcessSentinel"
                        }
                    ],
                    "Default": "Wait"
                },
                "Wait": {
                    "Type": "Wait",
                    "Seconds": 3600,
                    "Next": "CheckLaads"
                },
                "ProcessSentinel": {
                    "Type": "Task",
                    "Resource": self.process_sentinel.lambdaFn.function_arn,
                    "Next": "Done",
                    "InputPath": "$.available",
                    "ResultPath": "$.available",
                    "Retry": [
                        {
                        "ErrorEquals": ["States.ALL"],
                        "IntervalSeconds": 1,
                        "MaxAttempts": 3,
                        "BackoffRate": 2
                        }
                    ]
                },
                "Done": {
                    "Type": "Succeed"
                }
            }
        }

        sentinel_state = aws_stepfunctions.CfnStateMachine(
            self,
            'SentinelStateMachine',
            definition_string=json.dumps(sentinel_state_definition),
            role_arn=self.role.role_arn,
        )
