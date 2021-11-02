from typing import Dict

from aws_cdk import aws_events, aws_events_targets, aws_iam, aws_lambda, core
from hlsconstructs.docker_batchjob import DockerBatchJob
from hlsconstructs.lambdafunc import Lambda
from utils import align, aws_env


class BatchCron(Lambda):
    """AWS Batch Event Construct to Run Batch Jobs on a Cron using Lambda."""

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        cron_str: str,
        queue: str,
        job: DockerBatchJob,
        env: Dict = {},
        timeout: int = 10,
        **kwargs,
    ) -> None:

        jobdef = job.job.ref

        env_str = aws_env(env)

        code_str = f"""
            import boto3
            import json
            batch_client = boto3.client('batch')

            def handler(event, context):
                print(event)
                print({env_str})
                response = batch_client.submit_job(
                    jobName="{id}-job",
                    jobQueue="{queue}",
                    jobDefinition="{jobdef}",
                    containerOverrides={{
                        'environment': {env_str}
                    }}
                )
                print(response)
                return response
            """
        code_str = align(code_str)
        self.code = aws_lambda.InlineCode(code=code_str)

        super().__init__(scope, id, **kwargs)

        self.rule = aws_events.Rule(
            self, "Rule", schedule=aws_events.Schedule.expression(cron_str),
        )

        self.rule.add_target(aws_events_targets.LambdaFunction(self.function))

        self.function.add_to_role_policy(
            aws_iam.PolicyStatement(
                resources=[jobdef],
                actions=["batch:SubmitJob", "batch:DescribeJobs", "batch:TerminateJob"],
            )
        )
        self.function.add_to_role_policy(
            aws_iam.PolicyStatement(
                resources=[queue],
                actions=["batch:SubmitJob", "batch:DescribeJobs", "batch:TerminateJob"],
            )
        )
