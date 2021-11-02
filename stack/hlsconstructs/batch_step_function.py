import json

from aws_cdk import aws_iam, aws_stepfunctions, core
from hlsconstructs.step_function import StepFunction


class BatchStepFunction(StepFunction):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        region = core.Aws.REGION
        accountid = core.Aws.ACCOUNT_ID

        self.steps_role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[
                    f"arn:aws:events:{region}:{accountid}:rule/"
                    "StepFunctionsGetEventsForBatchJobsRule",
                ],
                actions=["events:PutTargets", "events:PutRule", "events:DescribeRule"],
            )
        )

        self.steps_role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=["*"],
                actions=["batch:SubmitJob", "batch:DescribeJobs", "batch:TerminateJob"],
            )
        )
