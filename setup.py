"""Setup for hls-orchestration"""

from setuptools import find_packages, setup

# Runtime requirements.
aws_cdk_extras = [
    "aws-cdk-lib>=2.0.0",
    "aws-cdk.aws-lambda-python-alpha",
    "constructs>=10.0.0",
]

install_requires: list[str] = []

extras_require_test = [
    *aws_cdk_extras,
    "flake8~=7.0",
    "black~=24.1",
    "boto3~=1.34",
    "pytest-cov~=4.1",
    "pytest~=8.0",
]

extras_require_dev = [
    *extras_require_test,
    "isort~=5.13",
    "nodeenv~=1.8",
    "pre-commit~=3.6",
    "pre-commit-hooks~=4.5",
]

extras_require = {
    "test": extras_require_test,
    "dev": extras_require_dev,
}


setup(
    name="hls-orchestration",
    version="0.0.1",
    python_requires=">=3.9",
    author="Development Seed",
    packages=find_packages(),
    package_data={
        ".": [
            "docker/hls-laads/*",
            "scripts/*",
            "cdk.json",
        ],
    },
    install_requires=install_requires,
    extras_require=extras_require,
    include_package_data=True,
)
