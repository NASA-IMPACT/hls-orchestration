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
        acjobqueue: str,
        landsat_mgrs_logger: str,
        landsat_ac_logger: str,
        landsat_logger: str,
        landsat_pathrow_status: str,
        pr2mgrs: str,
        check_landsat_tiling_exit_code: str,
        check_landsat_ac_exit_code: str,
        get_random_wait: str,
        replace_existing: bool,
        gibs_outputbucket: str,
        landsat_mgrs_step_function_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        retry = {
            "ErrorEquals": ["States.ALL"],
            "IntervalSeconds": 10,
            "MaxAttempts": 3,
            "BackoffRate": 2,
        }

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
                    "Retry": [retry],
                },
                "MGRSExists": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.mgrsvalues.count",
                            "NumericGreaterThan": 0,
                            "Next": "LogLandsat",
                        },
                    ],
                    "Default": "Done",
                },
                "LogLandsat": {
                    "Type": "Task",
                    "Resource": landsat_logger,
                    "ResultPath": None,
                    "Next": "LogLandsatMGRS",
                    "Retry": [retry],
                },
                "LogLandsatMGRS": {
                    "Type": "Task",
                    "Resource": landsat_mgrs_logger,
                    "ResultPath": None,
                    "Next": "CheckLaads",
                    "Retry": [retry],
                },
                "CheckLaads": {
                    "Type": "Task",
                    "Resource": laads_available_function,
                    "Parameters": {"granule.$": "$.scene", "scene_meta.$": "$"},
                    "ResultPath": "$.taskresult",
                    "Next": "LaadsAvailable",
                    "Retry": [retry],
                },
                "LaadsAvailable": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.taskresult.available",
                            "BooleanEquals": True,
                            "Next": "GetRandomWait",
                        }
                    ],
                    "Default": "Wait",
                },
                "Wait": {
                    "Type": "Wait",
                    "Seconds": 3600,
                    "Next": "CheckLaads"
                },
                "GetRandomWait": {
                    "Type": "Task",
                    "Resource": get_random_wait,
                    "ResultPath": "$.wait_time",
                    "Next": "WaitForAc",
                },
                "WaitForAc": {
                    "Type": "Wait",
                    "SecondsPath": "$.wait_time",
                    "Next": "RunLandsatAc"
                },
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
                                {
                                    "Name": "INPUT_BUCKET",
                                    "Value.$": "$.bucket"
                                },
                                {
                                    "Name": "PREFIX",
                                    "Value.$": "$.prefix"
                                },
                                {
                                    "Name": "GRANULE",
                                    "Value.$": "$.scene"
                                },
                                {
                                    "Name": "OUTPUT_BUCKET",
                                    "Value": intermediate_output_bucket,
                                },
                                {
                                    "Name": "LASRC_AUX_DIR",
                                    "Value": "/var/lasrc_aux"
                                },
                                {
                                    "Name": "REPLACE_EXISTING",
                                    "Value": replace
                                },
                                {
                                    "Name": "OMP_NUM_THREADS",
                                    "Value": "2"
                                }
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
                    "Retry": [retry],
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
                        "StartAt": "ProcessMGRSGrids",
                        "States": {
                            "ProcessMGRSGrids": {
                                "Type":"Task",
                                "Resource":"arn:aws:states:::states:startExecution.sync",
                                "Parameters":{
                                    "StateMachineArn": landsat_mgrs_step_function_arn,
                                    "Input":{
                                        "NeedCallback": False,
                                        "AWS_STEP_FUNCTIONS_STARTED_BY_EXECUTION_ID.$": "$$.Execution.Id",
                                        "MGRS.$": "$.MGRS",
                                        "path.$": "$.path",
                                        "date.$": "$.date",
                                    },
                                },
                                "Retry":[
                                    {
                                        "ErrorEquals":[
                                            "StepFunctions.ExecutionLimitExceeded"
                                        ]
                                    }
                                ],
                                "Next": "SuccessState",
                            },
                            "SuccessState": {"Type": "Succeed"},
                        },
                    }, "Next": "CheckExitCodes",
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
                    "Retry": [retry],
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
                "Done": {"Type": "Succeed"},
                "Error": {"Type": "Fail"},
            }
        }

        self.steps_role = aws_iam.Role(
            self,
            "StepsRole",
            assumed_by=aws_iam.ServicePrincipal("states.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "CloudWatchEventsFullAccess"
                ),
            ],
        )

        self.state_machine = aws_stepfunctions.CfnStateMachine(
            self,
            "LandsatStateMachine",
            definition_string=json.dumps(state_definition),
            role_arn=self.steps_role.role_arn,
        )

        region = core.Aws.REGION
        accountid = core.Aws.ACCOUNT_ID

        self.steps_role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[
                    f"arn:aws:events:{region}:{accountid}:rule/"
                    "StepFunctionsGetEventsForStepFunctionsExecutionRule",
                ],
                actions=["events:PutTargets", "events:PutRule", "events:DescribeRule"],
            )
        )
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
        self.steps_role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[landsat_mgrs_step_function_arn],
                actions=[
                    "states:StartExecution",
                ]
            )
        )
        self.steps_role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=["*"],
                actions=[
                    "states:DescribeExecution",
                    "states:StopExecution"
                ]
            )
        )
