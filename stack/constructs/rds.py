import os
from aws_cdk import aws_rds, aws_ec2, core, aws_iam, aws_secretsmanager
from constructs.network import Network


class Rds(core.Construct):
    def __init__(
        self, scope: core.Construct, id: str, network: Network, **kwargs,
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
                    ip_protocol="-1", cidr_ip="0.0.0.0/0",
                )
            ],
            security_group_egress=[
                aws_ec2.CfnSecurityGroup.EgressProperty(
                    ip_protocol="-1", cidr_ip="0.0.0.0/0",
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

        self.database = aws_rds.CfnDBCluster(
            self,
            "RdsCluster",
            engine="aurora-postgresql",
            engine_mode="serverless",
            engine_version="10.7",
            database_name="hls",
            db_subnet_group_name=self.subnet_group.ref,
            enable_http_endpoint=True,
            db_cluster_identifier=f"rds-{os.getenv('HLS_STACKNAME')}",
            master_username=core.Fn.join(
                "",
                [
                    "{{resolve:secretsmanager:",
                    self.secret.secret_arn,
                    ":SecretString:username}}",
                ],
            ),
            master_user_password=core.Fn.join(
                "",
                [
                    "{{resolve:secretsmanager:",
                    self.secret.secret_arn,
                    ":SecretString:password}}",
                ],
            ),
            vpc_security_group_ids=[self.security_group.ref],
        )

        region = core.Aws.REGION
        accountid = core.Aws.ACCOUNT_ID
        self.arn = core.Fn.join(
            ":", ["arn:aws:rds", region, accountid, "cluster", self.database.ref]
        )

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
