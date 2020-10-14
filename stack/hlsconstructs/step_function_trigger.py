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
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        self.execute_step_function = Lambda(
            self,
            "ExecuteStepFunction",
            code_file=code_file,
            env={"STATE_MACHINE": state_machine},
            timeout=90,
        )
        if input_bucket is not None:
            self.event_source = aws_lambda_event_sources.S3EventSource(
                bucket=input_bucket, events=[aws_s3.EventType.OBJECT_CREATED]
            )
        if input_sns is not None:
            self.event_source = aws_lambda_event_sources.SnsEventSource(topic=input_sns)
        self.execute_step_function.function.add_event_source(self.event_source)
        self.execute_step_function.function.add_to_role_policy(
            aws_iam.PolicyStatement(
                resources=[state_machine], actions=["states:StartExecution"]
            )
        )
