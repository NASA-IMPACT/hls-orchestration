import json

from aws_cdk import aws_iam, aws_stepfunctions, core
from hlsconstructs.batch_step_function import BatchStepFunction
from hlsconstructs.lambdafunc import Lambda
from hlsconstructs.state_machine_step_function import StateMachineStepFunction


class SentinelErrorsStepFunction(BatchStepFunction, StateMachineStepFunction):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        outputbucket: str,
        outputbucket_role_arn: str,
        inputbucket: str,
        sentinel_job_definition: str,
        jobqueue: str,
        update_sentinel_failure: Lambda,
        get_random_wait: Lambda,
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
            "Comment": "Sentinel Errors Step Function",
            "StartAt": "ProcessErrors",
            "States": {
                "ProcessErrors": {
                    "Type": "Map",
                    "ItemsPath": "$.errors",
                    "MaxConcurrency": 400,
                    "Iterator": {
                        "StartAt": "GetRandomWait",
                        "States": {
                            "GetRandomWait": {
                                "Type": "Task",
                                "Resource": get_random_wait.function.function_arn,
                                "ResultPath": "$.wait_time",
                                "Next": "WaitForProcessSentinel",
                            },
                            "WaitForProcessSentinel": {
                                "Type": "Wait",
                                "SecondsPath": "$.wait_time",
                                "Next": "ProcessSentinel"
                            },
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
                                            {"Name": "INPUT_BUCKET", "Value": inputbucket},
                                            {"Name": "LASRC_AUX_DIR", "Value": "/var/lasrc_aux"},
                                            {
                                                "Name": "GCC_ROLE_ARN",
                                                "Value": outputbucket_role_arn,
                                            },
                                            {
                                                "Name": "REPLACE_EXISTING",
                                                "Value": "replace",
                                            },
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
                                        "Next": "UpdateSentinelFailure",
                                        "ResultPath": "$.jobinfo",
                                    }
                                ],
                                "Next": "UpdateSentinelFailure",
                            },
                            "UpdateSentinelFailure": {
                                "Type": "Task",
                                "Resource": update_sentinel_failure.function.function_arn,
                                "Next": "SuccessState",
                                "Retry": [retry],
                            },
                            "SuccessState": {
                                "Type": "Succeed"
                            },
                        }
                    },
                    "Next": "Done"
                },
                "Done": {"Type": "Succeed"}
            }
        }

        self.state_machine = aws_stepfunctions.CfnStateMachine(
            self,
            "SentineErrorsStateMachine",
            definition_string=json.dumps(state_definition),
            role_arn=self.steps_role.role_arn,
        )

        self.addLambdasToRole(locals())
