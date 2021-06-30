from aws_cdk import (
    aws_stepfunctions,
    aws_iam,
    core,
)
import json


class LandsatIncompleteStepFunction(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        outputbucket: str,
        intermediate_output_bucket: str,
        outputbucket_role_arn: str,
        tilejobqueue: str,
        tile_job_definition: str,
        pr2mgrs: str,
        mgrs_logger: str,
        check_mgrs_pathrow_complete: str,
        get_random_wait: str,
        gibs_outputbucket: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        retry = {
            "ErrorEquals": ["States.ALL"],
            "IntervalSeconds": 10,
            "MaxAttempts": 3,
            "BackoffRate": 2,
        }
        state_definition = {
            "Comment": "Landsat Incomplete Step Function",
            "StartAt": "ProcessIncompletes",
            "States": {
                "ProcessIncompletes": {
                    "Type": "Map",
                    "ItemsPath": "$.incompletes",
                    "MaxConcurrency": 100,
                    "Iterator": {
                        "StartAt": "GetPathRowValues",
                        "States": {
                            "GetPathRowValues": {
                                "Type": "Task",
                                "Resource": pr2mgrs,
                                "ResultPath": "$.mgrs_metadata",
                                "Next": "CheckMGRSPathRowCompletes",
                                "Catch": [
                                    {
                                        "ErrorEquals": ["States.ALL"],
                                        "Next": "SuccessState",
                                    }
                                ],
                            },
                            "CheckMGRSPathRowCompletes": {
                                "Type": "Task",
                                "Resource": check_mgrs_pathrow_complete,
                                "ResultPath": "$.mgrs_completed",
                                "Next": "ReadyForTiling",
                                "Catch": [
                                    {
                                        "ErrorEquals": ["States.ALL"],
                                        "Next": "SuccessState",
                                    }
                                ],
                            },
                            "ReadyForTiling": {
                                "Type": "Choice",
                                "Choices": [
                                    {
                                        "Variable": "$.mgrs_completed",
                                        "IsNull": False,
                                        "Next": "GetRandomWaitTile",
                                    }
                                ],
                                "Default": "SuccessState",
                            },
                            "GetRandomWaitTile": {
                                "Type": "Task",
                                "Resource": get_random_wait,
                                "ResultPath": "$.wait_time",
                                "Next": "WaitForTiling",
                            },
                            "WaitForTiling": {
                                "Type": "Wait",
                                "SecondsPath": "$.wait_time",
                                "Next": "RunLandsatTile"
                            },
                            "RunLandsatTile": {
                                "Type": "Task",
                                "Resource": "arn:aws:states:::batch:submitJob.sync",
                                "ResultPath": "$.tilejobinfo",
                                "Parameters": {
                                    "JobName": "LandsatTileJob",
                                    "JobQueue": tilejobqueue,
                                    "JobDefinition": tile_job_definition,
                                    "ContainerOverrides": {
                                        "Command": ["export && landsat-tile.sh"],
                                        "Environment": [
                                            {
                                                "Name": "PATHROW_LIST",
                                                "Value.$": "$.mgrs_completed"
                                            },
                                            {
                                                "Name": "INPUT_BUCKET",
                                                "Value": intermediate_output_bucket
                                            },
                                            {
                                                "Name": "OUTPUT_BUCKET",
                                                "Value": outputbucket
                                            },
                                            {
                                                "Name": "GCC_ROLE_ARN",
                                                "Value": outputbucket_role_arn,
                                            },
                                            {
                                                "Name": "DATE",
                                                "Value.$": "$.date"
                                            },
                                            {
                                                "Name": "MGRS",
                                                "Value.$": "$.MGRS"
                                            },
                                            {
                                                "Name": "LANDSAT_PATH",
                                                "Value.$": "$.path"
                                            },
                                            {
                                                "Name": "MGRS_ULX",
                                                "Value.$": "$.mgrs_metadata.mgrs_ulx"
                                            },
                                            {
                                                "Name": "MGRS_ULY",
                                                "Value.$": "$.mgrs_metadata.mgrs_uly"
                                            },
                                            {
                                                "Name": "GIBS_OUTPUT_BUCKET",
                                                "Value": gibs_outputbucket
                                            },
                                        ],
                                    },
                                },
                                "Catch": [
                                    {
                                        "ErrorEquals": ["States.ALL"],
                                        "Next": "LogMGRS",
                                        "ResultPath": "$.tilejobinfo",
                                    }
                                ],
                                "Next": "LogMGRS",
                            },
                            "LogMGRS": {
                                "Type": "Task",
                                "Resource": mgrs_logger,
                                "Next": "SuccessState",
                                "Retry": [retry],
                            },
                            "SuccessState": {"Type": "Succeed"},
                        }
                    },
                    "Next": "Done",
                },
                "Done": {"Type": "Succeed"},
            }
        }
        self.steps_role = aws_iam.Role(
            self,
            "LandsatIncompletesStepsRole",
            assumed_by=aws_iam.ServicePrincipal("states.amazonaws.com"),
        )
        self.state_machine = aws_stepfunctions.CfnStateMachine(
            self,
            "LandsatIncompletesStateMachine",
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
