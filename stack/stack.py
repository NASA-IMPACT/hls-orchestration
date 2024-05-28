import os

from aws_cdk import aws_iam, aws_lambda, aws_s3, aws_sns, aws_ssm, core
from hlsconstructs.batch import Batch
from hlsconstructs.batch_cron import BatchCron
from hlsconstructs.docker_batchjob import DockerBatchJob
from hlsconstructs.efs import Efs
from hlsconstructs.lambdafunc import Lambda
from hlsconstructs.landsat_ac_errors_step_function import LandsatACErrorsStepFunction
from hlsconstructs.landsat_incomplete_step_function import LandsatIncompleteStepFunction
from hlsconstructs.landsat_mgrs_partials_step_function import (
    LandsatMGRSPartialsStepFunction,
)
from hlsconstructs.landsat_mgrs_step_function import LandsatMGRSStepFunction
from hlsconstructs.landsat_step_function import LandsatStepFunction
from hlsconstructs.network import Network
from hlsconstructs.rds import Rds
from hlsconstructs.s3 import S3
from hlsconstructs.sentinel_errors_step_function import SentinelErrorsStepFunction
from hlsconstructs.sentinel_step_function import SentinelStepFunction
from hlsconstructs.step_function_trigger import StepFunctionTrigger
from hlsconstructs.stepfunction_alarm import StepFunctionAlarm

# Required env settings
STACKNAME = os.environ["HLS_STACKNAME"]
LAADS_TOKEN = os.environ["HLS_LAADS_TOKEN"]
OUTPUT_BUCKET_ROLE_ARN = os.environ["HLS_OUTPUT_BUCKET_ROLE_ARN"]
OUTPUT_BUCKET = os.environ["HLS_OUTPUT_BUCKET"]
OUTPUT_BUCKET_HISTORIC = os.environ["HLS_OUTPUT_BUCKET_HISTORIC"]
GIBS_OUTPUT_BUCKET = os.environ["HLS_GIBS_OUTPUT_BUCKET"]
GIBS_OUTPUT_BUCKET_HISTORIC = os.environ["HLS_GIBS_OUTPUT_BUCKET_HISTORIC"]
LANDSAT_HISTORIC_SNS_TOPIC = os.environ["HLS_LANDASAT_HISTORIC_SNS_TOPIC"]


def getenv(key, default):
    value = os.getenv(key, default)
    return default if value == "" else value


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
RDS_MIN_CAPACITY = int(getenv("HLS_RDS_MIN_CAPACITY", 4))
RDS_MAX_CAPACITY = int(getenv("HLS_RDS_MAX_CAPACITY", 8))
DEBUG_BUCKET = getenv("HLS_DEBUG_BUCKET", False)


# Cron settings
LAADS_CRON = getenv("HLS_LAADS_CRON", "cron(0 0/12 * * ? *)")
LANDSAT_INCOMPLETE_CRON = getenv("HLS_LANDSAT_INCOMPLETE_CRON", "cron(0 12 * * ? *)")
LANDSAT_HISTORIC_INCOMPLETE_CRON = getenv(
    "HLS_LANDSAT_HISTORIC_INCOMPLETE_CRON", "cron(0 0/6 * * ? *)"
)
SENTINEL_ERRORS_CRON = getenv("HLS_SENTINEL_ERRORS_CRON", "cron(0 0/4 * * ? *)")
LANDSAT_AC_ERRORS_CRON = getenv("HLS_LANDSAT_AC_ERRORS_CRON", "cron(0 16 * * ? *)")
LANDSAT_HISTORIC_AC_ERRORS_CRON = getenv(
    "HLS_LANDSAT_HISTORIC_AC_ERRORS_CRON", "cron(0 0/4 * * ? *)"
)
LANDSAT_DAYS_PRIOR = getenv("HLS_LANDSAT_DAYS_PRIOR", "4")
LANDSAT_HISTORIC_HOURS_PRIOR = getenv("HLS_LANDSAT_HISTORIC_HOURS_PRIOR", "4")
SENTINEL_RETRY_LIMIT = getenv("HLS_SENTINEL_RETRY_LIMIT", "3")
LANDSAT_RETRY_LIMIT = getenv("HLS_LANDSAT_RETRY_LIMIT", "3")
SSH_KEYNAME = getenv("HLS_SSH_KEYNAME", "hls-mount")
LANDSAT_SNS_TOPIC = getenv(
    "HLS_LANDSAT_SNS_TOPIC", "arn:aws:sns:us-west-2:673253540267:public-c2-notify-v2"
)
LANDSAT_SNS_TOPIC_ENABLED = (
    getenv("HLS_LANDSAT_SNS_TOPIC_ENABLED", "true").lower() == "true"
)

