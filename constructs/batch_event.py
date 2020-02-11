from aws_cdk import core, aws_events, aws_lambda, aws_events_targets, aws_iam
import boto3
import json
from typing import Dict
from constructs.batch import Batch
from constructs.docker_batchjob import DockerBatchJob
from utils import aws_env, align


batch_client = boto3.client('batch')

class BatchCron(core.Construct):
    """AWS Batch Event Construct to Run Batch Jobs on a Cron using Lambda."""
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        cron_str: str,
        batch: Batch,
        job: DockerBatchJob,
        env: Dict = {},
        timeout: int = 10,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        
        queue=batch.jobqueue.ref
        jobdef=job.job.ref

        policy_statement = aws_iam.PolicyStatement(
            resources=[
                batch.jobqueue.ref,
                job.job.ref
            ],
            actions=[
                "batch:SubmitJob",
            ],
        )

        env_str = aws_env(env)

        code_doc=f"""
            import boto3
            import json
            batch_client = boto3.client('batch')

            def handler(event, context):
                print(event)
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
        code=align(code_doc)

        self.lambdaFn = aws_lambda.Function(
            self,
            'EventLambda',
            code=aws_lambda.InlineCode(code=code),
            timeout=core.Duration.seconds(timeout),
            handler='index.handler',
            runtime=aws_lambda.Runtime.PYTHON_3_7
        )

        self.lambdaFn.add_to_role_policy(policy_statement)

        self.rule = aws_events.Rule(
            self,
            "rule",
            schedule=aws_events.Schedule.expression(cron_str),
        )

        self.rule.add_target(aws_events_targets.LambdaFunction(self.lambdaFn))

        core.CfnOutput(self, "batchlambdafunc", value=self.lambdaFn.function_arn)
        core.CfnOutput(self, "batchjobname", value=f"{id}-job")
        core.CfnOutput(self, "batchjobrule", value=self.rule.rule_arn)