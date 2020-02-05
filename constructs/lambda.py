from aws_cdk import aws_lambda, core


class LambdaConstruct(core.Construct):
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

        code = aws_lambda.Code.from_asset(
            os.path.join(os.path.dirname(__file__), "..", asset_dir)
        )
        lambdaFn = aws_lambda.Function(
            self,
            "function",
            code=code,
            handler="handler.handler",
            memory_size=memory,
            timeout=core.Duration.seconds(timeout),
            runtime=aws_lambda.Runtime.PYTHON_3_7,
        )