DOWNLOADER_FUNCTION_ARN = getenv("HLS_DOWNLOADER_FUNCTION_ARN", None)
LAADS_BUCKET_BOOTSTRAP = getenv(
    "HLS_LAADS_BUCKET_BOOTSTRAP", "hls-development-laads-bucket"
)

# Stack named resources
SENTINEL_INPUT_BUCKET = f"{STACKNAME}-sentinel-input-files"
SENTINEL_INPUT_BUCKET_HISTORIC = f"{STACKNAME}-sentinel-input-files-historic"
LAADS_BUCKET = f"{STACKNAME}-laads-bucket"
LANDSAT_INTERMEDIATE_OUTPUT_BUCKET = f"{STACKNAME}-landsat-intermediate-output"
GIBS_INTERMEDIATE_OUTPUT_BUCKET = f"{STACKNAME}-gibs-intermediate-output"
LANDSAT_INPUT_BUCKET_HISTORIC = f"{STACKNAME}-landsat-input-historic"


try:
    MAXV_CPUS = int(getenv("HLS_MAXV_CPUS", 1200))
except ValueError:
    MAXV_CPUS = 1200

REPLACE_EXISTING = getenv("HLS_REPLACE_EXISTING", "true") == "true"
USE_CLOUD_WATCH = getenv("HLS_USE_CLOUD_WATCH", "false") == "true"
GCC = getenv("GCC", None) == "true"


class HlsStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        if GCC:
            from permission_boundary import PermissionBoundaryAspect

            vpcid = os.environ["HLS_GCC_VPCID"]
            boundary_arn = os.environ["HLS_GCC_BOUNDARY_ARN"]
            image_id = aws_ssm.StringParameter.from_string_parameter_attributes(
                self, "gcc_ami", parameter_name="/mcp/amis/aml2-ecs"
            ).string_value

            core.Aspects.of(self).add(PermissionBoundaryAspect(boundary_arn))
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
            self,
            "SentinelInputBucket",
            bucket_name=SENTINEL_INPUT_BUCKET,
            removal_policy=core.RemovalPolicy.DESTROY,
        )

        self.sentinel_input_bucket_historic = aws_s3.Bucket(
            self,
            "SentinelInputBucketHistoric",
            bucket_name=SENTINEL_INPUT_BUCKET_HISTORIC,
            removal_policy=core.RemovalPolicy.DESTROY,
        )

        self.landsat_input_bucket_historic = aws_s3.Bucket(
            self,
            "LandsatInputBucketHistoric",
            bucket_name=LANDSAT_INPUT_BUCKET_HISTORIC,
            removal_policy=core.RemovalPolicy.DESTROY,
        )

        self.landsat_intermediate_output_bucket = aws_s3.Bucket(
            self,
            "LandsatIntermediateBucket",
            bucket_name=LANDSAT_INTERMEDIATE_OUTPUT_BUCKET,
            removal_policy=core.RemovalPolicy.DESTROY,
            lifecycle_rules=[aws_s3.LifecycleRule(expiration=core.Duration.days(60))],
        )

        self.gibs_intermediate_output_bucket = aws_s3.Bucket(
            self,
            "GibsIntermediateBucket",
            bucket_name=GIBS_INTERMEDIATE_OUTPUT_BUCKET,
            removal_policy=core.RemovalPolicy.DESTROY,
            lifecycle_rules=[aws_s3.LifecycleRule(expiration=core.Duration.days(60))],
        )

        self.efs = Efs(self, "Efs", network=self.network)

        self.rds = Rds(
            self,
            "Rds",
            network=self.network,
            min_capacity=RDS_MIN_CAPACITY,
            max_capacity=RDS_MAX_CAPACITY,
        )

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

        self.batch = Batch(
            self,
            "Batch",
            network=self.network,
            efs=self.efs.filesystem,
            maxv_cpus=MAXV_CPUS,
            instance_types=["r5d"],
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
            memory=20000,
            vcpus=2,
        )

        self.landsat_task = DockerBatchJob(
            self,
            "LandsatTask",
            dockeruri=LANDSAT_ECR_URI,
            mountpath="/var/lasrc_aux",
            timeout=5400,
            memory=20000,
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
                    os.path.dirname(__file__), "..", "layers", "hls_lambda_layer"
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

        self.check_twin_granule_historic = Lambda(
            self,
            "CheckGranuleHistoric",
            code_file="twin_granule.py",
            env={"SENTINEL_INPUT_BUCKET": SENTINEL_INPUT_BUCKET_HISTORIC},
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

        self.landsat_mgrs_logger_historic = Lambda(
            self,
            "LandsatMGRSLoggerHistoric",
            code_file="landsat_mgrs_logger.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
                "HISTORIC": "historic",
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

        self.landsat_logger_historic = Lambda(
            self,
            "LandsatLoggerHistoric",
            code_file="landsat_logger.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
                "HISTORIC": "historic",
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
        )

        self.sentinel_logger_historic = Lambda(
            self,
            "SentinelLoggerHistoric",
            code_file="sentinel_logger.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
                "HISTORIC": "historic",
            },
            timeout=120,
        )

        self.sentinel_ac_logger = Lambda(
            self,
            "SentinelACLogger",
            code_file="sentinel_ac_logger.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
            },
            timeout=800,
            layers=[self.hls_lambda_layer],
        )

        self.update_sentinel_failure = Lambda(
            self,
            "UpdateSentinelFailure",
            code_file="sentinel_ac_logger.py",
            env={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
            },
            timeout=800,
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
            timeout=900,
        )

        #  self.put_landsat_task_cw_metric = Lambda(
        #  self,
        #  "PutLandsatTaskCWMetric",
        #  code_file="put_exit_code_cw_metric.py",
        #  env={
        #  "HLS_SECRETS": self.rds.secret.secret_arn,
        #  "HLS_DB_NAME": self.rds.database.database_name,
        #  "HLS_DB_ARN": self.rds.arn,
        #  "JOB_ID": f"{STACKNAME}_landsat_ac",
        #  "TABLE_NAME": "landsat_ac_granule_log",
        #  },
        #  timeout=900,
        #  )
        #  self.put_landsat_tile_task_cw_metric = Lambda(
        #  self,
        #  "PutLandsatTileTaskCWMetric",
        #  code_file="put_exit_code_cw_metric.py",
        #  env={
        #  "HLS_SECRETS": self.rds.secret.secret_arn,
        #  "HLS_DB_NAME": self.rds.database.database_name,
        #  "HLS_DB_ARN": self.rds.arn,
        #  "JOB_ID": f"{STACKNAME}_landsat_tile",
        #  "TABLE_NAME": "landsat_mgrs_granule_log",
        #  },
        #  timeout=900,
        #  )
        #  self.put_sentintel_task_cw_metric = Lambda(
        #  self,
        #  "PutSentinelTaskCWMetric",
        #  code_file="put_exit_code_cw_metric.py",
        #  env={
        #  "HLS_SECRETS": self.rds.secret.secret_arn,
        #  "HLS_DB_NAME": self.rds.database.database_name,
        #  "HLS_DB_ARN": self.rds.arn,
        #  "JOB_ID": f"{STACKNAME}_sentinel",
        #  "TABLE_NAME": "sentinel_granule_log",
        #  },
        #  timeout=900,
        #  )
        #  self.put_metric_policy = aws_iam.PolicyStatement(
        #  resources=["*"],
        #  actions=[
        #  "cloudwatch:PutMetricData",
        #  "cloudwatch:ListMetrics",
        #  ],
        #  )
        #  self.put_landsat_task_cw_metric.function.add_to_role_policy(
        #  self.put_metric_policy
        #  )
        #  self.put_landsat_tile_task_cw_metric.function.add_to_role_policy(
        #  self.put_metric_policy
        #  )
        #  self.put_sentintel_task_cw_metric.function.add_to_role_policy(
        #  self.put_metric_policy
        #  )
        #  self.put_metric_cron_rule = aws_events.Rule(
        #  self,
        #  "Rule",
        #  schedule=aws_events.Schedule.expression("cron(0/15 * * * ? *)"),
        #  targets=[
        #  aws_events_targets.LambdaFunction(
        #  self.put_landsat_task_cw_metric.function
        #  ),
        #  aws_events_targets.LambdaFunction(
        #  self.put_landsat_tile_task_cw_metric.function
        #  ),
        #  aws_events_targets.LambdaFunction(
        #  self.put_sentintel_task_cw_metric.function
        #  ),
        #  ],
        #  )

        self.laads_cron = BatchCron(
            self,
            "LaadsCron",
            cron_str=LAADS_CRON,
            queue=self.batch.laads_jobqueue.ref,
            job=self.laads_task,
            env={
                "LAADS_BUCKET": LAADS_BUCKET,
                "LASRC_AUX_DIR": "/var/lasrc_aux",
                "LAADS_TOKEN": LAADS_TOKEN,
                "LAADS_FLAG": "--today",
            },
        )

        self.laads_climatology_cron = BatchCron(
            self,
            "LaadsClimatologyCron",
            cron_str="cron(0 0 1-6 * ? *)",
            code_file="laads_submit_climatology_job.py",
            queue=self.batch.laads_jobqueue.ref,
            job=self.laads_task,
            env={
                "LAADS_BUCKET": LAADS_BUCKET,
                "LASRC_AUX_DIR": "/var/lasrc_aux",
                "LAADS_TOKEN": LAADS_TOKEN,
                "JOB_QUEUE": self.batch.laads_jobqueue.ref,
                "JOB_DEFINITION": self.laads_task.job.ref,
            },
        )

        self.sentinel_step_function = SentinelStepFunction(
            self,
            "SentinelStateMachine",
            check_twin_granule=self.check_twin_granule,
            laads_available=self.laads_available,
            outputbucket=OUTPUT_BUCKET,
            inputbucket=SENTINEL_INPUT_BUCKET,
            sentinel_job_definition=self.sentinel_task.job.ref,
            jobqueue=self.batch.sentinel_jobqueue.ref,
            sentinel_ac_logger=self.sentinel_ac_logger,
            sentinel_logger=self.sentinel_logger,
            check_exit_code=self.check_exit_code,
            outputbucket_role_arn=OUTPUT_BUCKET_ROLE_ARN,
            replace_existing=REPLACE_EXISTING,
            gibs_outputbucket=GIBS_OUTPUT_BUCKET,
            debug_bucket=DEBUG_BUCKET,
        )

        self.sentinel_step_function_historic = SentinelStepFunction(
            self,
            "SentinelHistoricStateMachine",
            check_twin_granule=self.check_twin_granule_historic,
            laads_available=self.laads_available,
            outputbucket=OUTPUT_BUCKET_HISTORIC,
            inputbucket=SENTINEL_INPUT_BUCKET_HISTORIC,
            sentinel_job_definition=self.sentinel_task.job.ref,
            jobqueue=self.batch.sentinel_historic_jobqueue.ref,
            sentinel_ac_logger=self.sentinel_ac_logger,
            sentinel_logger=self.sentinel_logger_historic,
            check_exit_code=self.check_exit_code,
            outputbucket_role_arn=OUTPUT_BUCKET_ROLE_ARN,
            replace_existing=REPLACE_EXISTING,
            gibs_outputbucket=GIBS_OUTPUT_BUCKET_HISTORIC,
        )

        self.sentinel_errors_step_function = SentinelErrorsStepFunction(
            self,
            "SentinelErrorsStateMachine",
            outputbucket=OUTPUT_BUCKET,
            inputbucket=SENTINEL_INPUT_BUCKET,
            sentinel_job_definition=self.sentinel_task.job.ref,
            jobqueue=self.batch.sentinel_jobqueue.ref,
            update_sentinel_failure=self.update_sentinel_failure,
            outputbucket_role_arn=OUTPUT_BUCKET_ROLE_ARN,
            gibs_outputbucket=GIBS_OUTPUT_BUCKET,
            get_random_wait=self.get_random_wait,
            debug_bucket=DEBUG_BUCKET,
        )

        self.sentinel_errors_step_function_historic = SentinelErrorsStepFunction(
            self,
            "SentinelHistoricErrorsStateMachine",
            outputbucket=OUTPUT_BUCKET_HISTORIC,
            inputbucket=SENTINEL_INPUT_BUCKET_HISTORIC,
            sentinel_job_definition=self.sentinel_task.job.ref,
            jobqueue=self.batch.sentinel_historic_jobqueue.ref,
            update_sentinel_failure=self.update_sentinel_failure,
            outputbucket_role_arn=OUTPUT_BUCKET_ROLE_ARN,
            gibs_outputbucket=GIBS_OUTPUT_BUCKET_HISTORIC,
            get_random_wait=self.get_random_wait,
        )

        self.landsat_mgrs_step_function = LandsatMGRSStepFunction(
            self,
            "LandsatMGRSStateMachine",
            outputbucket=OUTPUT_BUCKET,
            outputbucket_role_arn=OUTPUT_BUCKET_ROLE_ARN,
            intermediate_output_bucket=LANDSAT_INTERMEDIATE_OUTPUT_BUCKET,
            tile_job_definition=self.landsat_tile_task.job.ref,
            tilejobqueue=self.batch.landsattile_jobqueue.ref,
            landsat_pathrow_status=self.landsat_pathrow_status,
            pr2mgrs=self.pr2mgrs_lambda,
            mgrs_logger=self.mgrs_logger,
            get_random_wait=self.get_random_wait,
            gibs_outputbucket=GIBS_OUTPUT_BUCKET,
            debug_bucket=DEBUG_BUCKET,
        )

        self.landsat_mgrs_partials_step_function = LandsatMGRSPartialsStepFunction(
            self,
            "LandsatMGRSPartialsStateMachine",
            outputbucket=OUTPUT_BUCKET,
            outputbucket_role_arn=OUTPUT_BUCKET_ROLE_ARN,
            intermediate_output_bucket=LANDSAT_INTERMEDIATE_OUTPUT_BUCKET,
            tile_job_definition=self.landsat_tile_task.job.ref,
            tilejobqueue=self.batch.landsattile_jobqueue.ref,
            check_landsat_pathrow_complete=self.check_landsat_pathrow_complete,
            pr2mgrs=self.pr2mgrs_lambda,
            mgrs_logger=self.mgrs_logger,
            get_random_wait=self.get_random_wait,
            gibs_outputbucket=GIBS_OUTPUT_BUCKET,
        )

        self.landsat_mgrs_step_function_historic = LandsatMGRSStepFunction(
            self,
            "LandsatMGRSStateMachineHistoric",
            outputbucket=OUTPUT_BUCKET_HISTORIC,
            outputbucket_role_arn=OUTPUT_BUCKET_ROLE_ARN,
            intermediate_output_bucket=LANDSAT_INTERMEDIATE_OUTPUT_BUCKET,
            tile_job_definition=self.landsat_tile_task.job.ref,
            tilejobqueue=self.batch.landsattile_historic_jobqueue.ref,
            landsat_pathrow_status=self.landsat_pathrow_status,
            pr2mgrs=self.pr2mgrs_lambda,
            mgrs_logger=self.mgrs_logger,
            get_random_wait=self.get_random_wait,
            gibs_outputbucket=GIBS_OUTPUT_BUCKET,
        )

        self.landsat_mgrs_partials_step_function_historic = (
            LandsatMGRSPartialsStepFunction(
                self,
                "LandsatMGRSPartialsStateMachineHistoric",
                outputbucket=OUTPUT_BUCKET_HISTORIC,
                outputbucket_role_arn=OUTPUT_BUCKET_ROLE_ARN,
                intermediate_output_bucket=LANDSAT_INTERMEDIATE_OUTPUT_BUCKET,
                tile_job_definition=self.landsat_tile_task.job.ref,
                tilejobqueue=self.batch.landsattile_historic_jobqueue.ref,
                check_landsat_pathrow_complete=self.check_landsat_pathrow_complete,
                pr2mgrs=self.pr2mgrs_lambda,
                mgrs_logger=self.mgrs_logger,
                get_random_wait=self.get_random_wait,
                gibs_outputbucket=GIBS_OUTPUT_BUCKET,
            )
        )

        self.landsat_step_function = LandsatStepFunction(
            self,
            "LandsatStateMachine",
            laads_available=self.laads_available,
            intermediate_output_bucket=LANDSAT_INTERMEDIATE_OUTPUT_BUCKET,
            ac_job_definition=self.landsat_task.job.ref,
            acjobqueue=self.batch.landsatac_jobqueue.ref,
            landsat_mgrs_logger=self.landsat_mgrs_logger,
            landsat_ac_logger=self.landsat_ac_logger,
            landsat_logger=self.landsat_logger,
            pr2mgrs=self.pr2mgrs_lambda,
            check_landsat_tiling_exit_code=self.check_landsat_tiling_exit_code,
            check_landsat_ac_exit_code=self.check_exit_code,
            get_random_wait=self.get_random_wait,
            replace_existing=REPLACE_EXISTING,
            landsat_mgrs_step_function_arn=self.landsat_mgrs_step_function.state_machine.ref,
            debug_bucket=DEBUG_BUCKET,
        )

        self.landsat_step_function_historic = LandsatStepFunction(
            self,
            "LandsatStateMachineHistoric",
            laads_available=self.laads_available,
            intermediate_output_bucket=LANDSAT_INTERMEDIATE_OUTPUT_BUCKET,
            ac_job_definition=self.landsat_task.job.ref,
            acjobqueue=self.batch.landsatac_historic_jobqueue.ref,
            landsat_mgrs_logger=self.landsat_mgrs_logger_historic,
            landsat_ac_logger=self.landsat_ac_logger,
            landsat_logger=self.landsat_logger_historic,
            pr2mgrs=self.pr2mgrs_lambda,
            check_landsat_tiling_exit_code=self.check_landsat_tiling_exit_code,
            check_landsat_ac_exit_code=self.check_exit_code,
            get_random_wait=self.get_random_wait,
            replace_existing=REPLACE_EXISTING,
            landsat_mgrs_step_function_arn=self.landsat_mgrs_step_function_historic.state_machine.ref,
        )

        self.landsat_incomplete_step_function = LandsatIncompleteStepFunction(
            self,
            "LandsatIncompleteStateMachine",
            landsat_mgrs_step_function_arn=self.landsat_mgrs_partials_step_function.state_machine.ref,
            get_random_wait=self.get_random_wait,
        )

        self.landsat_historic_incomplete_step_function = LandsatIncompleteStepFunction(
            self,
            "LandsatHistoricIncompleteStateMachine",
            landsat_mgrs_step_function_arn=self.landsat_mgrs_partials_step_function_historic.state_machine.ref,
            get_random_wait=self.get_random_wait,
        )

        self.landsat_ac_errors_step_function = LandsatACErrorsStepFunction(
            self,
            "LandsatACErrorsStateMachine",
            landsat_step_function_arn=self.landsat_step_function.state_machine.ref,
        )

        self.landsat_historic_ac_errors_step_function = LandsatACErrorsStepFunction(
            self,
            "LandsatHistoricACErrorsStateMachine",
            landsat_step_function_arn=self.landsat_step_function_historic.state_machine.ref,
        )

        self.step_function_trigger = StepFunctionTrigger(
            self,
            "SentinelStepFunctionTrigger",
            state_machine=self.sentinel_step_function.sentinel_state_machine.ref,
            code_file="execute_step_function.py",
            timeout=180,
            input_bucket=self.sentinel_input_bucket,
        )

        self.step_function_trigger_historic = StepFunctionTrigger(
            self,
            "SentinelStepFunctionTriggerHistoric",
            state_machine=self.sentinel_step_function_historic.sentinel_state_machine.ref,
            code_file="execute_step_function.py",
            timeout=180,
            input_bucket=self.sentinel_input_bucket_historic,
        )

        if LANDSAT_SNS_TOPIC_ENABLED:
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

        # self.landsat_historic_sns_topic = aws_sns.Topic.from_topic_arn(
        #     self, "LandsatHistoricSNSTopic", topic_arn=LANDSAT_HISTORIC_SNS_TOPIC
        # )

        # self.landsat_step_function_historic_trigger = StepFunctionTrigger(
        #     self,
        #     "LandsatStepFunctionHistoricTrigger",
        #     state_machine=self.landsat_step_function_historic.state_machine.ref,
        #     code_file="execute_landsat_step_function.py",
        #     timeout=180,
        #     input_sns=self.landsat_historic_sns_topic,
        #     layers=[self.hls_lambda_layer],
        #     env_vars={
        #         "HISTORIC": "historic",
        #     },
        # )

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
                "RETRY_LIMIT": LANDSAT_RETRY_LIMIT,
            },
        )

        self.landsat_historic_incomplete_step_function_trigger = StepFunctionTrigger(
            self,
            "LandsatHistoricIncompleteStepFunctionTrigger",
            state_machine=self.landsat_historic_incomplete_step_function.state_machine.ref,
            code_file="process_landsat_mgrs_incompletes.py",
            timeout=900,
            lambda_name="ProcessLandsatMgrsIncompletes",
            layers=[self.hls_lambda_layer],
            cron_str=LANDSAT_HISTORIC_INCOMPLETE_CRON,
            env_vars={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
                "HOURS_PRIOR": LANDSAT_HISTORIC_HOURS_PRIOR,
                "RETRY_LIMIT": LANDSAT_RETRY_LIMIT,
                "HISTORIC": "historic",
            },
        )

        self.landsat_ac_errors_step_function_trigger = StepFunctionTrigger(
            self,
            "LandsatACErrorsStepFunctionTrigger",
            state_machine=self.landsat_ac_errors_step_function.state_machine.ref,
            code_file="process_landsat_ac_errors.py",
            timeout=900,
            lambda_name="ProcessLandsatACErrors",
            layers=[self.hls_lambda_layer],
            cron_str=LANDSAT_AC_ERRORS_CRON,
            env_vars={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
                "RETRY_LIMIT": LANDSAT_RETRY_LIMIT,
            },
        )

        self.landsat_historic_ac_errors_step_function_trigger = StepFunctionTrigger(
            self,
            "LandsatHistoricACErrorsStepFunctionTrigger",
            state_machine=self.landsat_historic_ac_errors_step_function.state_machine.ref,
            code_file="process_landsat_ac_errors.py",
            timeout=900,
            lambda_name="ProcessLandsatACErrors",
            layers=[self.hls_lambda_layer],
            cron_str=LANDSAT_HISTORIC_AC_ERRORS_CRON,
            env_vars={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
                "RETRY_LIMIT": LANDSAT_RETRY_LIMIT,
                "HISTORIC": "historic",
            },
        )

        self.sentinel_errors_step_function_trigger = StepFunctionTrigger(
            self,
            "SentinelErrorsStepFunctionTrigger",
            state_machine=self.sentinel_errors_step_function.state_machine.ref,
            code_file="process_sentinel_errors.py",
            timeout=900,
            lambda_name="ProcessSentinelErrors",
            cron_str=SENTINEL_ERRORS_CRON,
            env_vars={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
                "RETRY_LIMIT": SENTINEL_RETRY_LIMIT,
                "HISTORIC": "no",
            },
        )

        self.sentinel_historic_errors_step_function_trigger = StepFunctionTrigger(
            self,
            "SentinelHistoricErrorsStepFunctionTrigger",
            state_machine=self.sentinel_errors_step_function_historic.state_machine.ref,
            code_file="process_sentinel_errors.py",
            timeout=900,
            lambda_name="ProcessSentinelHistoricErrors",
            cron_str=SENTINEL_ERRORS_CRON,
            env_vars={
                "HLS_SECRETS": self.rds.secret.secret_arn,
                "HLS_DB_NAME": self.rds.database.database_name,
                "HLS_DB_ARN": self.rds.arn,
                "RETRY_LIMIT": SENTINEL_RETRY_LIMIT,
                "HISTORIC": "historic",
            },
        )

        # Alarms
        self.sentinel_step_function_alarm = StepFunctionAlarm(
            self,
            "SentinelStepFunctionAlarm",
            state_machine=self.sentinel_step_function.sentinel_state_machine.ref,
            root_name="Sentinel",
        )

        self.sentinel_step_function_historic_alarm = StepFunctionAlarm(
            self,
            "SentinelStepFunctioniHistoricAlarm",
            state_machine=self.sentinel_step_function_historic.sentinel_state_machine.ref,
            root_name="SentinelHistoric",
        )

        self.landsat_step_function_alarm = StepFunctionAlarm(
            self,
            "LandsatStepFunctionAlarm",
            state_machine=self.landsat_step_function.state_machine.ref,
            root_name="Landsat",
        )

        # Cross construct permissions
        self.addRDSpolicy()

        # Bucket policies
        self.laads_bucket_read_policy = aws_iam.PolicyStatement(
            resources=[
                self.laads_bucket.bucket_arn,
                f"{self.laads_bucket.bucket_arn}/*",
            ],
            actions=[
                "s3:Get*",
                "s3:List*",
            ],
        )
        self.laads_cron.function.add_to_role_policy(self.laads_bucket_read_policy)
        self.laads_available.function.add_to_role_policy(self.laads_bucket_read_policy)

        if DOWNLOADER_FUNCTION_ARN:
            self.downloader_function = aws_lambda.Function.from_function_arn(
                self, "DownloaderFunction", DOWNLOADER_FUNCTION_ARN
            )
            self.downloader_function.add_to_role_policy(
                aws_iam.PolicyStatement(
                    resources=[
                        self.sentinel_input_bucket.bucket_arn,
                        f"{self.sentinel_input_bucket.bucket_arn}/*",
                    ],
                    actions=["s3:PutObject*", "s3:Abort*"],
                )
            )

        self.sentinel_input_bucket_policy = aws_iam.PolicyStatement(
            resources=[
                self.sentinel_input_bucket.bucket_arn,
                f"{self.sentinel_input_bucket.bucket_arn}/*",
            ],
            actions=[
                "s3:Get*",
                "s3:List*",
            ],
        )
        self.check_twin_granule.function.add_to_role_policy(
            self.sentinel_input_bucket_policy
        )
        self.sentinel_task.role.add_to_policy(self.sentinel_input_bucket_policy)

        self.sentinel_input_bucket_historic_policy = aws_iam.PolicyStatement(
            resources=[
                self.sentinel_input_bucket_historic.bucket_arn,
                f"{self.sentinel_input_bucket_historic.bucket_arn}/*",
            ],
            actions=[
                "s3:Get*",
                "s3:List*",
            ],
        )
        self.check_twin_granule_historic.function.add_to_role_policy(
            self.sentinel_input_bucket_historic_policy
        )
        self.sentinel_task.role.add_to_policy(
            self.sentinel_input_bucket_historic_policy
        )

        self.laads_task.role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[
                    self.laads_bucket.bucket_arn,
                    f"{self.laads_bucket.bucket_arn}/*",
                ],
                actions=[
                    "s3:Get*",
                    "s3:Put*",
                    "s3:List*",
                    "s3:AbortMultipartUpload",
                ],
            )
        )
        self.laads_task.role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[
                    f"arn:aws:s3:::{LAADS_BUCKET_BOOTSTRAP}",
                    f"arn:aws:s3:::{LAADS_BUCKET_BOOTSTRAP}/*",
                ],
                actions=["s3:Get*", "s3:List*"],
            )
        )
        self.sentinel_task.role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[
                    self.gibs_intermediate_output_bucket.bucket_arn,
                    f"{self.gibs_intermediate_output_bucket.bucket_arn}/*",
                ],
                actions=[
                    "s3:Get*",
                    "s3:Put*",
                    "s3:List*",
                    "s3:AbortMultipartUpload",
                ],
            )
        )
        self.landsat_task.role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[
                    self.landsat_intermediate_output_bucket.bucket_arn,
                    f"{self.landsat_intermediate_output_bucket.bucket_arn}/*",
                ],
                actions=[
                    "s3:Get*",
                    "s3:Put*",
                    "s3:List*",
                    "s3:AbortMultipartUpload",
                ],
            )
        )
        self.landsat_task.role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[
                    "arn:aws:s3:::usgs-landsat",
                    "arn:aws:s3:::usgs-landsat/*",
                ],
                actions=[
                    "s3:Get*",
                    "s3:List*",
                ],
            )
        )
        self.landsat_tile_task.role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[
                    self.landsat_intermediate_output_bucket.bucket_arn,
                    f"{self.landsat_intermediate_output_bucket.bucket_arn}/*",
                ],
                actions=[
                    "s3:Get*",
                    "s3:List*",
                ],
            )
        )
        # Cross account role assumption for GCC bucket
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

    def addRDSpolicy(self):
        lambdas = [
            self.rds_bootstrap,
            self.landsat_mgrs_logger,
            self.landsat_mgrs_logger_historic,
            self.landsat_ac_logger,
            self.mgrs_logger,
            self.landsat_pathrow_status,
            self.sentinel_ac_logger,
            self.sentinel_logger,
            self.sentinel_logger_historic,
            self.update_sentinel_failure,
            self.check_landsat_pathrow_complete,
            self.landsat_incomplete_step_function_trigger.execute_step_function,
            self.landsat_historic_incomplete_step_function_trigger.execute_step_function,
            self.sentinel_errors_step_function_trigger.execute_step_function,
            self.sentinel_historic_errors_step_function_trigger.execute_step_function,
            self.landsat_logger,
            self.landsat_logger_historic,
            #  self.put_landsat_task_cw_metric,
            #  self.put_landsat_tile_task_cw_metric,
            #  self.put_sentintel_task_cw_metric,
            self.landsat_ac_errors_step_function_trigger.execute_step_function,
            self.landsat_historic_ac_errors_step_function_trigger.execute_step_function,
        ]
        for lambda_function in lambdas:
            lambda_function.function.add_to_role_policy(self.rds.policy_statement)
