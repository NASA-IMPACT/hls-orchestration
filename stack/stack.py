import os
import json
from aws_cdk import (core, aws_stepfunctions, aws_iam, aws_s3, aws_sns,
                     aws_lambda, aws_events, aws_events_targets, aws_ssm)
from hlsconstructs.network import Network
from hlsconstructs.s3 import S3
from hlsconstructs.efs import Efs
from hlsconstructs.rds import Rds
from hlsconstructs.docker_batchjob import DockerBatchJob
from hlsconstructs.batch import Batch
from hlsconstructs.lambdafunc import Lambda
from hlsconstructs.batch_cron import BatchCron
from hlsconstructs.sentinel_step_function import SentinelStepFunction
from hlsconstructs.landsat_step_function import LandsatStepFunction
from hlsconstructs.landsat_incomplete_step_function import LandsatIncompleteStepFunction
from hlsconstructs.sentinel_errors_step_function import SentinelErrorsStepFunction
from hlsconstructs.step_function_trigger import StepFunctionTrigger
from hlsconstructs.stepfunction_alarm import StepFunctionAlarm

# Required env settings
STACKNAME = os.environ["HLS_STACKNAME"]
LAADS_TOKEN = os.environ["HLS_LAADS_TOKEN"]
OUTPUT_BUCKET_ROLE_ARN = os.environ["HLS_OUTPUT_BUCKET_ROLE_ARN"]
OUTPUT_BUCKET = os.environ["HLS_OUTPUT_BUCKET"]
GIBS_OUTPUT_BUCKET = os.environ["HLS_GIBS_OUTPUT_BUCKET"]


def getenv(key, default):
    value = os.getenv(key, default)
    if len(value) == 0 or value is None:
        value = default
    return value


# Optional env settings
# Images
SENTINEL_ECR_URI = getenv(
    "HLS_SENTINEL_ECR_URI",
    "018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-sentinel:latest",
)
LANDSAT_ECR_URI = getenv(
    "HLS_LANDSAT_ECR_URI",
    "018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-landsat-c2:latest",
)
LANDSAT_TILE_ECR_URI = getenv(
    "HLS_LANDSAT_TILE_ECR_URI",
    "018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-landsat-tile:latest",
)
LAADS_ECR_URI = getenv(
    "HLS_LAADS_ECR_URI",
    "018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-laads:latest",
)

# Cron settings
LAADS_CRON = getenv("HLS_LAADS_CRON", "cron(0 0/12 * * ? *)")
LANDSAT_INCOMPLETE_CRON = getenv(
    "HLS_LANDSAT_INCOMPLETE_CRON",
    "cron(0 12 * * ? *)"
)
SENTINEL_ERRORS_CRON = getenv(
    "HLS_SENTINEL_ERRORS_CRON",
    "cron(0 20 * * ? *)"
)
LANDSAT_DAYS_PRIOR = getenv("HLS_LANDSAT_DAYS_PRIOR", "4")
SENTINEL_DAYS_PRIOR = getenv("HLS_SENTINEL_DAYS_PRIOR", "1")

SSH_KEYNAME = getenv("HLS_SSH_KEYNAME", "hls-mount")
LANDSAT_SNS_TOPIC = getenv(
    "HLS_LANDSAT_SNS_TOPIC", "arn:aws:sns:us-west-2:673253540267:public-c2-notify"
)

# Stack named resources
SENTINEL_INPUT_BUCKET = f"{STACKNAME}-sentinel-input-files"
LAADS_BUCKET = f"{STACKNAME}-laads-bucket"
LANDSAT_INTERMEDIATE_OUTPUT_BUCKET = f"{STACKNAME}-landsat-intermediate-output"
GIBS_INTERMEDIATE_OUTPUT_BUCKET = f"{STACKNAME}-gibs-intermediate-output"

try:
    MAXV_CPUS = int(getenv("HLS_MAXV_CPUS", 1200))
except ValueError:
    MAXV_CPUS = 1200

if getenv("HLS_REPLACE_EXISTING", "true") == "true":
    REPLACE_EXISTING = True
else:
    REPLACE_EXISTING = False

if getenv("HLS_USE_CLOUD_WATCH", "true") == "true":
    USE_CLOUD_WATCH = True
else:
    USE_CLOUD_WATCH = False

if getenv("GCC", None) == "true":
    GCC = True
