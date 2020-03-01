from aws_cdk import (
    core,
    aws_s3,
    aws_iam,
    aws_stepfunctions,
    aws_events,
    aws_events_targets,
    aws_lambda_event_sources,
)
from constructs.lambdafunc import Lambda


class StepFunctionTrigger(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        input_bucket_name: str,
        state_machine: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        self.bucket = aws_s3.Bucket(
            self,
            "InputBucket",
            bucket_name=input_bucket_name
        )
        self.execute_step_function = Lambda(
            self,
            "ExecuteStepFunction",
            code_dir="execute_step_function/hls_execute_step_function",
            env={"STATE_MACHINE": state_machine},
            handler="handler.handler"
        )

        self.s3_event_source = aws_lambda_event_sources.S3EventSource(
            bucket=self.bucket,
            events=[aws_s3.EventType.OBJECT_CREATED]
        )
        self.execute_step_function.function.add_event_source(
            self.s3_event_source
        )
        self.execute_step_function.function.add_to_role_policy(
            aws_iam.PolicyStatement(
                resources=[
                    state_machine
                ],
                actions=[
                    "states:StartExecution"
                ]
            )
        )
