import os
from aws_cdk import aws_lambda, core, aws_iam
from typing import Dict
from utils import align


class Lambda(core.Construct):
    """AWS Lambda Construct."""

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        memory: int = 512,
        timeout: int = 5,
        code_dir: str = None,
        code_file: str = None,
        code_str: str = None,
        env: Dict = None,
        runtime: aws_lambda.Runtime = aws_lambda.Runtime.PYTHON_3_7,
        handler: str = "index.handler",
        layers: list = None,
        **kwargs,
    ) -> None:
        """Create AWS Lambda stack."""
        super().__init__(scope, id, **kwargs)

        if code_dir is not None:
            self.code = aws_lambda.Code.from_asset(
                os.path.join(
                    os.path.dirname(__file__), "..", "..", "lambda_functions", code_dir
                )
            )
        elif code_file is not None:
            file = os.path.join(
                os.path.dirname(__file__), "..", "..", "lambda_functions", code_file
            )
            with open(file, encoding="utf8") as fp:
                code_str = fp.read()
            self.code = aws_lambda.InlineCode(code=code_str)
            self.handler = "index.handler"
        elif code_str is not None:
            code_str = align(code_str)
            self.code = aws_lambda.InlineCode(code=code_str)
            self.handler = "index.handler"

        if self.code is None:
            raise Exception("Must define function code")

        self.handler = handler

        self.function = aws_lambda.Function(
            self,
            "function",
            code=self.code,
            handler=self.handler,
            memory_size=memory,
            timeout=core.Duration.seconds(timeout),
            runtime=runtime,
            environment=env,
        )

        if layers is not None:
            for layer in layers:
                self.function.add_layers(layer)

        self.invoke_policy_statement = aws_iam.PolicyStatement(
            resources=[self.function.function_arn], actions=["lambda:InvokeFunction",],
        )
