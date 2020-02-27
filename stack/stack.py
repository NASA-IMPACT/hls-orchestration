import os
import json
from aws_cdk import core, aws_stepfunctions, aws_iam
from constructs.network import Network
from constructs.s3 import S3
from constructs.efs import Efs
from constructs.rds import Rds
from constructs.docker_batchjob import DockerBatchJob
from constructs.batch import Batch
from constructs.lambdafunc import Lambda
from constructs.batch_cron import BatchCron
from constructs.dummy_lambda import Dummy

STACKNAME = os.getenv("HLS_STACKNAME", "hls")
LAADS_BUCKET = os.getenv("HLS_LAADS_BUCKET", f"{STACKNAME}-bucket")
LAADS_TOKEN = os.getenv("HLS_LAADS_TOKEN", None)
LAADS_CRON = os.getenv("HLS_LAADS_CRON", "cron(0 0/12 * * ? *)")
LAADS_BUCKET_BOOTSTRAP = LAADS_BUCKET
SENTINEL_ECR_URI = os.getenv(
    "HLS_SENTINEL_ECR_URI",
    "018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-sentinel:latest",
)
SENTINEL_BUCKET = os.getenv("HLS_SENTINEL_BUCKET", f"{STACKNAME}-sentinel-output")

if LAADS_TOKEN is None:
    raise Exception("HLS_LAADS_TOKEN Env Var must be set")


class HlsStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.network = Network(self, "Network")

        self.laads_bucket = S3(self, "LaadsBucket", bucket_name=LAADS_BUCKET)

        self.sentinel_bucket = S3(self, "SentinelBucket", bucket_name=SENTINEL_BUCKET)

        self.efs = Efs(self, "Efs", network=self.network)

        self.rds = Rds(self, "Rds", network=self.network)

        self.lambda_logger = Lambda(
            self,
            "LambdaLogger",
            code_file="logger.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
            },
            timeout=30,
        )

        self.batch = Batch(
            self, "Batch", network=self.network, efs=self.efs.filesystem,
        )

        self.laads_task = DockerBatchJob(
            self,
            "LaadsTask",
            dockerdir="hls-laads",
            bucket=self.laads_bucket.bucket,
            mountpath="/var/lasrc_aux",
            timeout=259200,
            memory=10000,
            vcpus=4,
        )

        self.sentinel_task = DockerBatchJob(
            self,
            "SentinelTask",
            dockeruri=SENTINEL_ECR_URI,
            bucket=self.sentinel_bucket.bucket,
            mountpath="/var/lasrc_aux",
            timeout=3600,
            memory=10000,
            vcpus=4,
        )

        self.pr2mgrs_lambda = Lambda(
            self, "Pr2Mgrs", code_dir="pr2mgrs/hls_pr2mgrs", handler="handler.handler",
        )

        self.laads_available = Lambda(
            self,
            "LaadsAvailable",
            code_dir="laads-available/hls_laads_available",
            env={"LAADS_BUCKET": LAADS_BUCKET},
            handler="handler.handler",
        )

        self.laads_cron = BatchCron(
            self,
            "LaadsAvailableCron",
            cron_str=LAADS_CRON,
            batch=self.batch,
            job=self.laads_task,
            env={
                "LAADS_BUCKET": LAADS_BUCKET,
                "L8_AUX_DIR": "/var/lasrc_aux",
                "LAADS_TOKEN": LAADS_TOKEN,
                "LAADS_BUCKET_BOOTSTRAP": LAADS_BUCKET_BOOTSTRAP,
            },
        )

        self.process_sentinel = Dummy(self, "ProcessSentinelTask",)

        sentinel_state_definition = {
            "Comment": "Sentinel Step Function",
            "StartAt": "CheckLaads",
            "States": {
                "CheckLaads": {
                    "Type": "Task",
                    "Resource": self.laads_available.function.function_arn,
                    "ResultPath": "$",
                    "Next": "LaadsAvailable",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": 1,
                            "MaxAttempts": 3,
                            "BackoffRate": 2,
                        }
                    ],
                },
                "LaadsAvailable": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.available",
                            "BooleanEquals": True,
                            "Next": "ProcessSentinel",
                        }
                    ],
                    "Default": "Wait",
                },
                "Wait": {"Type": "Wait", "Seconds": 3600, "Next": "CheckLaads"},
                "ProcessSentinel": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::batch:submitJob.sync",
                    "ResultPath": "$",
                    "Parameters": {
                        "JobName": "ProcessSentinel",
                        "JobQueue": self.batch.jobqueue.ref,
                        "JobDefinition": self.sentinel_task.job.ref,
                        "ContainerOverrides": {
                            "Command": ["ls /var/lasrc_aux && sentinel.sh"],
                            "Memory": 10000,
                            "Environment": [
                                {"Name": "GRANULE_LIST", "Value.$": "$.granule"},
                                {"Name": "OUTPUT_BUCKET", "Value": SENTINEL_BUCKET},
                                {"Name": "LASRC_AUX_DIR", "Value": "/var/lasrc_aux"},
                            ],
                        },
                    },
                    "Catch": [
                        {"ErrorEquals": ["States.ALL"], "Next": "LogProcessSentinel"}
                    ],
                    "Next": "LogProcessSentinel",
                },
                "LogProcessSentinel": {
                    "Type": "Task",
                    "Resource": self.lambda_logger.function.function_arn,
                    "ResultPath": "$",
                    "Next": "Done",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": 1,
                            "MaxAttempts": 3,
                            "BackoffRate": 2,
                        }
                    ],
                },
                "Done": {"Type": "Succeed"},
            },
        }

        self.steps_role = aws_iam.Role(
            self,
            "StepsRole",
            assumed_by=aws_iam.ServicePrincipal("states.amazonaws.com"),
        )

        self.sentinel_state = aws_stepfunctions.CfnStateMachine(
            self,
            "SentinelStateMachine",
            definition_string=json.dumps(sentinel_state_definition),
            role_arn=self.steps_role.role_arn,
        )

        core.CfnOutput(
            self,
            "SentinelState",
            value=self.sentinel_state.ref,
            export_name="SentinelState",
        )

        # permissions
        self.laads_cron.function.add_to_role_policy(self.laads_task.policy_statement)
        self.laads_cron.function.add_to_role_policy(self.batch.policy_statement)
        self.laads_cron.function.add_to_role_policy(self.laads_bucket.policy_statement)

        self.lambda_logger.function.add_to_role_policy(self.rds.policy_statement)

        self.laads_available.function.add_to_role_policy(
            self.laads_bucket.policy_statement
        )

        self.steps_role.add_to_policy(self.laads_available.policy_statement)
        self.steps_role.add_to_policy(self.sentinel_task.policy_statement)
        self.steps_role.add_to_policy(self.lambda_logger.policy_statement)

        region = core.Aws.REGION
        acountid = core.Aws.ACCOUNT_ID
        self.steps_role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[
                    f"arn:aws:events:{region}:{acountid}:rule/StepFunctionsGetEventsForBatchJobsRule",
                ],
                actions=["events:PutTargets", "events:PutRule", "events:DescribeRule"],
            )
        )
        self.steps_role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=["*",],
                actions=["batch:SubmitJob", "batch:DescribeJobs", "batch:TerminateJob"],
            )
        )
