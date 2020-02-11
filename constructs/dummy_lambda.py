from aws_cdk import core, aws_lambda, aws_stepfunctions, aws_stepfunctions_tasks
from utils import aws_env, align
from typing import Dict


class Dummy(core.Construct):
    """Dummy Lambda to use for testing that just kicks the event out to Cloud Watch Logs."""

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        env: Dict = {},
        timeout: int = 10,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        env_str = aws_env(env)

        code_doc = f"""
            def handler(event, context):
                print("{env_str}")
                print(event)
            """
        code = align(code_doc)

        self.lambdaFn = aws_lambda.Function(
            self,
            "Dummy",
            code=aws_lambda.InlineCode(code=code),
            timeout=core.Duration.seconds(timeout),
            handler="index.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_7,
        )

        self.task = aws_stepfunctions.Task(
            self,
            'DummyTask',
            task=aws_stepfunctions_tasks.InvokeFunction(self.lambdaFn)
        )

