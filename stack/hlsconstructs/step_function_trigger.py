from typing import Dict, List

from aws_cdk import (
    aws_events,
    aws_events_targets,
    aws_iam,
    aws_lambda,
    aws_lambda_event_sources,
    aws_s3,
    aws_sns,
    aws_stepfunctions,
)
from constructs import Construct
from hlsconstructs.lambdafunc import Lambda


class StepFunctionTrigger(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        state_machine: str,
        code_file: str,
        timeout: int,
        lambda_name: str = "ExecuteStepFunction",
        layers: List[aws_lambda.LayerVersion] = None,
        input_bucket: aws_s3.Bucket = None,
        input_sns: aws_sns.Topic = None,
        env_vars: Dict[str, str] = None,
        cron_str: str = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        env = {
            "STATE_MACHINE": state_machine,
        }
        if env_vars:
            env.update(env_vars)

        self.execute_step_function = Lambda(
            self,
            lambda_name,
            code_file=code_file,
            timeout=timeout,
            env=env,
            layers=layers,
            runtime=aws_lambda.Runtime.PYTHON_3_8,
        )

        if input_bucket is not None:
            self.event_source = aws_lambda_event_sources.S3EventSource(
                bucket=input_bucket, events=[aws_s3.EventType.OBJECT_CREATED]
            )
        if input_sns is not None:
            self.event_source = aws_lambda_event_sources.SnsEventSource(topic=input_sns)
        if cron_str is not None:
            self.rule = aws_events.Rule(
                self,
                "Rule",
                schedule=aws_events.Schedule.expression(cron_str),
            )
            self.rule.add_target(
                aws_events_targets.LambdaFunction(self.execute_step_function.function)
            )
        else:
            self.execute_step_function.function.add_event_source(self.event_source)

        self.execute_step_function.function.add_to_role_policy(
            aws_iam.PolicyStatement(
                resources=[state_machine], actions=["states:StartExecution"]
            )
        )
