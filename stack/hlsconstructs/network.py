from aws_cdk import core
from aws_cdk import aws_ec2


class Network(core.Construct):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

#       vpcid = self.node.try_get_context("vpc-0e7684c7341e1e0db")
        vpcid ="vpc-07a334625775da83c"
#       stack vpcid ="vpc-0e7684c7341e1e0db"
        self.vpc = aws_ec2.Vpc.from_lookup(self, "VPC",vpc_id=vpcid)
        print(self.vpc.public_subnets)
#               public_subnets = vpc.select_subnets(subnetType=ec2.SubnetType.PUBLIC)
#               cdk.CfnOutput(self, "publicsubnets",
#                     value=public_subnets.subnet_ids.to_string())
                 #vpc_id = "vpc-0e7684c7341e1e0db"

        self.public_subnets = self.vpc.public_subnets
