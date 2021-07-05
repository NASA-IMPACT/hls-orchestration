from aws_cdk import aws_s3, core, aws_iam
import boto3
import botocore


# Creates new S3 bucket. If bucket already exists will connect to existing bucket.
class S3(core.Construct):
    def __init__(
        self, scope: core.Construct, id: str, bucket_name: str = None, **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        if bucket_name is None:
            bucket_name = f"{id}-bucket"

        # check if bucket already exists
        try:
            boto3.client("s3").head_bucket(Bucket=bucket_name)
            bucket = aws_s3.Bucket.from_bucket_name(self, "bucket", bucket_name)
        except botocore.exceptions.ClientError:
            bucket = aws_s3.Bucket(self, "bucket", bucket_name=bucket_name)

        self.bucket = bucket
        self.bucket_name = bucket.bucket_name
        self.bucket_arn = bucket.bucket_arn
