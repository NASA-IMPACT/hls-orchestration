import os
from typing import Dict

from aws_cdk import (
    aws_events,
    aws_events_targets,
    aws_iam,
    aws_lambda,
    aws_lambda_python,
    core,
)
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
        package_code_dir: str = None,
        env: Dict = None,
        runtime: aws_lambda.Runtime = aws_lambda.Runtime.PYTHON_3_8,
        handler: str = "index.handler",
        layers: list = None,
        cron_str: str = None,
        **kwargs,
    ) -> None:
        """Create AWS Lambda stack."""
        super().__init__(scope, id, **kwargs)

        if package_code_dir is not None:
            absolute_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "lambda_functions",
                package_code_dir,
            )
            self.function = aws_lambda_python.PythonFunction(
                self,
                "function",
                entry=absolute_path,
                index="index.py",
                memory_size=memory,
                timeout=core.Duration.seconds(timeout),
                runtime=runtime,
                environment=env,
            )
        else:
            if code_dir is not None:
                self.code = aws_lambda.Code.from_asset(
                    os.path.join(
                        os.path.dirname(__file__),
                        "..",
                        "..",
                        "lambda_functions",
                        code_dir,
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

        if cron_str is not None:
            self.rule = aws_events.Rule(
                self,
                "rule",
                schedule=aws_events.Schedule.expression(cron_str),
            )
            self.rule.add_target(aws_events_targets.LambdaFunction(self.function))

        self.invoke_policy_statement = aws_iam.PolicyStatement(
            resources=[self.function.function_arn],
            actions=[
                "lambda:InvokeFunction",
            ],
        )
