from aws_cdk import aws_efs, aws_ec2, core
from constructs.network import Network


class Efs(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        network: Network,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.mount_target_security_group = aws_ec2.CfnSecurityGroup(
            self,
            "MountTargetSecurityGroup",
            vpc_id=network.vpc.ref,
            group_description="Security Group for EFS Mount Target",
            security_group_ingress=[
                aws_ec2.CfnSecurityGroup.IngressProperty(
                    ip_protocol="tcp",
                    from_port=2049,
                    to_port=2049,
                    cidr_ip="0.0.0.0/0",
                )
            ],
        )

        self.filesystem = aws_efs.CfnFileSystem(
            self, f"Efs", encrypted=False, lifecycle_policies=None
        )

        mount_targets = []
        for subnet in network.public_subnets:
            mount_target = aws_efs.CfnMountTarget(
                self,
                f"MountTarget{len(mount_targets)+1}",
                file_system_id=self.filesystem.ref,
                security_groups=[self.mount_target_security_group.ref],
                subnet_id=subnet.ref,
            )
            mount_targets.append(mount_target)

        core.CfnOutput(self, "filesystem", value=self.filesystem.ref)
