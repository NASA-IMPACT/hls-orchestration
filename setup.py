"""Setup for hls-orchestration"""

from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()

# Runtime requirements.
aws_cdk_min_version = "1.22.0"
aws_cdk_reqs = [
    "core",
    "aws-s3",
    "aws-iam",
    "aws-lambda",
    "aws-efs",
    "aws-ecs",
    "aws-batch",
    "aws-ecr-assets",
    "aws-events",
    "aws-events-targets",
    "aws-stepfunctions",
]

inst_reqs = ["boto3"]

inst_reqs.append([f"aws_cdk.{x}>={aws_cdk_min_version}" for x in aws_cdk_reqs])

extra_reqs = {
    "test": ["pytest", "pytest-cov", "black", "flake8"]
}

setup(
    name="hls-orchestration",
    version="0.0.1",
    python_requires=">=3.7",
    author="Vincent Sarago",
    author_email="vincent@developmentseed.org",
    packages=find_packages(),
    package_data={
        ".": [
            "docker/hls-laads/*",
            "scripts/*",
            "cdk.json",
            "lambda/p2mgrs/hls_pr2mgrs/*",
            "lambda/laads-available/hls_laads_available/*",
            "stack/constructs/userdata.txt",
        ],
    },
    install_requires=inst_reqs,
    extras_require=extra_reqs,
    include_package_data=True,
)
