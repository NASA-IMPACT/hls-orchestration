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
        outputbucket_role_arn: str,
        intermediate_output_bucket: str,
        ac_job_definition: str,
        tile_job_definition: str,
        acjobqueue: str,
        tilejobqueue: str,
        lambda_logger: str,
        landsat_mgrs_logger: str,
        landsat_ac_logger: str,
        landsat_pathrow_status: str,
        pr2mgrs: str,
        mgrs_logger: str,
        check_landsat_tiling_exit_code: str,
        check_landsat_ac_exit_code: str,
        replace_existing: bool,
        gibs_outputbucket: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        lambda_interval = 10
        lambda_max_attempts = 3
        lambda_backoff_rate = 2

        if replace_existing:
            replace = "replace"
        else:
            replace = None

        state_definition = {
            "Comment": "Landsat Step Function",
            "StartAt": "GetMGRSValues",
            "States": {
                "GetMGRSValues": {
                    "Type": "Task",
                    "Resource": pr2mgrs,
                    "ResultPath": "$.mgrsvalues",
                    "Next": "MGRSExists",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": lambda_interval,
                            "MaxAttempts": lambda_max_attempts,
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
                            "Next": "CheckLaads",
                        },
                        {
                            "Variable": "$.mgrsvalues.count",
                            "NumericEquals": 0,
                            "Next": "LogNoMGRS",
                        }
                    ],
                    "Default": "Done",
                },
                "LogNoMGRS": {
                    "Type": "Task",
                    "Resource": landsat_ac_logger,
                    "ResultPath": None,
                    "Next": "Done",
                    "Parameters": {
                        "jobinfo": {
                            "JobId": "mgrs_skipped",
                        },
                        "scene.$": "$.scene"
                    },
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": lambda_interval,
                            "MaxAttempts": lambda_max_attempts,
                            "BackoffRate": 2,
                        }
                    ],
                },
                "CheckLaads": {
                    "Type": "Task",
                    "Resource": laads_available_function,
                    "Parameters": {"granule.$": "$.scene", "scene_meta.$": "$"},
                    "ResultPath": "$.taskresult",
                    "Next": "LaadsAvailable",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": lambda_interval,
                            "MaxAttempts": lambda_max_attempts,
                            "BackoffRate": lambda_backoff_rate,
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
                            "Next": "LogLandsatMGRS",
                        }
                    ],
                    "Default": "Wait",
                },
                "Wait": {"Type": "Wait", "Seconds": 3600, "Next": "CheckLaads"},
                "LogLandsatMGRS": {
                    "Type": "Task",
                    "Resource": landsat_mgrs_logger,
                    "ResultPath": None,
                    "Next": "WaitForAc",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": lambda_interval,
                            "MaxAttempts": lambda_max_attempts,
                            "BackoffRate": lambda_backoff_rate,
                        }
                    ],
                },
                "WaitForAc": {"Type": "Wait", "Seconds": 60, "Next": "RunLandsatAc"},
                "RunLandsatAc": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::batch:submitJob.sync",
                    "ResultPath": "$.jobinfo",
                    "Parameters": {
                        "JobName": "LandsatAcJob",
                        "JobQueue": acjobqueue,
                        "JobDefinition": ac_job_definition,
                        "ContainerOverrides": {
                            "Command": ["export && landsat.sh"],
                            "Environment": [
                                {"Name": "INPUT_BUCKET", "Value.$": "$.bucket"},
                                {"Name": "PREFIX", "Value.$": "$.prefix"},
                                {"Name": "GRANULE", "Value.$": "$.scene"},
                                {
                                    "Name": "OUTPUT_BUCKET",
                                    "Value": intermediate_output_bucket,
                                },
                                {"Name": "LASRC_AUX_DIR", "Value": "/var/lasrc_aux"},
                                {"Name": "REPLACE_EXISTING", "Value": replace},
                            ],
                        },
                    },
                    "Catch": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "Next": "LogLandsatAcError",
                            "ResultPath": "$.jobinfo",
                        }
                    ],
                    "Next": "LogLandsatAc",
                },
                "LogLandsatAc": {
                    "Type": "Task",
                    "Resource": landsat_ac_logger,
                    "ResultPath": None,
                    "Next": "ProcessMGRSGrid",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": lambda_interval,
                            "MaxAttempts": lambda_max_attempts,
                            "BackoffRate": 2,
                        }
                    ],
                },
                "ProcessMGRSGrid": {
                    "Type": "Map",
                    "ItemsPath": "$.mgrsvalues.mgrs",
                    "Parameters": {
                        "MGRS.$": "$$.Map.Item.Value",
                        "path.$": "$.path",
                        "date.$": "$.date",
                    },
                    "MaxConcurrency": 0,
                    "Iterator": {
                        "StartAt": "GetPathRowValues",
                        "States": {
                            "GetPathRowValues": {
                                "Type": "Task",
                                "Resource": pr2mgrs,
                                "ResultPath": "$.mgrs_metadata",
                                "Next": "CheckPathRowStatus",
                            },
                            "CheckPathRowStatus": {
                                "Type": "Task",
                                "Resource": landsat_pathrow_status,
                                "ResultPath": "$.ready_for_tiling",
                                "Next": "ReadyForTiling",
                            },
                            "ReadyForTiling": {
                                "Type": "Choice",
                                "Choices": [
                                    {
                                        "Variable": "$.ready_for_tiling",
                                        "BooleanEquals": True,
                                        "Next": "RunLandsatTile",
                                    }
                                ],
                                "Default": "SuccessState",
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
                                            {"Name": "PATHROW_LIST", "Value.$": "$.mgrs_metadata.pathrows_string"},
                                            {"Name": "INPUT_BUCKET", "Value": intermediate_output_bucket},
                                            {"Name": "OUTPUT_BUCKET", "Value": outputbucket},
                                            {
                                                "Name": "GCC_ROLE_ARN",
                                                "Value": outputbucket_role_arn,
                                            },
                                            {"Name": "DATE", "Value.$": "$.date"},
                                            {"Name": "MGRS", "Value.$": "$.MGRS"},
                                            {"Name": "LANDSAT_PATH", "Value.$": "$.path"},
                                            {"Name": "MGRS_ULX", "Value.$": "$.mgrs_metadata.mgrs_ulx"},
                                            {"Name": "MGRS_ULY", "Value.$": "$.mgrs_metadata.mgrs_uly"},
                                            {"Name": "GIBS_OUTPUT_BUCKET", "Value": gibs_outputbucket},
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
                                "Retry": [
                                    {
                                        "ErrorEquals": ["States.ALL"],
                                        "IntervalSeconds": lambda_interval,
                                        "MaxAttempts": lambda_max_attempts,
                                        "BackoffRate": lambda_backoff_rate,
                                    }
                                ],
                            },
                            "SuccessState": {"Type": "Succeed"},
                        },
                    },
                    "Next": "CheckExitCodes",
                },
                "CheckExitCodes": {
                    "Type": "Task",
                    "Resource": check_landsat_tiling_exit_code,
                    "Next": "HadTilingFailure",
                },
                "HadTilingFailure": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$",
                            "BooleanEquals": True,
                            "Next": "Done",
                        },
                        {
                            "Variable": "$",
                            "BooleanEquals": False,
                            "Next": "Error",
                        }
                    ],
                    "Default": "Done",
                },
                "LogLandsatAcError": {
                    "Type": "Task",
                    "Resource": landsat_ac_logger,
                    "Next": "CheckAcExitCode",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": lambda_interval,
                            "MaxAttempts": lambda_max_attempts,
                            "BackoffRate": lambda_backoff_rate,
                        }
                    ],
                },
                "CheckAcExitCode": {
                    "Type": "Task",
                    "Resource": check_landsat_ac_exit_code,
                    "Next": "HadAcFailure",
                },
                "HadAcFailure": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$",
                            "BooleanEquals": True,
                            "Next": "Done",
                        },
                        {
                            "Variable": "$",
                            "BooleanEquals": False,
                            "Next": "Error",
                        }
                    ],
                    "Default": "Done",
                },
                "LogError": {
                    "Type": "Task",
                    "Resource": lambda_logger,
                    "ResultPath": "$",
                    "Next": "Error",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": lambda_interval,
                            "MaxAttempts": lambda_max_attempts,
                            "BackoffRate": lambda_backoff_rate,
                        }
                    ],
                },
                "Done": {"Type": "Succeed"},
                "Error": {"Type": "Fail"},
            }
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
