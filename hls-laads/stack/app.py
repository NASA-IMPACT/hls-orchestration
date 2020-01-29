import os
from aws_cdk import core
from constructs.network import Network
from constructs.s3 import S3
from constructs.efs import Efs
from constructs.docker_batchjob import DockerBatchJob
from constructs.batch import Batch

STACKNAME = os.getenv("STACKNAME", "hls")
LAADS_BUCKET = os.getenv("LAADS_BUCKET", "bitner-devseed-hls-ouput")
LAADS_SCHEDULE = os.getenv("LAADS_SCHEDULE", "cron(0 0/12 * * ? *)")


class HlsStack(core.Stack):
    def __init__(
        self, scope: core.Construct, id: str, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.network = Network(self, "network")
        security_group = self.network.security_group
        vpc = self.network.vpc

        self.laads_bucket = S3(
            self, "s3", bucket_name=LAADS_BUCKET
        )

        self.efs = Efs(
            self,
            "efs",
            vpc=vpc,
            security_group=security_group,
        )
        filesystem = self.efs.filesystem
        filesystem_arn = core.Arn.format(
            {
                "resource-name": filesystem.ref,
                "service": "elasticfilesystem",
                "resource": "file-system",
            },
            self
        )

        self.batch = Batch(
            self,
            "batch",
            vpc=vpc,
            efs_arn=filesystem_arn,
            efs=filesystem,
            security_group=security_group,
        )

        self.laads_task = DockerBatchJob(
            self,
            "laads-task",
            dockerdir="laads",
            bucket=LAADS_BUCKET,
            mountpath="/var/lasrc_aux",
            timeout=259200,
            memory=10000,
            vcpus=4,
        )

app = core.App()
hls_stack = HlsStack(
    app,
    STACKNAME,
    stack_name=STACKNAME,
)
app.synth()
