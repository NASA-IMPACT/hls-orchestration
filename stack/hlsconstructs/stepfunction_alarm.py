from aws_cdk import core, aws_cloudwatch, aws_cloudwatch_actions, aws_sns


class StepFunctionAlarm(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        state_machine: str,
        root_name: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.step_function_metric = aws_cloudwatch.Metric(
            namespace="AWS/States",
            metric_name=f"{root_name}StepFunctionFailures",
            period=core.Duration.minutes(20),
            statistic="avg",
            dimensions={
                "StateMachineArn": state_machine
            }
        )

        self.step_function_alarm = aws_cloudwatch.Alarm(
            self,
            f"{root_name}CWStepFunctionAlarm",
            metric=self.step_function_metric,
            threshold=0.2,
            evaluation_periods=1,
        )

        self.step_function_sns = aws_sns.Topic(
            self,
            f"{root_name}StepFunctionFailuresSNS"
        )

        self.step_function_alarm.add_alarm_action(
            aws_cloudwatch_actions.SnsAction(self.step_function_sns)
        )
