import os
import json
from aws_cdk import core, aws_stepfunctions
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

        self.network = Network(self, "Network")

        self.laads_bucket = S3(self, "S3", bucket_name=LAADS_BUCKET)

        self.efs = Efs(self, "Efs", network=self.network)
        filesystem = self.efs.filesystem
        filesystem_arn = core.Arn.format(
            {
                "resource-name": filesystem.ref,
                "service": "elasticfilesystem",
                "resource": "file-system",
            },
            self,
        )
        filesystem_uri = f"{filesystem.ref}.efs.{self.region}.amazonaws.com"

        self.batch = Batch(
            self,
            "Batch",
            network=self.network,
            efs_arn=filesystem_arn,
            efs=filesystem,
            efs_uri=filesystem_uri,
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

        self.pr2mgrs_lambda = Lambda(
            self, "Pr2Mgrs", asset_dir="hls-pr2mgrs/hls_pr2mgrs"
        )

        self.laads_available = Lambda(
            self,
            "LaadsAvailable",
            asset_dir="hls-laads-available/hls_laads_available",
            env={"LAADS_BUCKET": LAADS_BUCKET},
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
            },
        )

        self.wait = aws_stepfunctions.Wait(
            self,
            "wait",
            time=aws_stepfunctions.WaitTime.duration(core.Duration.seconds(3600)),
        )

        self.process_sentinel = Dummy(self, "ProcessSentinel")

        self.sentinel_step_definition = self.laads_available.task.next(
            aws_stepfunctions.Choice(self, "laads_available")
            .when(
                aws_stepfunctions.Condition.string_equals("$.available", "TRUE"),
                self.process_sentinel.task,
            )
            .otherwise(self.wait)
        )

        self.sentinel_state_machine = aws_stepfunctions.StateMachine(
            self, "SentinelStateMachine", definition=self.sentinel_step_definition
        )
