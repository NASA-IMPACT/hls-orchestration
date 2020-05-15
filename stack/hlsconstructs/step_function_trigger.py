from aws_cdk import (
    core,
    aws_s3,
    aws_iam,
    aws_stepfunctions,
    aws_events,
    aws_events_targets,
    aws_lambda_event_sources,
)
from hlsconstructs.lambdafunc import Lambda


class StepFunctionTrigger(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        input_bucket: aws_s3.Bucket,
        state_machine: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        self.execute_step_function = Lambda(
            self,
            "ExecuteStepFunction",
            code_dir="execute_step_function/hls_execute_step_function",
            env={"STATE_MACHINE": state_machine},
            handler="handler.handler",
        )

        self.s3_event_source = aws_lambda_event_sources.S3EventSource(
            bucket=input_bucket, events=[aws_s3.EventType.OBJECT_CREATED]
        )
        self.execute_step_function.function.add_event_source(self.s3_event_source)
        self.execute_step_function.function.add_to_role_policy(
            aws_iam.PolicyStatement(
                resources=[state_machine], actions=["states:StartExecution"]
            )
        )
