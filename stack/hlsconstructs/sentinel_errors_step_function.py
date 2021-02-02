from aws_cdk import (
    aws_stepfunctions,
    aws_iam,
    core,
)
import json


class SentinelErrorsStepFunction(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        outputbucket: str,
        outputbucket_role_arn: str,
        inputbucket: str,
        sentinel_job_definition: str,
        jobqueue: str,
        lambda_logger: str,
        update_sentinel_failure: str,
        get_random_wait: str,
        gibs_intermediate_output_bucket: str,
        gibs_outputbucket: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        lambda_interval = 10
        lambda_max_attempts = 3
        lambda_backoff_rate = 2

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
                                "Resource": get_random_wait,
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
                                                "Name": "GIBS_INTERMEDIATE_BUCKET",
                                                "Value": gibs_intermediate_output_bucket,
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
                                        "Next": "UpdatetSentinelFailure",
                                        "ResultPath": "$.jobinfo",
                                    }
                                ],
                                "Next": "UpdatetSentinelFailure",
                            },
                            "UpdatetSentinelFailure": {
                                "Type": "Task",
                                "Resource": update_sentinel_failure,
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

        self.steps_role = aws_iam.Role(
            self,
            "SentinelErrorsStepsRole",
            assumed_by=aws_iam.ServicePrincipal("states.amazonaws.com"),
        )
        self.state_machine = aws_stepfunctions.CfnStateMachine(
            self,
            "SentineErrorsStateMachine",
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
