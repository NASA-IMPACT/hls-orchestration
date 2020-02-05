from aws_cdk import (
    aws_ecr_assets,
    aws_batch,
    aws_ecs,
    aws_iam,
    aws_s3,
    core,
)
import os

dirname = os.path.dirname(os.path.realpath(__file__))


class DockerBatchJob(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        dockerdir: str,
        bucket: aws_s3.Bucket = None,
        timeout: int = 3600,
        memory: int = 10000,
        vcpus: int = 4,
        mountpath: str = "/efs",
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        policies = None
        if bucket is not None:
            s3_policy_statement = aws_iam.PolicyStatement(
                resources=[
                    bucket.bucket_arn,
                    f"{bucket.bucket_arn}/*",
                ],
                actions=[
                    "s3:Get*",
                    "s3:Put*",
                    "s3:List*",
                    "s3:AbortMultipartUpload",
                ],
            )
            s3_policy_document = aws_iam.PolicyDocument(
                statements=[s3_policy_statement]
            )
            policies = [s3_policy_document]

        role = aws_iam.Role(
            self,
            "taskrole",
            assumed_by=aws_iam.ServicePrincipal(
                "ecs-tasks.amazonaws.com"
            ),
            inline_policies=policies,
        )

        host = aws_batch.CfnJobDefinition.VolumesHostProperty(
            source_path="/mnt/efs"
        )

        volume = aws_batch.CfnJobDefinition.VolumesProperty(
            name=f"volume", host=host,
        )

        image = aws_ecr_assets.DockerImageAsset(
            self,
            "DockerImageAsset",
            directory=os.path.join(
                dirname, "..", "docker", dockerdir
            ),
        )

        mount_point = aws_batch.CfnJobDefinition.MountPointsProperty(
            source_volume=volume.name,
            container_path=mountpath,
            read_only=False,
        )

        container_properties = aws_batch.CfnJobDefinition.ContainerPropertiesProperty(
            image=image.image_uri,
            job_role_arn=role.role_arn,
            memory=memory,
            mount_points=[mount_point],
            vcpus=vcpus,
            volumes=[volume],
        )

        job = aws_batch.CfnJobDefinition(
            self,
            f"batchjob",
            container_properties=container_properties,
            retry_strategy=aws_batch.CfnJobDefinition.RetryStrategyProperty(
                attempts=1
            ),
            timeout=aws_batch.CfnJobDefinition.TimeoutProperty(
                attempt_duration_seconds=timeout
            ),
            type="Container",
        )

        self.image = image
        self.job = job
        self.role = role

        core.CfnOutput(self, f"jobdef", value=job.ref)
