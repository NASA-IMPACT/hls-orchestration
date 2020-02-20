from aws_cdk import aws_rds, aws_ec2, core, aws_iam
from constructs.network import Network


class Rds(core.Construct):
    def __init__(
        self, scope: core.Construct, id: str, network: Network, **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.database = aws_rds.DatabaseCluster(
            self, 
            "Rds",
            default_database_name="hls",
            engine_version="10.7",
            engine=aws_rds.DatabaseInstanceEngine.AURORA_POSTGRESQL,
            master_user=aws_rds.Login(
                username='admin',
            ),
            instance_props=aws_rds.InstanceProps(
                instance_type=aws_ec2.InstanceType('db.t3.small'),
                vpc=network.vpc
            ),
            instances=1,
        )
        
        # enable_http_endpoint is not made available on DatabaseCluster
        # so we need to add it onto the child CfnDBCluster manually
        cfndb = self.database.node.default_child
        cfndb.enable_http_endpoint=True

        self.secrets_policy_statement = aws_iam.PolicyStatement(
            resources=["arn:aws:secretsmanager:*:*:secret:rds-db-credentials/*"],
            actions=[
                "secretsmanager:GetSecretValue",
                "secretsmanager:PutResourcePolicy",
                "secretsmanager:PutSecretValue",
                "secretsmanager:DeleteSecret",
                "secretsmanager:DescribeSecret",
                "secretsmanager:TagResource"
            ],
        )

        self.rds_policy_statement = aws_iam.PolicyStatement(
            resources=["*"],
            actions=[
                "secretsmanager:CreateSecret",
                "secretsmanager:ListSecrets",
                "secretsmanager:GetRandomPassword",
                "tag:GetResources",
                "rds-data:BatchExecuteStatement",
                "rds-data:BeginTransaction",
                "rds-data:CommitTransaction",
                "rds-data:ExecuteStatement",
                "rds-data:RollbackTransaction"
            ],
        )
