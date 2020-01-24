"""Lambda Stack."""

import os
from aws_cdk import aws_lambda, core


class LambdaStack(core.Stack):
    """AWS Lambda Stack."""

    def __init__(
        self, app: core.App, id: str, memory: int = 512, timeout: int = 5
    ) -> None:
        """Create AWS Lambda stack."""
        super().__init__(app, id)

        code = aws_lambda.Code.from_asset(
            os.path.join(os.path.dirname(__file__), "..", "hls_pr2mgrs")
        )
        lambdaFn = aws_lambda.Function(
            self,
            "PathRow2MGRS",
            code=code,
            handler="handler.handler",
            memory_size=memory,
            timeout=core.Duration.seconds(timeout),
            runtime=aws_lambda.Runtime.PYTHON_3_7,
        )
