from aws_cdk import aws_lambda, core
import os


class Lambda(core.Construct):
    """AWS Lambda Construct."""

    def __init__(
        self, 
        app: core.App, 
        id: str, 
        memory: int = 512, 
        timeout: int = 5,
        asset_dir: str = None,
    ) -> None:
        """Create AWS Lambda stack."""
        super().__init__(app, id)

        self.code = aws_lambda.Code.from_asset(
            os.path.join(os.path.dirname(__file__), "..", asset_dir)
        )

        self.lambdaFn = aws_lambda.Function(
            self,
            "function",
            code=self.code,
            handler="handler.handler",
            memory_size=memory,
            timeout=core.Duration.seconds(timeout),
            runtime=aws_lambda.Runtime.PYTHON_3_7,
        )
        
        core.CfnOutput(self, "lambdafunc", value=self.lambdaFn.function_arn)
