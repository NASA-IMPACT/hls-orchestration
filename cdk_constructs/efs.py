from aws_cdk import aws_efs as efs, core
from aws_cdk.aws_ec2 import IVpc, ISecurityGroup


class Efs(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        vpc: IVpc,
        security_group: ISecurityGroup,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        filesystem = efs.CfnFileSystem(
            self, f"efs", encrypted=False, lifecycle_policies=None
        )

        mount_targets = []
        for subnet in vpc.public_subnets:
            subnet_id = subnet.subnet_id
            mt = efs.CfnMountTarget(
                self,
                f"{len(mount_targets)}-mount-target",
                file_system_id=filesystem.ref,
                security_groups=[security_group.security_group_id],
                subnet_id=subnet_id,
            )
            mount_targets.append(mt)

        self.filesystem = filesystem
        self.mount_targets = mount_targets
        core.CfnOutput(self, "filesystem", value=filesystem.ref)