else:
    GCC = False

# Common resurces
LAADS_BUCKET_BOOTSTRAP = "hls-development-laads-bucket"


class HlsStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        if GCC:
            vpcid = os.environ["HLS_GCC_VPCID"]
            image_id = aws_ssm.StringParameter.from_string_parameter_attributes(
                self, "gcc_ami", parameter_name="/gcc/amis/aml2-ecs"
            ).string_value
            from permission_boundary import PermissionBoundaryAspect
            self.node.apply_aspect(
                PermissionBoundaryAspect(
                    f'arn:aws:iam::{core.Aws.ACCOUNT_ID}:policy/gcc-tenantOperatorBoundary'
                )
            )
        else:
            vpcid = None
            image_id = None

        self.network = Network(self, "Network", vpcid=vpcid)

        self.laads_bucket = S3(self, "LaadsBucket", bucket_name=LAADS_BUCKET)

        self.sentinel_output_bucket = aws_s3.Bucket.from_bucket_name(
            self, "sentinel_output_bucket", OUTPUT_BUCKET
        )

        self.landsat_output_bucket = aws_s3.Bucket.from_bucket_name(
            self, "landsat_output_bucket", OUTPUT_BUCKET
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
            use_cw=USE_CLOUD_WATCH,
            image_id=image_id,
        )

        self.laads_task = DockerBatchJob(
            self,
            "LaadsTask",
            dockeruri=LAADS_ECR_URI,
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

        self.hls_lambda_layer = aws_lambda.LayerVersion(
            self,
            "HLSLambdaLayer",
            code=aws_lambda.Code.from_asset(
                os.path.join(
                    os.path.dirname(__file__), "..", "layers",
                    "hls_lambda_layer"
                )
            ),
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_7],
        )

        self.pr2mgrs_lambda = Lambda(
            self,
            "Pr2Mgrs",
            code_dir="pr2mgrs/hls_pr2mgrs",
            handler="handler.handler",
            timeout=120,
        )

        self.laads_available = Lambda(
            self,
            "LaadsAvailable",
            code_file="laads_available.py",
            env={"LAADS_BUCKET": LAADS_BUCKET},
            timeout=120,
        )

        self.check_twin_granule = Lambda(
            self,
            "CheckGranule",
            code_file="twin_granule.py",
            env={"SENTINEL_INPUT_BUCKET": SENTINEL_INPUT_BUCKET},
            timeout=120,
        )

        self.landsat_mgrs_logger = Lambda(
            self,
            "LandsatMGRSLogger",
            code_file="landsat_mgrs_logger.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
            },
            timeout=120,
        )

        self.mgrs_logger = Lambda(
            self,
            "MGRSLogger",
            code_file="mgrs_logger.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
            },
            timeout=120,
            layers=[self.hls_lambda_layer],
        )

        self.landsat_ac_logger = Lambda(
            self,
            "LandsatAcLogger",
            code_file="landsat_ac_logger.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
            },
            timeout=120,
            layers=[self.hls_lambda_layer],
        )

        self.landsat_logger = Lambda(
            self,
            "LandsatLogger",
            code_file="landsat_logger.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
            },
            timeout=120,
        )

        self.landsat_pathrow_status = Lambda(
            self,
            "LandsatPathrowStatus",
            code_file="landsat_pathrow_status.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
            },
            timeout=120,
        )

        self.check_landsat_tiling_exit_code = Lambda(
            self,
            "CheckLandsatTilingExitCode",
            code_file="check_landsat_tiling_exit_code.py",
            timeout=30,
        )

        self.check_exit_code = Lambda(
            self,
            "CheckExitCode",
            code_file="check_exit_code.py",
            timeout=30,
        )

        self.sentinel_logger = Lambda(
            self,
            "SentinelLogger",
            code_file="sentinel_logger.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
            },
            timeout=120,
            layers=[self.hls_lambda_layer],

        )

        self.update_sentinel_failure = Lambda(
            self,
            "UpdateSentinelFailure",
            code_file="update_sentinel_failure.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
            },
            timeout=120,
            layers=[self.hls_lambda_layer],
        )

        self.get_random_wait = Lambda(
            self,
            "GetRandomWait",
            code_file="get_random_wait.py",
            timeout=120,
        )

        self.check_landsat_pathrow_complete = Lambda(
            self,
            "CheckLandsatPathrowComplete",
            code_file="check_landsat_pathrow_complete.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
            },
            timeout=900
        )

        self.put_landsat_task_cw_metric = Lambda(
            self,
            "PutLandsatTaskCWMetric",
            code_file="put_exit_code_cw_metric.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
                "JOB_ID": f"{STACKNAME}_landsat_ac",
                "TABLE_NAME": "landsat_ac_granule_log",
            },
            timeout=900,
        )
        self.put_landsat_tile_task_cw_metric = Lambda(
            self,
            "PutLandsatTileTaskCWMetric",
            code_file="put_exit_code_cw_metric.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
                "JOB_ID": f"{STACKNAME}_landsat_tile",
                "TABLE_NAME": "landsat_mgrs_granule_log",
            },
            timeout=900,
        )
        self.put_sentintel_task_cw_metric = Lambda(
            self,
            "PutSentinelTaskCWMetric",
            code_file="put_exit_code_cw_metric.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
                "JOB_ID": f"{STACKNAME}_sentinel",
                "TABLE_NAME": "sentinel_granule_log",
            },
            timeout=900,
        )
        self.put_metric_policy = aws_iam.PolicyStatement(
            resources=["*"],
            actions=[
                "cloudwatch:PutMetricData",
                "cloudwatch:ListMetrics",
            ],
        )
        self.put_landsat_task_cw_metric.function.add_to_role_policy(
            self.put_metric_policy
        )
        self.put_landsat_tile_task_cw_metric.function.add_to_role_policy(
            self.put_metric_policy
        )
        self.put_sentintel_task_cw_metric.function.add_to_role_policy(
            self.put_metric_policy
        )
        self.put_metric_cron_rule = aws_events.Rule(
            self,
            "Rule",
            schedule=aws_events.Schedule.expression("cron(0/15 * * * ? *)"),
            targets=[
                aws_events_targets.LambdaFunction(
                    self.put_landsat_task_cw_metric.function
                ),
                aws_events_targets.LambdaFunction(
                    self.put_landsat_tile_task_cw_metric.function
                ),
                aws_events_targets.LambdaFunction(
                    self.put_sentintel_task_cw_metric.function
                ),
            ]
        )

        self.laads_cron = BatchCron(
            self,
            "LaadsCron",
            cron_str=LAADS_CRON,
            queue=self.batch.laads_jobqueue.ref,
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
            outputbucket=OUTPUT_BUCKET,
            inputbucket=SENTINEL_INPUT_BUCKET,
            sentinel_job_definition=self.sentinel_task.job.ref,
            jobqueue=self.batch.sentinel_jobqueue.ref,
            lambda_logger=self.lambda_logger.function.function_arn,
            sentinel_logger=self.sentinel_logger.function.function_arn,
            check_exit_code=self.check_exit_code.function.function_arn,
            outputbucket_role_arn=OUTPUT_BUCKET_ROLE_ARN,
            replace_existing=REPLACE_EXISTING,
            gibs_outputbucket=GIBS_OUTPUT_BUCKET,
        )

        self.sentinel_errors_step_function = SentinelErrorsStepFunction(
            self,
            "SentinelErrorsStateMachine",
            outputbucket=OUTPUT_BUCKET,
            inputbucket=SENTINEL_INPUT_BUCKET,
            sentinel_job_definition=self.sentinel_task.job.ref,
            jobqueue=self.batch.sentinel_jobqueue.ref,
            lambda_logger=self.lambda_logger.function.function_arn,
            update_sentinel_failure=self.update_sentinel_failure.function.function_arn,
            outputbucket_role_arn=OUTPUT_BUCKET_ROLE_ARN,
            gibs_intermediate_output_bucket=GIBS_INTERMEDIATE_OUTPUT_BUCKET,
            gibs_outputbucket=GIBS_OUTPUT_BUCKET,
            get_random_wait=self.get_random_wait.function.function_arn,
        )

        self.landsat_step_function = LandsatStepFunction(
            self,
            "LandsatStateMachine",
            laads_available_function=self.laads_available.function.function_arn,
            outputbucket=OUTPUT_BUCKET,
            outputbucket_role_arn=OUTPUT_BUCKET_ROLE_ARN,
            intermediate_output_bucket=LANDSAT_INTERMEDIATE_OUTPUT_BUCKET,
            ac_job_definition=self.landsat_task.job.ref,
            tile_job_definition=self.landsat_tile_task.job.ref,
            acjobqueue=self.batch.landsatac_jobqueue.ref,
            tilejobqueue=self.batch.landsattile_jobqueue.ref,
            lambda_logger=self.lambda_logger.function.function_arn,
            landsat_mgrs_logger=self.landsat_mgrs_logger.function.function_arn,
            landsat_ac_logger=self.landsat_ac_logger.function.function_arn,
            landsat_logger=self.landsat_logger.function.function_arn,
            landsat_pathrow_status=self.landsat_pathrow_status.function.function_arn,
            pr2mgrs=self.pr2mgrs_lambda.function.function_arn,
            mgrs_logger=self.mgrs_logger.function.function_arn,
            check_landsat_tiling_exit_code=self.check_landsat_tiling_exit_code.function.function_arn,
            check_landsat_ac_exit_code=self.check_exit_code.function.function_arn,
            get_random_wait=self.get_random_wait.function.function_arn,
            gibs_outputbucket=GIBS_OUTPUT_BUCKET,
            replace_existing=REPLACE_EXISTING,
        )

        self.landsat_incomplete_step_function = LandsatIncompleteStepFunction(
            self,
            "LandsatIncompleteStateMachine",
            outputbucket=OUTPUT_BUCKET,
            outputbucket_role_arn=OUTPUT_BUCKET_ROLE_ARN,
            tilejobqueue=self.batch.landsattile_jobqueue.ref,
            tile_job_definition=self.landsat_tile_task.job.ref,
            intermediate_output_bucket=LANDSAT_INTERMEDIATE_OUTPUT_BUCKET,
            lambda_logger=self.lambda_logger.function.function_arn,
            check_mgrs_pathrow_complete=self.check_landsat_pathrow_complete.function.function_arn,
            pr2mgrs=self.pr2mgrs_lambda.function.function_arn,
            mgrs_logger=self.mgrs_logger.function.function_arn,
            gibs_outputbucket=GIBS_OUTPUT_BUCKET,
            get_random_wait=self.get_random_wait.function.function_arn,
        )

        self.step_function_trigger = StepFunctionTrigger(
            self,
            "SentinelStepFunctionTrigger",
            state_machine=self.sentinel_step_function.sentinel_state_machine.ref,
            code_file="execute_step_function.py",
            timeout=180,
            input_bucket=self.sentinel_input_bucket,
        )

        self.landsat_sns_topic = aws_sns.Topic.from_topic_arn(
            self, "LandsatSNSTopc", topic_arn=LANDSAT_SNS_TOPIC
        )

        self.landsat_step_function_trigger = StepFunctionTrigger(
            self,
            "LandsatStepFunctionTrigger",
            state_machine=self.landsat_step_function.state_machine.ref,
            code_file="execute_landsat_step_function.py",
            timeout=180,
            input_sns=self.landsat_sns_topic,
            layers=[self.hls_lambda_layer],
        )

        self.landsat_incomplete_step_function_trigger = StepFunctionTrigger(
            self,
            "LandsatIncompleteStepFunctionTrigger",
            state_machine=self.landsat_incomplete_step_function.state_machine.ref,
            code_file="process_landsat_mgrs_incompletes.py",
            timeout=900,
            lambda_name="ProcessLandsatMgrsIncompletes",
            layers=[self.hls_lambda_layer],
            cron_str=LANDSAT_INCOMPLETE_CRON,
            env_vars={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
                "DAYS_PRIOR": LANDSAT_DAYS_PRIOR,
            },
        )

        self.sentinel_errors_step_function_trigger = StepFunctionTrigger(
            self,
            "SentinelErrorsStepFunctionTrigger",
            state_machine=self.sentinel_errors_step_function.state_machine.ref,
            code_file="process_sentinel_errors_by_date.py",
            timeout=900,
            lambda_name="ProcessSentinelErrors",
            cron_str=SENTINEL_ERRORS_CRON,
            env_vars={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
                "DAYS_PRIOR": SENTINEL_DAYS_PRIOR,
            },
        )

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

        # Cross construct permissions
        self.laads_bucket_read_policy = aws_iam.PolicyStatement(
            resources=[
                self.laads_bucket.bucket_arn,
                f"{self.laads_bucket.bucket_arn}/*",
            ],
            actions=["s3:Get*", "s3:List*",],
        )
        self.batch_jobqueue_policy = aws_iam.PolicyStatement(
            resources=[
                self.batch.sentinel_jobqueue.ref,
                self.batch.laads_jobqueue.ref,
                self.batch.landsatac_jobqueue.ref,
                self.batch.landsattile_jobqueue.ref,
            ],
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
        sentinel_lambdas = [
            self.check_twin_granule,
            self.laads_available,
            self.lambda_logger,
            self.sentinel_logger,
            self.check_exit_code,
        ]
        self.addLambdaInvokePolicies(
            self.sentinel_step_function,
            sentinel_lambdas,
        )

        sentinel_errors_lambdas = [
            self.update_sentinel_failure,
            self.get_random_wait
        ]
        self.addLambdaInvokePolicies(
            self.sentinel_errors_step_function,
            sentinel_errors_lambdas,
        )

        self.landsat_step_function.steps_role.add_to_policy(self.batch_jobqueue_policy)
        landsat_lambdas = [
            self.laads_available,
            self.lambda_logger,
            self.landsat_mgrs_logger,
            self.pr2mgrs_lambda,
            self.landsat_ac_logger,
            self.landsat_pathrow_status,
            self.mgrs_logger,
            self.check_landsat_tiling_exit_code,
            self.check_exit_code,
            self.get_random_wait,
            self.landsat_logger,
        ]
        self.addLambdaInvokePolicies(
            self.landsat_step_function,
            landsat_lambdas
        )

        landsat_incomplete_lambdas = [
            self.check_landsat_pathrow_complete,
            self.pr2mgrs_lambda,
            self.lambda_logger,
            self.mgrs_logger,
            self.get_random_wait,
        ]
        self.addLambdaInvokePolicies(
            self.landsat_incomplete_step_function,
            landsat_incomplete_lambdas
        )

        self.addRDSpolicy()

        # Bucket policies
        self.sentinel_input_bucket_policy = aws_iam.PolicyStatement(
            resources=[
                self.sentinel_input_bucket.bucket_arn,
                f"{self.sentinel_input_bucket.bucket_arn}/*",
            ],
            actions=["s3:Get*", "s3:List*",],
        )
        self.check_twin_granule.function.add_to_role_policy(
            self.sentinel_input_bucket_policy
        )
        self.sentinel_task.role.add_to_policy(
            self.sentinel_input_bucket_policy
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
                resources=["arn:aws:s3:::usgs-landsat", "arn:aws:s3:::usgs-landsat/*",],
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
                resources=[OUTPUT_BUCKET_ROLE_ARN],
                actions=["sts:AssumeRole"],
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
            "sentineljobqueueexport",
            export_name=f"{STACKNAME}-sentineljobqueue",
            value=self.batch.sentinel_jobqueue.ref,
        )
        core.CfnOutput(
            self,
            "landsatacjobqueueexport",
            export_name=f"{STACKNAME}-landsatacjobqueue",
            value=self.batch.landsatac_jobqueue.ref,
        )
        core.CfnOutput(
            self,
            "landsattilejobqueueexport",
            export_name=f"{STACKNAME}-landsattilejobqueue",
            value=self.batch.landsattile_jobqueue.ref,
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

    def addLambdaInvokePolicies(self, stepfunction, lambdas):
        for lambda_function in lambdas:
            stepfunction.steps_role.add_to_policy(
                lambda_function.invoke_policy_statement
            )

    def addRDSpolicy(self):
        lambdas = [
            self.lambda_logger,
            self.rds_bootstrap,
            self.landsat_mgrs_logger,
            self.landsat_ac_logger,
            self.mgrs_logger,
            self.landsat_pathrow_status,
            self.sentinel_logger,
            self.update_sentinel_failure,
            self.check_landsat_pathrow_complete,
            self.landsat_incomplete_step_function_trigger.execute_step_function,
            self.sentinel_errors_step_function_trigger.execute_step_function,
            self.landsat_logger,
            self.put_landsat_task_cw_metric,
            self.put_landsat_tile_task_cw_metric,
            self.put_sentintel_task_cw_metric,
        ]
        for lambda_function in lambdas:
            lambda_function.function.add_to_role_policy(
                self.rds.policy_statement
            )
