import json

from aws_cdk import aws_iam, aws_stepfunctions, core
from hlsconstructs.lambdafunc import Lambda
from hlsconstructs.state_machine_step_function import StateMachineStepFunction


class LandsatIncompleteStepFunction(StateMachineStepFunction):
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
                                "Next": "ProcessMGRSGrids",
                            },
                            "ProcessMGRSGrids": {
                                "Type": "Task",
                                "Resource": "arn:aws:states:::states:startExecution.sync",
                                "Parameters": {
                                    "StateMachineArn": landsat_mgrs_step_function_arn,
                                    "Input": {
                                        "NeedCallback": False,
                                        "AWS_STEP_FUNCTIONS_STARTED_BY_EXECUTION_ID.$": "$$.Execution.Id",
                                        "MGRS.$": "$.MGRS",
                                        "path.$": "$.path",
                                        "date.$": "$.date",
                                    },
                                },
                                "Catch": [
                                    {
                                        "ErrorEquals": ["States.ALL"],
                                        "Next": "SuccessState",
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
            },
        }

        self.state_machine = aws_stepfunctions.CfnStateMachine(
            self,
            "LandsatIncompletesStateMachine",
            definition_string=json.dumps(state_definition),
            role_arn=self.steps_role.role_arn,
        )

        self.steps_role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[landsat_mgrs_step_function_arn],
                actions=[
                    "states:StartExecution",
                ],
            )
        )

        self.add_lambdas_to_role(locals())
