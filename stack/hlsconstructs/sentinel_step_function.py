import json

from aws_cdk import aws_iam, aws_stepfunctions, core
from hlsconstructs.batch_step_function import BatchStepFunction
from hlsconstructs.lambdafunc import Lambda


class SentinelStepFunction(BatchStepFunction):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        check_twin_granule: Lambda,
        laads_available: Lambda,
        outputbucket: str,
        outputbucket_role_arn: str,
        inputbucket: str,
        sentinel_job_definition: str,
        jobqueue: str,
        sentinel_ac_logger: Lambda,
        sentinel_logger: Lambda,
        check_exit_code: Lambda,
        replace_existing: bool,
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

        if replace_existing:
            replace = "replace"
        else:
            replace = None
        sentinel_state_definition = {
            "Comment": "Sentinel Step Function",
            "StartAt": "CheckGranule",
            "States": {
                "CheckGranule": {
                    "Type": "Task",
                    "Resource": check_twin_granule.function.function_arn,
                    "ResultPath": "$",
                    "Next": "LogSentinel",
                    "Retry": [retry],
                },
                "LogSentinel": {
                    "Type": "Task",
                    "Resource": sentinel_logger.function.function_arn,
                    "ResultPath": "$",
                    "Next": "CheckLaads",
                    "Retry": [retry],
                },
                "CheckLaads": {
                    "Type": "Task",
                    "Resource": laads_available.function.function_arn,
                    "ResultPath": "$",
                    "Next": "LaadsAvailable",
                    "Retry": [retry],
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
                    "ResultPath": "$.jobinfo",
                    "Parameters": {
                        "JobName": "BatchJobNotification",
                        "JobQueue": jobqueue,
                        "JobDefinition": sentinel_job_definition,
                        "ContainerOverrides": {
                            "Command": ["export && sentinel.sh"],
                            "Environment": [
                                {"Name": "GRANULE_LIST", "Value.$": "$.granule"},
                                {"Name": "OUTPUT_BUCKET", "Value": outputbucket},
                                {"Name": "DEBUG_BUCKET", "Value": outputbucket},
                                {"Name": "INPUT_BUCKET", "Value": inputbucket},
                                {"Name": "LASRC_AUX_DIR", "Value": "/var/lasrc_aux"},
                                {
                                    "Name": "VIIRS_AUX_STARTING_DATE",
                                    "Value": "20210101",
                                },
                                {
                                    "Name": "GCC_ROLE_ARN",
                                    "Value": outputbucket_role_arn,
                                },
                                {"Name": "REPLACE_EXISTING", "Value": replace},
                                {
                                    "Name": "GIBS_OUTPUT_BUCKET",
                                    "Value": gibs_outputbucket,
                                },
                                {
                                    "Name": "OMP_NUM_THREADS",
                                    "Value": "2",
                                },
                            ],
                        },
                    },
                    "Catch": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "Next": "LogSentinelAC",
                            "ResultPath": "$.jobinfo",
                        }
                    ],
                    "Next": "LogSentinelAC",
                },
                "LogSentinelAC": {
                    "Type": "Task",
                    "Resource": sentinel_ac_logger.function.function_arn,
                    "Next": "CheckSentinelExitCode",
                    "Retry": [retry],
                },
                "CheckSentinelExitCode": {
                    "Type": "Task",
                    "Resource": check_exit_code.function.function_arn,
                    "Next": "HadSentinelFailure",
                    "Retry": [retry],
                },
                "HadSentinelFailure": {
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
            },
        }

        self.sentinel_state_machine = aws_stepfunctions.CfnStateMachine(
            self,
            "SentinelStateMachine",
            definition_string=json.dumps(sentinel_state_definition),
            role_arn=self.steps_role.role_arn,
        )

        self.add_lambdas_to_role(locals())
