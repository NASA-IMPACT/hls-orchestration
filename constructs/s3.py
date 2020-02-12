from aws_cdk import aws_s3, core, aws_iam
import boto3
import botocore


# Creates new S3 bucket. If bucket already exists will connect to existing bucket.
class S3(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        bucket_name: str = None,
        role: aws_iam.Role = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        if bucket_name is None:
            bucket_name = f"{id}-bucket"

        # check if bucket already exists
        try:
            boto3.client("s3").head_bucket(Bucket=bucket_name)
            bucket = aws_s3.Bucket.from_bucket_name(
                self, f"bucket", bucket_name
            )
        except botocore.exceptions.ClientError:
            bucket = aws_s3.Bucket(
                self, f"bucket", bucket_name=bucket_name
            )

        self.policy_statement = aws_iam.PolicyStatement(
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
        role.add_to_policy(self.policy_statement)

        self.bucket = bucket
        self.bucket_name = bucket.bucket_name
        self.bucket_arn = bucket.bucket_arn

        core.CfnOutput(self, "bucket_arn", value=bucket.bucket_arn)
        core.CfnOutput(self, "bucket_name", value=bucket.bucket_name)
