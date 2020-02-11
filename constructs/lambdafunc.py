from aws_cdk import aws_lambda, core, aws_stepfunctions, aws_stepfunctions_tasks
import os
from typing import Dict



class Lambda(core.Construct):
    """AWS Lambda Construct."""

    def __init__(
        self, 
        scope: core.Construct, 
        id: str, 
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
            memory_size=memory,
            timeout=core.Duration.seconds(timeout),
            runtime=aws_lambda.Runtime.PYTHON_3_7,
            environment=env,
        )

        self.task = aws_stepfunctions.Task(
            self,
            'SfTask',
            task=aws_stepfunctions_tasks.InvokeFunction(self.lambdaFn)
        )
        
        core.CfnOutput(self, "lambdafunc", value=self.lambdaFn.function_arn)
