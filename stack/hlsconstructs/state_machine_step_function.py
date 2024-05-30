import json

from aws_cdk import Aws, aws_iam, aws_stepfunctions
from constructs import Construct
from hlsconstructs.lambdafunc import Lambda
from hlsconstructs.step_function import StepFunction


class StateMachineStepFunction(StepFunction):
    def __init__(
        self,
        scope: Construct,
        id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.steps_role.add_managed_policy(
            aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                "CloudWatchEventsFullAccess"
            )
        )

        region = Aws.REGION
        accountid = Aws.ACCOUNT_ID

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
