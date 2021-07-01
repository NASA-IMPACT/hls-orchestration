from aws_cdk import (
    aws_stepfunctions,
    aws_iam,
    core,
)
import json


class LandsatACErrorsStepFunction(core.Construct):
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
                "Done": {"Type": "Succeed"}
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
            "LandsatACErrorsStateMachine",
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
                resources=[landsat_step_function_arn],
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
