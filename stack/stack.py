import os
from aws_cdk import core
from constructs.network import Network
from constructs.s3 import S3
from constructs.efs import Efs
from constructs.docker_batchjob import DockerBatchJob
from constructs.batch import Batch
from constructs.lambdafunc import Lambda

STACKNAME = os.getenv("STACKNAME", "hls")
LAADS_BUCKET = os.getenv("LAADS_BUCKET", f"{STACKNAME}-bucket")

class HlsStack(core.Stack):
    def __init__(
        self, scope: core.Construct, id: str, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.network = Network(self, "Network")

        self.laads_bucket = S3(
            self, "S3", bucket_name=LAADS_BUCKET
        )

        self.efs = Efs(
            self,
            "Efs",
            network=self.network
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
        filesystem_uri = f"{filesystem.ref}.efs.{self.region}.amazonaws.com"
        
        self.batch = Batch(
            self,
            "Batch",
            network=self.network,
            efs_arn=filesystem_arn,
            efs=filesystem,
            efs_uri=filesystem_uri
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
            self,
            "Pr2Mgrs",
            asset_dir="hls-pr2mgrs/hls_pr2mgrs"
        )
