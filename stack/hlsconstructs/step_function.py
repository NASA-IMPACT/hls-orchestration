from typing import Any, Mapping

from aws_cdk import aws_iam
from constructs import Construct
from hlsconstructs.lambdafunc import Lambda


class StepFunction(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        self.steps_role = aws_iam.Role(
            self,
            "StepsRole",
            assumed_by=aws_iam.ServicePrincipal("states.amazonaws.com"),
        )

    def add_lambdas_to_role(self, arguments: Mapping[str, Any]):
        for arg in arguments.values():
            if isinstance(arg, Lambda):
                self.steps_role.add_to_policy(arg.invoke_policy_statement)
