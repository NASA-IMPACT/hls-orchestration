import json

from aws_cdk import aws_iam, aws_stepfunctions, core
from hlsconstructs.state_machine_step_function import StateMachineStepFunction


class LandsatACErrorsStepFunction(StateMachineStepFunction):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        landsat_step_function_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        state_definition = {
            "Comment": "Landsat AC Errors Step Function",
            "StartAt": "ProcessErrors",
            "States": {
                "ProcessErrors": {
                    "Type": "Map",
                    "ItemsPath": "$.errors",
                    "MaxConcurrency": 100,
                    "Iterator": {
                        "StartAt": "ProcessError",
                        "States": {
                            "ProcessError": {
                                "Type":"Task",
                                "Resource":"arn:aws:states:::states:startExecution.sync",
                                "Parameters":{
                                    "StateMachineArn": landsat_step_function_arn,
                                    "Input":{
                                        "NeedCallback": False,
                                        "AWS_STEP_FUNCTIONS_STARTED_BY_EXECUTION_ID.$": "$$.Execution.Id",
                                        "sensor.$": "$.sensor",
                                        "satellite.$": "$.satellite",
                                        "processingCorrectionLevel.$": "$.processingCorrectionLevel",
                                        "path.$": "$.path",
                                        "row.$": "$.row",
                                        "acquisitionYear.$": "$.acquisitionYear",
                                        "acquisitionMonth.$": "$.acquisitionMonth",
                                        "acquisitionDay.$": "$.acquisitionDay",
                                        "processingYear.$": "$.processingYear",
                                        "processingMonth.$": "$.processingMonth",
                                        "processingDay.$": "$.processingDay",
                                        "collectionNumber.$": "$.collectionNumber",
                                        "collectionCategory.$": "$.collectionCategory",
                                        "scene.$": "$.scene",
                                        "date.$": "$.date",
                                        "scheme.$": "$.scheme",
                                        "bucket.$": "$.bucket",
                                        "prefix.$": "$.prefix"
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
                "Done": {"Type": "Succeed"}
            }
        }

        self.state_machine = aws_stepfunctions.CfnStateMachine(
            self,
            "LandsatACErrorsStateMachine",
            definition_string=json.dumps(state_definition),
            role_arn=self.steps_role.role_arn,
        )

        self.steps_role.add_to_policy(
            aws_iam.PolicyStatement(
                resources=[landsat_step_function_arn],
                actions=[
                    "states:StartExecution",
                ]
            )
        )
