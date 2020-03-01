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
from constructs.sentinel_step_function import SentinelStepFunction
from constructs.step_function_trigger import StepFunctionTrigger

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
SENTINEL_INPUT_BUCKET = os.getenv(
    "HLS_SENTINEL_INPUT_BUCKET",
    f"{STACKNAME}-sentinel-input"
)

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

        self.sentinel_step_function = SentinelStepFunction(
            self,
            "SentinelStateMachine",
            laads_available_function=self.laads_available.function.function_arn,
            outputbucket=SENTINEL_BUCKET,
            inputbucket=SENTINEL_INPUT_BUCKET,
            sentinel_job_definition=self.sentinel_task.job.ref,
            jobqueue=self.batch.jobqueue.ref,
        )

        self.step_function_trigger = StepFunctionTrigger(
            self,
            "SentinelStepFunctionTrigger",
            input_bucket_name=SENTINEL_INPUT_BUCKET,
            state_machine=self.sentinel_step_function.sentinel_state_machine.ref
        )

        # Cross construct permissions
        self.laads_cron.function.add_to_role_policy(self.laads_task.policy_statement)
        self.laads_cron.function.add_to_role_policy(self.batch.policy_statement)
        self.laads_cron.function.add_to_role_policy(self.laads_bucket.policy_statement)
        self.laads_available.function.add_to_role_policy(
            self.laads_bucket.policy_statement
        )
        self.sentinel_step_function.steps_role.add_to_policy(
            self.laads_available.policy_statement
        )
        self.sentinel_step_function.steps_role.add_to_policy(
            self.sentinel_task.policy_statement
        )

        self.sentinel_task.role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[
                    self.step_function_trigger.bucket.bucket_arn,
                    f"{self.step_function_trigger.bucket.bucket_arn}/*",
                ],
                actions=["s3:Get*", "s3:Put*", "s3:List*", "s3:AbortMultipartUpload",],
            )
        )
        # Stack exports
        core.CfnOutput(self, "jobqueueexport", export_name=f"{STACKNAME}-jobqueue",
                       value=self.batch.jobqueue.ref)
        core.CfnOutput(self, "sentinelstatemachineexport",
                       export_name=f"{STACKNAME}-setinelstatemachine",
                       value=self.sentinel_step_function.sentinel_state_machine.ref)
