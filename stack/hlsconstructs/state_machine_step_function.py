import json

from aws_cdk import aws_iam, aws_stepfunctions, core
from hlsconstructs.lambdafunc import Lambda
from hlsconstructs.step_function import StepFunction


class StateMachineStepFunction(StepFunction):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.steps_role.add_managed_policy(
            aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                "CloudWatchEventsFullAccess"
            )
        )

        region = core.Aws.REGION
        accountid = core.Aws.ACCOUNT_ID

        self.steps_role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[
                    f"arn:aws:events:{region}:{accountid}:rule/"
                    "StepFunctionsGetEventsForStepFunctionsExecutionRule",
                ],
                actions=["events:PutTargets", "events:PutRule", "events:DescribeRule"],
            )
        )

        self.steps_role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=["*"],
                actions=["states:DescribeExecution", "states:StopExecution"],
            )
        )
