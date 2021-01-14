from aws_cdk import (
    core,
    aws_s3,
    aws_iam,
    aws_stepfunctions,
    aws_events,
    aws_events_targets,
    aws_lambda_event_sources,
    aws_sns,
)
from hlsconstructs.lambdafunc import Lambda


class StepFunctionTrigger(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        state_machine: str,
        code_file: str,
        input_bucket: aws_s3.Bucket = None,
        input_sns: aws_sns.Topic = None,
        days_prior: str = None,
        cron_str: str = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        if days_prior:
            env = {
                "STATE_MACHINE": state_machine,
                "DAYS_PRIOR": days_prior
            }
        else:
            env = {
                "STATE_MACHINE": state_machine
            }

        self.execute_step_function = Lambda(
            self,
            "ExecuteStepFunction",
            code_file=code_file,
            timeout=90,
            env=env
        )

        if input_bucket is not None:
            self.event_source = aws_lambda_event_sources.S3EventSource(
                bucket=input_bucket, events=[aws_s3.EventType.OBJECT_CREATED]
            )
        if input_sns is not None:
            self.event_source = aws_lambda_event_sources.SnsEventSource(
                topic=input_sns
            )
        if cron_str is not None:
            self.rule = aws_events.Rule(
                self, "Rule", schedule=aws_events.Schedule.expression(cron_str),
            )
            self.rule.add_target(
                aws_events_targets.LambdaFunction(
                    self.execute_step_function.function
                )
            )
        else:
            self.execute_step_function.function.add_event_source(self.event_source)

        self.execute_step_function.function.add_to_role_policy(
            aws_iam.PolicyStatement(
                resources=[state_machine], actions=["states:StartExecution"]
            )
        )
