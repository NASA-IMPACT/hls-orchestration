import os
from aws_cdk import aws_lambda, core, aws_iam
from typing import Dict



class Lambda(core.Construct):
    """AWS Lambda Construct."""

    def __init__(
        self, 
        scope: core.Construct, 
        id: str, 
        role: aws_iam.Role,
        memory: int = 512, 
        timeout: int = 5,
        asset_dir: str = None,
        env: Dict = None,
        **kwargs,
    ) -> None:
        """Create AWS Lambda stack."""
        super().__init__(scope, id, **kwargs)

        self.code = aws_lambda.Code.from_asset(
            os.path.join(os.path.dirname(__file__), "..", asset_dir)
        )

        self.lambdaFn = aws_lambda.Function(
            self,
            "function",
            code=self.code,
            handler="handler.handler",
            # role=role,
            memory_size=memory,
            timeout=core.Duration.seconds(timeout),
            runtime=aws_lambda.Runtime.PYTHON_3_7,
            environment=env,
        )

        self.policy_statement = aws_iam.PolicyStatement(
            resources=[self.lambdaFn.function_arn],
            actions=[
                "lambda:InvokeFunction",
            ],
        )

        role.add_to_policy(self.policy_statement)

        core.CfnOutput(self, "lambdafunc", value=self.lambdaFn.function_arn)
