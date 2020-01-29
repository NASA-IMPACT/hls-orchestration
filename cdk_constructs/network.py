from aws_cdk import core
from aws_cdk.aws_ec2 import (
    Vpc,
    NatProvider,
    SubnetConfiguration,
    SubnetType,
    SecurityGroup
)


class Network(core.Construct):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Subnet configurations for a public and private tier
        public_subnet = SubnetConfiguration(
            name=f"public-subnet",
            subnet_type=SubnetType.PUBLIC,
            cidr_mask=24,
        )

        private_subnet = SubnetConfiguration(
            name=f"private-subnet",
            subnet_type=SubnetType.PRIVATE,
            cidr_mask=24,
        )

        vpc = Vpc(
            self,
            f"vpc",
            cidr="10.0.0.0/16",
            enable_dns_hostnames=True,
            enable_dns_support=True,
            max_azs=2,
            nat_gateway_provider=NatProvider.gateway(),
            nat_gateways=1,
            subnet_configuration=[public_subnet, private_subnet],
        )

        security_group = SecurityGroup(self, f"security_group", vpc=vpc)

        self.security_group = security_group
        self.vpc = vpc

        core.CfnOutput(self, "vpcid", value=vpc.vpc_id)
        core.CfnOutput(
            self, "security_group_id", value=security_group.security_group_id
        )
