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
        landsat_ac_logger: str,
        pr2mgrs: str,
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
            "StartAt": "CheckLaads",
            "States": {
                "CheckLaads": {
                    "Type": "Task",
                    "Resource": laads_available_function,
                    "Parameters": {
                        "granule.$": "$.scene",
                        "scene_meta.$": "$"
                    },
                    "ResultPath": "$.taskresult",
                    "Next": "LaadsAvailable",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": 1,
                            "MaxAttempts": 3,
                            "BackoffRate": 2,
                        }
                    ],
                    "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "LogError",}],
                },
                "LaadsAvailable": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.taskresult.available",
                            "BooleanEquals": True,
                            "Next": "GetMGRSValues",
                        }
                    ],
                    "Default": "Wait",
                },
                "Wait": {"Type": "Wait", "Seconds": 3600, "Next": "CheckLaads"},
                "GetMGRSValues": {
                    "Type": "Task",
                    "Resource": pr2mgrs,
                    "ResultPath": "$.mgrsvalues",
                    "Next": "MGRSExists",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": 1,
                            "MaxAttempts": 3,
                            "BackoffRate": 2,
                        }
                    ],
                },
                "MGRSExists": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.mgrsvalues.count",
                            "NumericGreaterThan": 0,
                            "Next": "LandsatMGRSLog",
                        }
                    ],
                    "Default": "Done",
                },
                "LandsatMGRSLog": {
                    "Type": "Task",
                    "Resource": landsat_mgrs_logger,
                    "ResultPath": None,
                    "Next": "LandsatAcLog",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": 1,
                            "MaxAttempts": 3,
                            "BackoffRate": 2,
                        }
                    ],
                },
                "LandsatAcLog": {
                    "Type": "Task",
                    "Resource": landsat_ac_logger,
                    "ResultPath": None,
                    "Next": "ProcessMGRSGrid",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": 1,
                            "MaxAttempts": 3,
                            "BackoffRate": 2,
                        }
                    ],
                },
                "ProcessMGRSGrid": {
                    "Type": "Map",
                    "ItemsPath": "$.mgrsvalues.mgrs",
                    "ResultPath": "$.pathrows",
                    "Parameters": {
                        "MGRS.$": "$$.Map.Item.Value",
                        "path.$": "$.path"
                    },
                    "MaxConcurrency": 0,
                    "Iterator": {
                        "StartAt": "GetPathRowValues",
                        "States": {
                            "GetPathRowValues": {
                                "Type": "Task",
                                "Resource": pr2mgrs,
                                "End": True
                            }
                        }
                    },
                    "End": True
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
