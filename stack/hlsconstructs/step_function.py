from aws_cdk import (
    aws_stepfunctions,
    aws_iam,
    core,
)
import json
from hlsconstructs.lambdafunc import Lambda


class StepFunction(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.steps_role = aws_iam.Role(
            self,
            "StepsRole",
            assumed_by=aws_iam.ServicePrincipal("states.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "CloudWatchEventsFullAccess"
                ),
            ],
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
                actions=[
                    "states:DescribeExecution",
                    "states:StopExecution"
                ]
            )
        )

        # Allow the step function role to invoke all its Lambdas.
        arguments = locals()
        for key in arguments:
            arg = arguments[key]
            if type(arg) == Lambda:
                self.steps_role.add_to_policy(
                    arg.invoke_policy_statement
                )
