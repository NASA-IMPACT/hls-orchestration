import os

from aws_cdk import aws_batch, aws_ec2, aws_ecs, aws_efs, aws_iam, aws_ssm, core
from hlsconstructs.network import Network

dirname = os.path.dirname(os.path.realpath(__file__))


class Batch(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        network: Network,
        instance_types: list,
        maxv_cpus: int,
        ssh_keyname: str,
        efs: aws_efs.CfnFileSystem = None,
        use_cw: bool = True,
        image_id=None,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.ecs_host_security_group = aws_ec2.CfnSecurityGroup(
            self,
            "EcsHostSecurityGroup",
            vpc_id=network.vpc.vpc_id,
            group_description="Security Group for ECS Host",
        )

        self.ecs_security_group_ingress_from_self = aws_ec2.CfnSecurityGroupIngress(
            self,
            "EcsSecurityGroupIngressFromSelf",
            group_id=self.ecs_host_security_group.ref,
            ip_protocol="-1",
            source_security_group_id=self.ecs_host_security_group.ref,
        )

        batch_service_role = aws_iam.Role(
            self,
            "BatchServiceRole",
            assumed_by=aws_iam.ServicePrincipal("batch.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSBatchServiceRole"
                ),
            ],
        )

        efs_policy_statement = aws_iam.PolicyStatement(
            resources=["*"],
            actions=[
                "elasticfilesystem:DescribeMountTargets",
                "elasticfilesystem:DescribeFileSystems",
            ],
        )

        efs_policy_document = aws_iam.PolicyDocument(statements=[efs_policy_statement])

        self.ecs_instance_role = aws_iam.Role(
            self,
            "EcsInstanceRole",
            assumed_by=aws_iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonEC2ContainerServiceforEC2Role"
                ),
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "CloudWatchAgentServerPolicy"
                ),
            ],
            inline_policies={"efspolicy": efs_policy_document},
        )

        ecs_instance_profile = aws_iam.CfnInstanceProfile(
            self,
            "EcsInstanceProfile",
            roles=[self.ecs_instance_role.role_name],
        )

        self.ec2_spot_fleet_role = aws_iam.Role(
            self,
            "AmazonEC2SpotFleetRole",
            assumed_by=aws_iam.ServicePrincipal("spotfleet.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonEC2SpotFleetTaggingRole"
                ),
            ],
        )
        if use_cw:
            cloudwatch_ssm_param = f"BatchCloudwatchAgentConfig{self.node.unique_id}"
            cloudwatch_config_string = open(
                os.path.join(dirname, "cloudwatchconfig.json"), "r"
            ).read()
            cloudwatch_config_param = aws_ssm.StringParameter(
                self,
                "CloudWatchAgentConfigParam",
                description="Configruation of Cloudwatch Agent for Amazon Linux 2",
                parameter_name=cloudwatch_ssm_param,
                string_value=cloudwatch_config_string,
            )
            # Grant ssm:GetParameters to ECS Instnace role.
            cloudwatch_config_param.grant_read(self.ecs_instance_role)

            userdata_file = open(os.path.join(dirname, "userdata.txt"), "rb").read()
            user_data = aws_ec2.UserData.for_linux()
            user_data_string = str(userdata_file, "utf-8").format(
                efs.ref, cloudwatch_ssm_param
            )
        else:
            userdata_file = open(
                os.path.join(dirname, "userdata_no_cw.txt"), "rb"
            ).read()
            user_data = aws_ec2.UserData.for_linux()
            user_data_string = str(userdata_file, "utf-8").format(efs.ref)

        user_data.add_commands(user_data_string)
        user_data_str = "\n".join(user_data.render().split("\n")[1:])

        launch_template_data = aws_ec2.CfnLaunchTemplate.LaunchTemplateDataProperty(
            user_data=core.Fn.base64(user_data_str),
            key_name=ssh_keyname,
        )

        launch_template = aws_ec2.CfnLaunchTemplate(
            self,
            "LaunchTemplate",
            launch_template_data=launch_template_data,
        )

        launch_template_props = (
            aws_batch.CfnComputeEnvironment.LaunchTemplateSpecificationProperty(
                launch_template_id=launch_template.ref,
                version=launch_template.attr_latest_version_number,
            )
        )
        if image_id is None:
            image_id = (
                aws_ecs.EcsOptimizedImage.amazon_linux2().get_image(self).image_id
            )

        compute_resources = aws_batch.CfnComputeEnvironment.ComputeResourcesProperty(
            allocation_strategy="BEST_FIT_PROGRESSIVE",
            desiredv_cpus=0,
            image_id=image_id,
            instance_role=ecs_instance_profile.ref,
            instance_types=instance_types,
            launch_template=launch_template_props,
            maxv_cpus=maxv_cpus,
            minv_cpus=0,
            security_group_ids=[self.ecs_host_security_group.ref],
            subnets=[s.subnet_id for s in network.public_subnets],
            type="SPOT",
            spot_iam_fleet_role=self.ecs_host_security_group.ref,
        )

        compute_environment = aws_batch.CfnComputeEnvironment(
            self,
            "ComputeEnvironment",
            compute_resources=compute_resources,
            service_role=batch_service_role.role_arn,
            type="MANAGED",
        )

        sentinel_jobqueue = aws_batch.CfnJobQueue(
            self,
            "SentinelJobQueue",
            priority=6,
            compute_environment_order=[
                aws_batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
                    compute_environment=compute_environment.ref, order=1
                )
            ],
        )
        sentinel_historic_jobqueue = aws_batch.CfnJobQueue(
            self,
            "SentinelHistoricJobQueue",
            priority=3,
            compute_environment_order=[
                aws_batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
                    compute_environment=compute_environment.ref, order=1
                )
            ],
        )
        landsatac_jobqueue = aws_batch.CfnJobQueue(
            self,
            "LandsatAcJobQueue",
            priority=5,
            compute_environment_order=[
                aws_batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
                    compute_environment=compute_environment.ref, order=1
                )
            ],
        )
        landsatac_historic_jobqueue = aws_batch.CfnJobQueue(
            self,
            "LandsatHistoricAcJobQueue",
            priority=2,
            compute_environment_order=[
                aws_batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
                    compute_environment=compute_environment.ref, order=1
                )
            ],
        )
        landsattile_jobqueue = aws_batch.CfnJobQueue(
            self,
            "LandsatTileJobQueue",
            priority=4,
            compute_environment_order=[
                aws_batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
                    compute_environment=compute_environment.ref, order=1
                )
            ],
        )
        landsattile_historic_jobqueue = aws_batch.CfnJobQueue(
            self,
            "LandsatHistoricTileJobQueue",
            priority=1,
            compute_environment_order=[
                aws_batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
                    compute_environment=compute_environment.ref, order=1
                )
            ],
        )
        laads_jobqueue = aws_batch.CfnJobQueue(
            self,
            "LaadsJobQueue",
            priority=10,
            compute_environment_order=[
                aws_batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
                    compute_environment=compute_environment.ref, order=1
                )
            ],
        )

        self.compute_environment = compute_environment
        self.sentinel_jobqueue = sentinel_jobqueue
        self.sentinel_historic_jobqueue = sentinel_historic_jobqueue
        self.landsatac_jobqueue = landsatac_jobqueue
        self.landsatac_historic_jobqueue = landsatac_historic_jobqueue
        self.landsattile_jobqueue = landsattile_jobqueue
        self.landsattile_historic_jobqueue = landsattile_historic_jobqueue
        self.laads_jobqueue = laads_jobqueue
