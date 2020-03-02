from aws_cdk import core
from aws_cdk import aws_ec2


class Network(core.Construct):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.vpc = aws_ec2.Vpc(
            self,
            "Vpc",
            cidr="10.1.0.0/16",
            enable_dns_hostnames=True,
            enable_dns_support=True,
            nat_gateways=0,
            subnet_configuration=[
                aws_ec2.SubnetConfiguration(
                    name="PublicSubnet1", subnet_type=aws_ec2.SubnetType.PUBLIC,
                ),
                # aws_ec2.SubnetConfiguration(
                #    name="PublicSubnet2", subnet_type=aws_ec2.SubnetType.PUBLIC,
                #),
            ],
            max_azs=2,
        )

        self.public_subnets = self.vpc.public_subnets

        self.az1_public_subnets = []
        az = None
        for s in self.vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PUBLIC).subnets:
            if az is None or az == s.availability_zone:
                az = s.availability_zone
                self.az1_public_subnets.append(s)
