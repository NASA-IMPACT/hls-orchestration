from aws_cdk import aws_ec2, core


class Network(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        vpcid=None,
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)
        if vpcid:
            self.vpc = aws_ec2.Vpc.from_lookup(self, "Vpc", vpc_id=vpcid)
        else:
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
                ],
                max_azs=2,
            )
        self.public_subnets = self.vpc.public_subnets
