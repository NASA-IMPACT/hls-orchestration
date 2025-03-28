import os

from aws_cdk import RemovalPolicy, SecretValue, aws_ec2, aws_iam, aws_rds, aws_secretsmanager
from constructs import Construct
from hlsconstructs.network import Network


class Rds(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        network: Network,
        min_capacity: int,
        max_capacity: int,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.subnet_group = aws_rds.CfnDBSubnetGroup(
            self,
            "RdsSubnetGroup",
            db_subnet_group_description="Rds Subnet Group",
            subnet_ids=network.vpc.select_subnets(one_per_az=True).subnet_ids,
        )

        self.security_group = aws_ec2.CfnSecurityGroup(
            self,
            "RdsSecurityGroup",
            vpc_id=network.vpc.vpc_id,
            group_description="Security Group for RDS",
            security_group_ingress=[
                aws_ec2.CfnSecurityGroup.IngressProperty(
                    ip_protocol="-1",
                    cidr_ip="0.0.0.0/0",
                )
            ],
            security_group_egress=[
                aws_ec2.CfnSecurityGroup.EgressProperty(
                    ip_protocol="-1",
                    cidr_ip="0.0.0.0/0",
                )
            ],
        )

        self.secret = aws_secretsmanager.Secret(
            self,
            "RdsSecret",
            description="Login for Rds",
            generate_secret_string=aws_secretsmanager.SecretStringGenerator(
                exclude_characters='"@/\\',
                generate_string_key="password",
                password_length=30,
                secret_string_template='{"username":"master"}',
            ),
        )

        self.database_name = "hls"
        self.database = aws_rds.DatabaseCluster(
            self,
            "RdsCluster",
            engine=aws_rds.DatabaseClusterEngine.aurora_postgres(
                version=aws_rds.AuroraPostgresEngineVersion.VER_13_12,
            ),
            default_database_name=self.database_name,
            enable_data_api=True,
            cluster_identifier=f"rds-{os.getenv('HLS_STACKNAME')}",
            serverless_v2_min_capacity=min_capacity,
            serverless_v2_max_capacity=max_capacity,
            writer=aws_rds.ClusterInstance.serverless_v2(
                id="instance-1",
                instance_identifier=f"rds-{os.getenv('HLS_STACKNAME')}-instance-1",
            ),
            credentials=aws_rds.Credentials.from_password(
                username="master",
                password=SecretValue.secrets_manager(secret_id=self.secret.secret_arn),
            ),
            vpc=network.vpc,
            subnet_group=self.subnet_group,
            security_groups=[self.security_group],
            removal_policy=RemovalPolicy.RETAIN,
        )

        self.arn = self.database.cluster_arn

        self.policy_statement = aws_iam.PolicyStatement(
            resources=[self.arn, self.secret.secret_arn],
            actions=[
                "secretsmanager:GetSecretValue",
                "secretsmanager:CreateSecret",
                "secretsmanager:ListSecrets",
                "secretsmanager:GetRandomPassword",
                "tag:GetResources",
                "rds-data:BatchExecuteStatement",
                "rds-data:BeginTransaction",
                "rds-data:CommitTransaction",
                "rds-data:ExecuteStatement",
                "rds-data:RollbackTransaction",
            ],
        )
