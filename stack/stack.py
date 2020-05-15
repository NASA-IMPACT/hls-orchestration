import os
import json
from aws_cdk import core, aws_stepfunctions, aws_iam, aws_s3
from hlsconstructs.network import Network
from hlsconstructs.s3 import S3
from hlsconstructs.efs import Efs
from hlsconstructs.rds import Rds
from hlsconstructs.docker_batchjob import DockerBatchJob
from hlsconstructs.batch import Batch
from hlsconstructs.lambdafunc import Lambda
from hlsconstructs.batch_cron import BatchCron
from hlsconstructs.dummy_lambda import Dummy
from hlsconstructs.sentinel_step_function import SentinelStepFunction
from hlsconstructs.step_function_trigger import StepFunctionTrigger

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
    "HLS_SENTINEL_INPUT_BUCKET", f"{STACKNAME}-sentinel-input"
)
try:
    MAXV_CPUS = int(os.getenv("HLS_MAXV_CPUS"))
except ValueError:
    MAXV_CPUS = 200

if os.getenv("HLS_REPLACE_EXISTING") == "true":
    REPLACE_EXISTING = True
else:
    REPLACE_EXISTING = False

HLS_SENTINEL_BUCKET_ROLE_ARN = os.getenv("HLS_SENTINEL_BUCKET_ROLE_ARN", None)
HLS_REPLACE_EXISTING = os.getenv("HLS_REPLACE_EXISTING", None)

if LAADS_TOKEN is None:
    raise Exception("HLS_LAADS_TOKEN Env Var must be set")

if HLS_SENTINEL_BUCKET_ROLE_ARN is None:
    raise Exception("HLS_SENTINEL_BUCKET_ROLE_ARN Env Var must be set")


class HlsStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.network = Network(self, "Network")

        self.laads_bucket = S3(self, "LaadsBucket", bucket_name=LAADS_BUCKET)

        # self.sentinel_bucket = S3(self, "SentinelBucket", bucket_name=SENTINEL_BUCKET)
        self.sentinel_bucket = aws_s3.Bucket.from_bucket_name(
            self, f"bucket", SENTINEL_BUCKET
        )
        # Must be created as part of the stack due to trigger requirements
        self.sentinel_input_bucket = aws_s3.Bucket(
            self, "SentinelInputBucket", bucket_name=SENTINEL_INPUT_BUCKET
        )

        self.efs = Efs(self, "Efs", network=self.network)

        self.rds = Rds(self, "Rds", network=self.network)

        self.rds_bootstrap = Lambda(
            self,
            "LambdaDBBootstrap",
            code_file="setupdb.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
            },
            timeout=300,
        )

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
            self,
            "Batch",
            network=self.network,
            efs=self.efs.filesystem,
            maxv_cpus=MAXV_CPUS,
            instance_types=["r5d.large"],
        )

        self.laads_task = DockerBatchJob(
            self,
            "LaadsTask",
            dockerdir="hls-laads",
            bucket=self.laads_bucket.bucket,
            mountpath="/var/lasrc_aux",
            timeout=259200,
            memory=10000,
            vcpus=2,
        )

        self.sentinel_task = DockerBatchJob(
            self,
            "SentinelTask",
            dockeruri=SENTINEL_ECR_URI,
            bucket=self.sentinel_bucket,
            mountpath="/var/lasrc_aux",
            timeout=5400,
            memory=14000,
            vcpus=2,
        )

        self.pr2mgrs_lambda = Lambda(
            self, "Pr2Mgrs", code_dir="pr2mgrs/hls_pr2mgrs", handler="handler.handler",
        )

        self.laads_available = Lambda(
            self,
            "LaadsAvailable",
            code_dir="laads_available/hls_laads_available",
            env={"LAADS_BUCKET": LAADS_BUCKET},
            handler="handler.handler",
        )

        self.check_granule = Lambda(
            self,
            "CheckGranule",
            code_file="twin_granule.py",
            env={"SENTINEL_INPUT_BUCKET": SENTINEL_INPUT_BUCKET},
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

        self.sentinel_step_function = SentinelStepFunction(
            self,
            "SentinelStateMachine",
            check_granule=self.check_granule.function.function_arn,
            laads_available_function=self.laads_available.function.function_arn,
            outputbucket=SENTINEL_BUCKET,
            inputbucket=SENTINEL_INPUT_BUCKET,
            sentinel_job_definition=self.sentinel_task.job.ref,
            jobqueue=self.batch.jobqueue.ref,
            lambda_logger=self.lambda_logger.function.function_arn,
            outputbucket_role_arn=HLS_SENTINEL_BUCKET_ROLE_ARN,
            replace_existing=REPLACE_EXISTING,
        )

        self.step_function_trigger = StepFunctionTrigger(
            self,
            "SentinelStepFunctionTrigger",
            input_bucket=self.sentinel_input_bucket,
            state_machine=self.sentinel_step_function.sentinel_state_machine.ref,
        )

        # Cross construct permissions
        self.laads_bucket_read_policy = aws_iam.PolicyStatement(
            resources=[
                self.laads_bucket.bucket_arn,
                f"{self.laads_bucket.bucket_arn}/*",
            ],
            actions=["s3:Get*", "s3:List*",],
        )
        self.batch_jobqueue_policy = aws_iam.PolicyStatement(
            resources=[self.batch.jobqueue.ref],
            actions=["batch:SubmitJob", "batch:DescribeJobs", "batch:TerminateJob"],
        )
        self.laads_cron.function.add_to_role_policy(self.laads_bucket_read_policy)
        self.laads_available.function.add_to_role_policy(self.laads_bucket_read_policy)
        self.laads_cron.function.add_to_role_policy(self.batch_jobqueue_policy)
        self.laads_cron.function.add_to_role_policy(
            aws_iam.PolicyStatement(
                resources=[self.laads_task.job.ref],
                actions=["batch:SubmitJob", "batch:DescribeJobs", "batch:TerminateJob"],
            )
        )

        self.sentinel_step_function.steps_role.add_to_policy(self.batch_jobqueue_policy)
        self.sentinel_step_function.steps_role.add_to_policy(
            self.check_granule.invoke_policy_statement
        )
        self.sentinel_step_function.steps_role.add_to_policy(
            self.laads_available.invoke_policy_statement
        )
        self.sentinel_step_function.steps_role.add_to_policy(
            self.lambda_logger.invoke_policy_statement
        )
        self.lambda_logger.function.add_to_role_policy(self.rds.policy_statement)
        self.rds_bootstrap.function.add_to_role_policy(self.rds.policy_statement)

        self.check_granule.function.add_to_role_policy(
            aws_iam.PolicyStatement(
                resources=[
                    self.sentinel_input_bucket.bucket_arn,
                    f"{self.sentinel_input_bucket.bucket_arn}/*",
                ],
                actions=["s3:Get*", "s3:List*",],
            )
        )

        self.laads_task.role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[
                    self.laads_bucket.bucket_arn,
                    f"{self.laads_bucket.bucket_arn}/*",
                ],
                actions=["s3:Get*", "s3:Put*", "s3:List*", "s3:AbortMultipartUpload",],
            )
        )
        self.sentinel_task.role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[
                    self.sentinel_input_bucket.bucket_arn,
                    f"{self.sentinel_input_bucket.bucket_arn}/*",
                ],
                actions=["s3:Get*", "s3:List*",],
            )
        )
        self.batch.ecs_instance_role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[HLS_SENTINEL_BUCKET_ROLE_ARN], actions=["sts:AssumeRole"],
            )
        )

        # Add policies for Lambda to listen for bucket events and trigger step
        # function
        cw_events_full = aws_iam.ManagedPolicy.from_managed_policy_arn(
            self, "cweventsfull", "arn:aws:iam::aws:policy/CloudWatchEventsFullAccess"
        )
        self.sentinel_step_function.steps_role.add_managed_policy(cw_events_full)

        # Stack exports
        core.CfnOutput(
            self,
            "jobqueueexport",
            export_name=f"{STACKNAME}-jobqueue",
            value=self.batch.jobqueue.ref,
        )
        core.CfnOutput(
            self,
            "sentinelstatemachineexport",
            export_name=f"{STACKNAME}-setinelstatemachine",
            value=self.sentinel_step_function.sentinel_state_machine.ref,
        )
        core.CfnOutput(
            self,
            "setupdbexport",
            export_name=f"{STACKNAME}-setupdb",
            value=self.rds_bootstrap.function.function_arn,
        )
        core.CfnOutput(
            self,
            "sentineloutputexport",
            export_name=f"{STACKNAME}-sentineloutput",
            value=self.sentinel_bucket.bucket_name,
        )
        core.CfnOutput(
            self,
            "sentinelinputexport",
            export_name=f"{STACKNAME}-sentinelinput",
            value=self.sentinel_input_bucket.bucket_name,
        )
        core.CfnOutput(
            self,
            "sentineljobdefinition",
            export_name=f"{STACKNAME}-sentineljobdefinition",
            value=self.sentinel_task.job.ref,
        )
