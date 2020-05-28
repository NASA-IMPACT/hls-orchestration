from aws_cdk import (
    aws_stepfunctions,
    aws_iam,
    core,
)
import json


class LandsatStepFunction(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        laads_available_function: str,
        outputbucket: str,
        # outputbucket_role_arn: str,
        intermediate_output_bucket: str,
        ac_job_definition: str,
        # tiling_job_definition: str,
        jobqueue: str,
        lambda_logger: str,
        landsat_mgrs_logger: str,
        replace_existing: bool,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # if replace_existing:
        # replace = "replace"
        # else:
        # replace = None

        state_definition = {
            "Comment": "Landsat Step Function",
            "StartAt": "LandsatMGRSLog",
            "States": {
                "LandsatMGRSLog": {
                    "Type": "Task",
                    "Resource": landsat_mgrs_logger,
                    "ResultPath": "$",
                    "Next": "Done",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": 1,
                            "MaxAttempts": 3,
                            "BackoffRate": 2,
                        }
                    ],
                },
                "Done": {"Type": "Succeed"}
            },
        }

        self.steps_role = aws_iam.Role(
            self,
            "StepsRole",
            assumed_by=aws_iam.ServicePrincipal("states.amazonaws.com"),
        )

        self.state_machine = aws_stepfunctions.CfnStateMachine(
            self,
            "LandsatStateMachine",
            definition_string=json.dumps(state_definition),
            role_arn=self.steps_role.role_arn,
        )

        region = core.Aws.REGION
        acountid = core.Aws.ACCOUNT_ID
        self.steps_role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[
                    f"arn:aws:events:{region}:{acountid}:rule/"
                    "StepFunctionsGetEventsForBatchJobsRule",
                ],
                actions=["events:PutTargets", "events:PutRule", "events:DescribeRule"],
            )
        )
        self.steps_role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=["*",],
                actions=["batch:SubmitJob", "batch:DescribeJobs", "batch:TerminateJob"],
            )
        )
