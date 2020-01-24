"""Setup for cdk-watchbot."""

from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()

# Runtime requirements.
inst_reqs = []

extra_reqs = {
    "test": ["pytest", "pytest-cov"],
    "deploy": ["aws-cdk.core", "aws-cdk.aws_lambda"],
}

setup(
    name="hls-pr2mgrs",
    version="0.0.1",
    python_requires=">=3.7",
    author=u"Vincent Sarago",
    author_email="vincent@developmentseed.org",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    package_data={"hls_pr2mgrs": ["data/L8S2overlap.txt"]},
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
