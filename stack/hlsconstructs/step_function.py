import json

from aws_cdk import aws_iam, aws_stepfunctions, core
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
        )

    def addLambdasToRole(self, arguments):
        for key in arguments:
            arg = arguments[key]
            if type(arg) == Lambda:
                self.steps_role.add_to_policy(arg.invoke_policy_statement)
