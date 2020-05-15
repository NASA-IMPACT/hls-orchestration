from aws_cdk import core, aws_lambda
from utils import aws_env, align
from typing import Dict
from hlsconstructs.lambdafunc import Lambda


class Dummy(Lambda):
    """Dummy Lambda to use for testing."""

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        env: Dict = {},
        timeout: int = 10,
        code_str: str = None,
        **kwargs,
    ) -> None:

        env_str = aws_env(env)
        code_str = f"""
            def handler(event, context):
                print("{env_str}")
                print(event)
                return event
            """
        code_str = align(code_str)
        self.code = aws_lambda.InlineCode(code=code_str)
        super().__init__(scope, id, **kwargs)
