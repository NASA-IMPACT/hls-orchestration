from aws_cdk import (
    aws_stepfunctions,
    aws_iam,
    core,
)
import json


class SentinelStepFunction(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        laads_available_function: str,
        outputbucket: str,
        sentinel_job_definition: str,
        jobqueue: str,
        lambda_logger: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        sentinel_state_definition = {
            "Comment": "Sentinel Step Function",
            "StartAt": "CheckLaads",
            "States": {
                "CheckLaads": {
                    "Type": "Task",
                    "Resource": laads_available_function,
                    "ResultPath": "$",
                    "Next": "LaadsAvailable",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": 1,
                            "MaxAttempts": 3,
                            "BackoffRate": 2,
                        }
                    ],
                    "Catch": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "Next": "LogError",
                        }
                    ],
                },
                "LaadsAvailable": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.available",
                            "BooleanEquals": True,
                            "Next": "ProcessSentinel",
                        }
                    ],
                    "Default": "Wait",
                },
                "Wait": {"Type": "Wait", "Seconds": 3600, "Next": "CheckLaads"},
                "ProcessSentinel": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::batch:submitJob.sync",
                    "Parameters": {
                        "JobName": "BatchJobNotification",
                        "JobQueue": jobqueue,
                        "JobDefinition": sentinel_job_definition,
                        "ContainerOverrides": {
                            "Command": ["export && sentinel.sh"],
                            "Memory": 10000,
                            "Environment": [
                                {"Name": "GRANULE_LIST", "Value.$": "$.granule"},
                                {"Name": "OUTPUT_BUCKET", "Value": outputbucket},
                                {"Name": "LASRC_AUX_DIR", "Value": "/var/lasrc_aux"},
                            ],
                        },
                    },
                    "Catch": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "Next": "LogError",
                        }
                    ],
                    "Next": "Log",
                },
                "Log": {
                    "Type": "Task",
                    "Resource": lambda_logger,
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
                "LogError": {
                    "Type": "Task",
                    "Resource": lambda_logger,
                    "ResultPath": "$",
                    "Next": "Error",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": 1,
                            "MaxAttempts": 3,
                            "BackoffRate": 2,
                        }
                    ],
                },
                "Done": {"Type": "Succeed"},
                "Error": {"Type": "Fail"},
            },
        }

        self.steps_role = aws_iam.Role(
            self,
            "StepsRole",
            assumed_by=aws_iam.ServicePrincipal("states.amazonaws.com"),
        )

        self.sentinel_state_machine = aws_stepfunctions.CfnStateMachine(
            self,
            "SentinelStateMachine",
            definition_string=json.dumps(sentinel_state_definition),
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
