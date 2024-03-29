"""Setup for hls-orchestration"""


from setuptools import find_packages, setup

# Runtime requirements.
aws_cdk_version = "1.203.0"
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
    "aws-rds",
    "aws-secretsmanager",
    "aws-lambda-event-sources",
    "aws-ssm",
    "aws-sns",
    "aws-cloudwatch",
    "aws-cloudwatch-actions",
    "aws-lambda-python",
]

inst_reqs = [
    "boto3",
    *[f"aws_cdk.{x}=={aws_cdk_version}" for x in aws_cdk_reqs],
]

extra_reqs = {
    "test": [
        "pytest",
        "pytest-cov",
        "black",
        "flake8",
        "isort",
    ],
    "dev": [
        "pytest",
        "black",
        "flake8",
        "nodeenv",
        "isort",
        "mypy",
        "pre-commit",
        "pre-commit-hooks",
    ],
}

setup(
    name="hls-orchestration",
    version="0.0.1",
    python_requires=">=3.7",
    author="Development Seed",
    packages=find_packages(),
    package_data={
        ".": [
            "docker/hls-laads/*",
            "scripts/*",
            "cdk.json",
        ],
    },
    install_requires=inst_reqs,
    extras_require=extra_reqs,
    include_package_data=True,
)
