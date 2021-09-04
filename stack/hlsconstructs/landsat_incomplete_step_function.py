from aws_cdk import (
    aws_stepfunctions,
    aws_iam,
    core,
)
from hlsconstructs.lambdafunc import Lambda
import json


class LandsatIncompleteStepFunction(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        landsat_mgrs_step_function_arn: str,
        get_random_wait: Lambda,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        state_definition = {
            "Comment": "Landsat Incomplete Step Function",
            "StartAt": "ProcessIncompletes",
            "States": {
                "ProcessIncompletes": {
                    "Type": "Map",
                    "ItemsPath": "$.incompletes",
                    "MaxConcurrency": 100,
                    "Iterator": {
                        "StartAt": "GetRandomWait",
                        "States": {
                            "GetRandomWait": {
                                "Type": "Task",
                                "Resource": get_random_wait.function.function_arn,
                                "ResultPath": "$.wait_time",
                                "Next": "Wait",
                            },
                            "Wait": {
                                "Type": "Wait",
                                "SecondsPath": "$.wait_time",
                                "Next": "ProcessMGRSGrids"
                            },
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
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "CloudWatchEventsFullAccess"
                ),
            ],
        )

        self.state_machine = aws_stepfunctions.CfnStateMachine(
            self,
            "LandsatIncompletesStateMachine",
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
                resources=["*",],
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

        # Allow the step function role to invoke all its Lambdas.

        arguments = locals()
        for key in arguments:
            arg = arguments[key]
            if type(arg) == Lambda:
                self.steps_role.add_to_policy(
                    arg.invoke_policy_statement
                )
