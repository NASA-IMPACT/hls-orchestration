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
        check_twin_granule: str,
        laads_available_function: str,
        outputbucket: str,
        outputbucket_role_arn: str,
        inputbucket: str,
        sentinel_job_definition: str,
        jobqueue: str,
        lambda_logger: str,
        sentinel_logger: str,
        check_exit_code: str,
        replace_existing: bool,
        gibs_intermediate_output_bucket: str,
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
        sentinel_state_definition = {
            "Comment": "Sentinel Step Function",
            "StartAt": "CheckGranule",
            "States": {
                "CheckGranule": {
                    "Type": "Task",
                    "Resource": check_twin_granule,
                    "ResultPath": "$",
                    "Next": "CheckLaads",
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
                "CheckLaads": {
                    "Type": "Task",
                    "Resource": laads_available_function,
                    "ResultPath": "$",
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
                                {"Name": "INPUT_BUCKET", "Value": inputbucket},
                                {"Name": "LASRC_AUX_DIR", "Value": "/var/lasrc_aux"},
                                {
                                    "Name": "GCC_ROLE_ARN",
                                    "Value": outputbucket_role_arn,
                                },
                                {"Name": "REPLACE_EXISTING", "Value": replace},
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
                            "Next": "LogSentinel",
                            "ResultPath": "$.jobinfo",
                        }
                    ],
                    "Next": "LogSentinel",
                },
                "LogSentinel": {
                    "Type": "Task",
                    "Resource": sentinel_logger,
                    "Next": "CheckSentinelExitCode",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": lambda_interval,
                            "MaxAttempts": lambda_max_attempts,
                            "BackoffRate": lambda_backoff_rate,
                        }
                    ],
                },
                "CheckSentinelExitCode": {
                    "Type": "Task",
                    "Resource": check_exit_code,
                    "Next": "HadSentinelFailure",
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
