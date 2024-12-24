import json
from typing import Union

from aws_cdk import aws_iam, aws_stepfunctions
from constructs import Construct
from hlsconstructs.batch_step_function import BatchStepFunction
from hlsconstructs.lambdafunc import Lambda
from hlsconstructs.state_machine_step_function import StateMachineStepFunction


class L30_Reprocess_StepFunction(BatchStepFunction, StateMachineStepFunction):
    def __init__(
        self,
        scope: Construct,
        id: str,
        laads_available: Lambda,
        intermediate_output_bucket: str,
        ac_job_definition: str,
        acjobqueue: str,
        pr2mgrs: Lambda,
        get_landsat_scenes: Lambda,
        check_landsat_tiling_exit_code: Lambda,
        check_landsat_ac_exit_code: Lambda,
        get_random_wait: Lambda,
        replace_existing: bool,
        tile_job_definition: str,
        tilejobqueue: str,
        gibs_outputbucket: str,
        debug_bucket: Union[bool, str] = False,
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
            "Comment": "L30 Reprocessing",
            "StartAt": "GetPathrows",
            "States": {
                "GetPathrows": {
                    "Type": "Task",
                    "Resource": pr2mgrs.function.function_arn,
                    "ResultPath": "$.pathrows",
                    "Next": "CheckLaads",
                    "Retry": [retry],
                },
                "CheckLaads": {
                    "Type": "Task",
                    "Resource": laads_available.function.function_arn,
                    "Parameters": {"date.$": "$.date"},
                    "ResultPath": "$.laads_available",
                    "Next": "LaadsAvailable",
                    "Retry": [retry],
                },
                "LaadsAvailable": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.laads_available.available",
                            "BooleanEquals": True,
                            "Next": "GetRandomWait",
                        }
                    ],
                    "Default": "Wait",
                },
                "Wait": {"Type": "Wait", "Seconds": 3600, "Next": "CheckLaads"},
                "GetLandsatScenes": {
                    "Type": "Task",
                    "Resource": get_landsat_scenes.function.function_arn,
                    "Parameters": {"date.$": "pathrows.$"},
                    "ResultPath": "$.scenes",
                    "Next": "LaadsAvailable",
                    "Retry": [retry],
                },
                "ProcessLandsatScenes": {
                    "Type": "Map",
                    "ItemsPath": "$.scenes.scenes",
                    "Parameters": {
                        "scene.$": "$$.Map.Item.Value",
                        "path.$": "$.path",
                        "date.$": "$.date",
                        "bucket.$": "$.scenes.bucket",
                        "prefix.$": "$.scenes.prefix",
                    },
                    "MaxConcurrency": 0,
                    "Iterator": {
                        "StartAt": "RunLandsatAc",
                        "States": {
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
                                                "Value.$": "$.bucket",
                                            },
                                            {"Name": "PREFIX", "Value.$": "$.prefix"},
                                            {"Name": "GRANULE", "Value.$": "$.scene"},
                                            {
                                                "Name": "OUTPUT_BUCKET",
                                                "Value": intermediate_output_bucket,
                                            },
                                            {
                                                "Name": "LASRC_AUX_DIR",
                                                "Value": "/var/lasrc_aux",
                                            },
                                            {
                                                "Name": "VIIRS_AUX_STARTING_DATE",
                                                "Value": "20210101",
                                            },
                                            {
                                                "Name": "REPLACE_EXISTING",
                                                "Value": replace,
                                            },
                                            {"Name": "OMP_NUM_THREADS", "Value": "2"},
                                        ],
                                    },
                                    "Catch": [
                                        {
                                            "ErrorEquals": ["States.ALL"],
                                            "Next": "CheckAcExitCode",
                                            "ResultPath": "$.jobinfo",
                                        }
                                    ],
                                    "Next": "CheckAcExitCode",
                                },
                                "CheckAcExitCode": {
                                    "Type": "Task",
                                    "Resource": check_landsat_ac_exit_code.function.function_arn,
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
                                        },
                                    ],
                                    "Default": "Done",
                                },
                                "Done": {"Type": "Succeed"},
                                "Error": {"Type": "Fail"},
                            }
                        },
                    },
                },
            },
        }
        if debug_bucket:
            state_definition["States"]["RunLandsatAc"]["Parameters"][
                "ContainerOverrides"
            ]["Environment"].append({"Name": "DEBUG_BUCKET", "Value": debug_bucket})
        self.state_machine = aws_stepfunctions.CfnStateMachine(
            self,
            "LandsatStateMachine",
            definition_string=json.dumps(state_definition),
            role_arn=self.steps_role.role_arn,
        )

        self.add_lambdas_to_role(locals())
