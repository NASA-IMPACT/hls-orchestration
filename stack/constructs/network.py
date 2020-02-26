from aws_cdk import core
from aws_cdk import aws_ec2


class Network(core.Construct):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.vpc = aws_ec2.CfnVPC(
            self,
            "Vpc",
            cidr_block="10.0.0.0/16",
            enable_dns_hostnames=True,
            enable_dns_support=True,
        )

        self.internet_gateway = aws_ec2.CfnInternetGateway(self, "InternetGateway")

        self.gateway_attachment = aws_ec2.CfnVPCGatewayAttachment(
            self,
            "GatewayAttachment",
            vpc_id=self.vpc.ref,
            internet_gateway_id=self.internet_gateway.ref,
        )

        self.public_route_table = aws_ec2.CfnRouteTable(
            self, "public-route-table", vpc_id=self.vpc.ref
        )

        self.public_route = aws_ec2.CfnRoute(
            self,
            "PublicRoute",
            route_table_id=self.public_route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=self.internet_gateway.ref,
        )

        self.public_subnets = []
        self.public_subnet_route_associations = []
        for s in range(1, 3):
            subnet = aws_ec2.CfnSubnet(
                self,
                f"PublicSubnet{s}",
                vpc_id=self.vpc.ref,
                cidr_block=f"10.0.{s-1}.0/24",
                availability_zone=core.Fn.select(s - 1, core.Fn.get_azs()),
                map_public_ip_on_launch=True,
            )
            route_table_association = aws_ec2.CfnSubnetRouteTableAssociation(
                self,
                f"PublicSubnet{s}RouteTableAssociation",
                subnet_id=subnet.ref,
                route_table_id=self.public_route_table.ref,
            )
            self.public_subnets.append(subnet)
            self.public_subnet_route_associations.append(route_table_association)
