import os
import json
from aws_cdk import core, aws_stepfunctions, aws_iam, aws_s3, aws_sns
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
from hlsconstructs.landsat_step_function import LandsatStepFunction
from hlsconstructs.step_function_trigger import StepFunctionTrigger
from hlsconstructs.stepfunction_alarm import StepFunctionAlarm

STACKNAME = os.getenv("HLS_STACKNAME", "hls")

# SENTINEL_ECR_URI = "018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-sentinel:v3.0.4"
SENTINEL_ECR_URI = "018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-sentinel:latest"
LANDSAT_ECR_URI = "018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-landsat:latest"
LANDSAT_TILE_ECR_URI = "018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-landsat-tile:v1.4"

LAADS_BUCKET = f"{STACKNAME}-laads-bucket"
LAADS_TOKEN = os.getenv("HLS_LAADS_TOKEN", None)
LAADS_CRON = os.getenv("HLS_LAADS_CRON", "cron(0 0/12 * * ? *)")
LAADS_BUCKET_BOOTSTRAP = LAADS_BUCKET
if LAADS_TOKEN is None:
    raise Exception("HLS_LAADS_TOKEN Env Var must be set")


SENTINEL_INPUT_BUCKET = f"{STACKNAME}-sentinel-input-files"
SENTINEL_OUTPUT_BUCKET = os.getenv("HLS_SENTINEL_OUTPUT_BUCKET")
HLS_SENTINEL_OUTPUT_BUCKET_ROLE_ARN = os.getenv(
    "HLS_SENTINEL_OUTPUT_BUCKET_ROLE_ARN", None
)
if HLS_SENTINEL_OUTPUT_BUCKET_ROLE_ARN is None:
    raise Exception("HLS_SENTINEL_OUTPUT_BUCKET_ROLE_ARN Env Var must be set")

LANDSAT_SNS_TOPIC = os.getenv("HLS_LANDSAT_SNS_TOPIC",)
LANDSAT_OUTPUT_BUCKET = os.getenv("HLS_LANDSAT_OUTPUT_BUCKET",)
LANDSAT_INTERMEDIATE_OUTPUT_BUCKET = f"{STACKNAME}-landsat-intermediate-output"

GIBS_INTERMEDIATE_OUTPUT_BUCKET = f"{STACKNAME}-gibs-intermediate-output"
GIBS_OUTPUT_BUCKET = os.getenv("HLS_GIBS_OUTPUT_BUCKET")

SSH_KEYNAME = os.getenv("HLS_SSH_KEYNAME")
try:
    # MAXV_CPUS = int(os.getenv("HLS_MAXV_CPUS"))
    MAXV_CPUS = 1200
except ValueError:
    MAXV_CPUS = 200

HLS_REPLACE_EXISTING = os.getenv("HLS_REPLACE_EXISTING", None)
if os.getenv("HLS_REPLACE_EXISTING") == "true":
    REPLACE_EXISTING = True
else:
    REPLACE_EXISTING = False


class HlsStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.network = Network(self, "Network")

        self.laads_bucket = S3(self, "LaadsBucket", bucket_name=LAADS_BUCKET)

        self.sentinel_output_bucket = aws_s3.Bucket.from_bucket_name(
            self, "sentinel_output_bucket", SENTINEL_OUTPUT_BUCKET
        )

        self.landsat_output_bucket = aws_s3.Bucket.from_bucket_name(
            self, "landsat_output_bucket", LANDSAT_OUTPUT_BUCKET
        )

        # Must be created as part of the stack due to trigger requirements
        self.sentinel_input_bucket = aws_s3.Bucket(
            self, "SentinelInputBucket", bucket_name=SENTINEL_INPUT_BUCKET
        )

        self.landsat_intermediate_output_bucket = aws_s3.Bucket(
            self,
            "LandsatIntermediateBucket",
            bucket_name=LANDSAT_INTERMEDIATE_OUTPUT_BUCKET,
        )

        self.gibs_intermediate_output_bucket = aws_s3.Bucket(
            self, "GibsIntermediateBucket", bucket_name=GIBS_INTERMEDIATE_OUTPUT_BUCKET,
        )

        self.landsat_sns_topic = aws_sns.Topic.from_topic_arn(
            self, "LandsatSNSTopc", topic_arn=LANDSAT_SNS_TOPIC
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
            instance_types=["r5d.2xlarge"],
            ssh_keyname=SSH_KEYNAME,
        )

        self.laads_task = DockerBatchJob(
            self,
            "LaadsTask",
            dockerdir="hls-laads",
            mountpath="/var/lasrc_aux",
            timeout=259200,
            memory=10000,
            vcpus=2,
        )

        self.sentinel_task = DockerBatchJob(
            self,
            "SentinelTask",
            dockeruri=SENTINEL_ECR_URI,
            mountpath="/var/lasrc_aux",
            timeout=7200,
            memory=15000,
            vcpus=2,
        )

        self.landsat_task = DockerBatchJob(
            self,
            "LandsatTask",
            dockeruri=LANDSAT_ECR_URI,
            mountpath="/var/lasrc_aux",
            timeout=5400,
            memory=15000,
            vcpus=2,
        )

        self.landsat_tile_task = DockerBatchJob(
            self,
            "LandsatTileTask",
            dockeruri=LANDSAT_TILE_ECR_URI,
            timeout=5400,
            memory=16000,
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

        self.check_twin_granule = Lambda(
            self,
            "CheckGranule",
            code_file="twin_granule.py",
            env={"SENTINEL_INPUT_BUCKET": SENTINEL_INPUT_BUCKET},
        )

        self.landsat_mgrs_logger = Lambda(
            self,
            "LandsatMGRSLogger",
            code_dir="landsat_mgrs_logger/hls_landsat_mgrs_logger",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
            },
            timeout=30,
            handler="handler.handler",
        )

        self.mgrs_logger = Lambda(
            self,
            "MGRSLogger",
            code_dir="mgrs_logger/hls_mgrs_logger",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
            },
            timeout=30,
            handler="handler.handler",
        )

        self.landsat_ac_logger = Lambda(
            self,
            "LandsatAcLogger",
            code_dir="landsat_ac_logger/hls_landsat_ac_logger",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
            },
            timeout=30,
            handler="handler.handler",
        )

        self.landsat_pathrow_status = Lambda(
            self,
            "LandsatPathrowStatus",
            code_dir="landsat_pathrow_status/hls_landsat_pathrow_status",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
            },
            timeout=30,
            handler="handler.handler",
        )

        self.check_landsat_tiling_exit_code = Lambda(
            self,
            "CheckLandsatTilingExitCode",
            code_dir="check_landsat_tiling_exit_code/hls_check_landsat_tiling_exit_code",
            timeout=30,
            handler="handler.handler"
        )

        self.check_exit_code = Lambda(
            self,
            "CheckExitCode",
            code_dir="check_exit_code/hls_check_exit_code",
            timeout=30,
            handler="handler.handler"
        )

        self.laads_cron = BatchCron(
            self,
            "LaadsCron",
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
            check_twin_granule=self.check_twin_granule.function.function_arn,
            laads_available_function=self.laads_available.function.function_arn,
            outputbucket=SENTINEL_OUTPUT_BUCKET,
            inputbucket=SENTINEL_INPUT_BUCKET,
            sentinel_job_definition=self.sentinel_task.job.ref,
            jobqueue=self.batch.jobqueue.ref,
            lambda_logger=self.lambda_logger.function.function_arn,
            outputbucket_role_arn=HLS_SENTINEL_OUTPUT_BUCKET_ROLE_ARN,
            replace_existing=REPLACE_EXISTING,
            gibs_intermediate_output_bucket=GIBS_INTERMEDIATE_OUTPUT_BUCKET,
            gibs_outputbucket=GIBS_OUTPUT_BUCKET,
        )

        self.landsat_step_function = LandsatStepFunction(
            self,
            "LandsatStateMachine",
            laads_available_function=self.laads_available.function.function_arn,
            outputbucket=LANDSAT_OUTPUT_BUCKET,
            outputbucket_role_arn=HLS_SENTINEL_OUTPUT_BUCKET_ROLE_ARN,
            intermediate_output_bucket=LANDSAT_INTERMEDIATE_OUTPUT_BUCKET,
            ac_job_definition=self.landsat_task.job.ref,
            tile_job_definition=self.landsat_tile_task.job.ref,
            jobqueue=self.batch.jobqueue.ref,
            lambda_logger=self.lambda_logger.function.function_arn,
            landsat_mgrs_logger=self.landsat_mgrs_logger.function.function_arn,
            landsat_ac_logger=self.landsat_ac_logger.function.function_arn,
            landsat_pathrow_status=self.landsat_pathrow_status.function.function_arn,
            pr2mgrs=self.pr2mgrs_lambda.function.function_arn,
            mgrs_logger=self.mgrs_logger.function.function_arn,
            check_landsat_tiling_exit_code=self.check_landsat_tiling_exit_code.function.function_arn,
            check_landsat_ac_exit_code=self.check_exit_code.function.function_arn,
            replace_existing=REPLACE_EXISTING,
        )

        self.step_function_trigger = StepFunctionTrigger(
            self,
            "SentinelStepFunctionTrigger",
            state_machine=self.sentinel_step_function.sentinel_state_machine.ref,
            code_dir="execute_step_function/hls_execute_step_function",
            input_bucket=self.sentinel_input_bucket,
        )
        self.landsat_step_function_trigger = StepFunctionTrigger(
            self,
            "LandsatStepFunctionTrigger",
            state_machine=self.landsat_step_function.state_machine.ref,
            code_dir="execute_landsat_step_function/hls_execute_landsat_step_function",
            input_sns=self.landsat_sns_topic,
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
            self.check_twin_granule.invoke_policy_statement
        )
        self.sentinel_step_function.steps_role.add_to_policy(
            self.laads_available.invoke_policy_statement
        )
        self.sentinel_step_function.steps_role.add_to_policy(
            self.lambda_logger.invoke_policy_statement
        )

        self.landsat_step_function.steps_role.add_to_policy(self.batch_jobqueue_policy)
        self.landsat_step_function.steps_role.add_to_policy(
            self.laads_available.invoke_policy_statement
        )
        self.landsat_step_function.steps_role.add_to_policy(
            self.lambda_logger.invoke_policy_statement
        )
        self.landsat_step_function.steps_role.add_to_policy(
            self.landsat_mgrs_logger.invoke_policy_statement
        )
        self.landsat_step_function.steps_role.add_to_policy(
            self.pr2mgrs_lambda.invoke_policy_statement
        )
        self.landsat_step_function.steps_role.add_to_policy(
            self.landsat_ac_logger.invoke_policy_statement
        )
        self.landsat_step_function.steps_role.add_to_policy(
            self.landsat_pathrow_status.invoke_policy_statement
        )
        self.landsat_step_function.steps_role.add_to_policy(
            self.mgrs_logger.invoke_policy_statement
        )
        self.landsat_step_function.steps_role.add_to_policy(
            self.check_landsat_tiling_exit_code.invoke_policy_statement
        )
        self.landsat_step_function.steps_role.add_to_policy(
            self.check_exit_code.invoke_policy_statement
        )

        self.lambda_logger.function.add_to_role_policy(self.rds.policy_statement)
        self.rds_bootstrap.function.add_to_role_policy(self.rds.policy_statement)
        self.landsat_mgrs_logger.function.add_to_role_policy(self.rds.policy_statement)
        self.landsat_ac_logger.function.add_to_role_policy(self.rds.policy_statement)
        self.mgrs_logger.function.add_to_role_policy(self.rds.policy_statement)
        self.landsat_pathrow_status.function.add_to_role_policy(
            self.rds.policy_statement
        )

        self.check_twin_granule.function.add_to_role_policy(
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
        self.sentinel_task.role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[
                    self.gibs_intermediate_output_bucket.bucket_arn,
                    f"{self.gibs_intermediate_output_bucket.bucket_arn}/*",
                ],
                actions=["s3:Get*", "s3:Put*", "s3:List*", "s3:AbortMultipartUpload",],
            )
        )
        self.landsat_task.role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[
                    self.landsat_intermediate_output_bucket.bucket_arn,
                    f"{self.landsat_intermediate_output_bucket.bucket_arn}/*",
                ],
                actions=["s3:Get*", "s3:Put*", "s3:List*", "s3:AbortMultipartUpload",],
            )
        )
        self.landsat_task.role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=["arn:aws:s3:::landsat-pds", "arn:aws:s3:::landsat-pds/*",],
                actions=["s3:Get*", "s3:List*",],
            )
        )
        self.landsat_tile_task.role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[
                    self.landsat_intermediate_output_bucket.bucket_arn,
                    f"{self.landsat_intermediate_output_bucket.bucket_arn}/*",
                ],
                actions=["s3:Get*", "s3:List*",],
            )
        )
        self.batch.ecs_instance_role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[HLS_SENTINEL_OUTPUT_BUCKET_ROLE_ARN],
                actions=["sts:AssumeRole"],
            )
        )

        # Add policies for Lambda to listen for bucket events and trigger step
        # function
        cw_events_full = aws_iam.ManagedPolicy.from_managed_policy_arn(
            self, "cweventsfull", "arn:aws:iam::aws:policy/CloudWatchEventsFullAccess"
        )
        self.sentinel_step_function.steps_role.add_managed_policy(cw_events_full)

        # Alarms
        self.sentinel_step_function_alarm = StepFunctionAlarm(
            self,
            "SentinelStepFunctionAlarm",
            state_machine=self.sentinel_step_function.sentinel_state_machine.ref,
            root_name="Sentinel",
        )

        self.landsat_step_function_alarm = StepFunctionAlarm(
            self,
            "LandsatStepFunctionAlarm",
            state_machine=self.landsat_step_function.state_machine.ref,
            root_name="Landsat",
        )

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
            value=self.sentinel_output_bucket.bucket_name,
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
        core.CfnOutput(
            self,
            "landsatintermediateoutput",
            export_name=f"{STACKNAME}-landsatintermediateoutput",
            value=self.landsat_intermediate_output_bucket.bucket_name,
        )
        core.CfnOutput(
            self,
            "landsatjobdefinition",
            export_name=f"{STACKNAME}-landsatjobdefinition",
            value=self.landsat_task.job.ref,
        )
        core.CfnOutput(
            self,
            "landsattilejobdefinition",
            export_name=f"{STACKNAME}-landsattilejobdefinition",
            value=self.landsat_tile_task.job.ref,
        )
        core.CfnOutput(
            self,
            "gibsintermediateoutput",
            export_name=f"{STACKNAME}-gibsintermediateoutput",
            value=self.gibs_intermediate_output_bucket.bucket_name,
        )
