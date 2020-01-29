from aws_cdk import (
    aws_batch,
    aws_ec2,
    aws_ecs,
    aws_efs,
    aws_iam,
    core,
)
import os

dirname = os.path.dirname(os.path.realpath(__file__))


class Batch(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        vpc: aws_ec2.Vpc = None,
        security_group: aws_ec2.SecurityGroup = None,
        efs: aws_efs.CfnFileSystem = None,
        efs_arn: str = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        batch_service_role = aws_iam.Role(
            self,
            f"batchservicerole",
            assumed_by=aws_iam.ServicePrincipal(
                "batch.amazonaws.com"
            ),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSBatchServiceRole"
                )
            ],
        )

        efs_policy_statement = aws_iam.PolicyStatement(
            resources=[efs_arn],
            actions=[
                "elasticfilesystem:DescribeMountTargets",
                "elasticfilesystem:DescribeFileSystems",
            ],
        )

        efs_policy_document = aws_iam.PolicyDocument(
            statements=[efs_policy_statement]
        )

        ecs_instance_role = aws_iam.Role(
            self,
            f"ecsinstancerole",
            assumed_by=aws_iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonEC2ContainerServiceforEC2Role"
                )
            ],
            inline_policies=[efs_policy_document],
        )

        ecs_instance_profile = aws_iam.CfnInstanceProfile(
            self,
            f"ecsinstanceprofile",
            roles=[ecs_instance_role.role_name],
        )

        userdata_file = open(
            os.path.join(dirname, "userdata.txt"), "rb"
        ).read()
        user_data = aws_ec2.UserData.for_linux()
        user_data_string = str(userdata_file, "utf-8").format(efs.ref)
        user_data.add_commands(user_data_string)

        launch_template_data = aws_ec2.CfnLaunchTemplate.LaunchTemplateDataProperty(
            user_data=core.Fn.base64(user_data.render())
        )

        launch_template = aws_ec2.CfnLaunchTemplate(
            self,
            f"launch-template",
            launch_template_data=launch_template_data,
        )

        launch_template_props = aws_batch.CfnComputeEnvironment.LaunchTemplateSpecificationProperty(
            launch_template_id=launch_template.ref
        )

        image_id = (
            aws_ecs.EcsOptimizedImage.amazon_linux2()
            .get_image(self)
            .image_id
        )

        compute_resources = aws_batch.CfnComputeEnvironment.ComputeResourcesProperty(
            allocation_strategy="BEST_FIT_PROGRESSIVE",
            desiredv_cpus=0,
            image_id=image_id,
            instance_role=ecs_instance_profile.ref,
            instance_types=["m4.xlarge"],
            launch_template=launch_template_props,
            maxv_cpus=40,
            minv_cpus=0,
            security_group_ids=[security_group.security_group_id],
            subnets=[s.subnet_id for s in vpc.public_subnets],
            type="EC2",
        )

        batch = aws_batch.CfnComputeEnvironment(
            self,
            f"batch",
            compute_resources=compute_resources,
            service_role=batch_service_role.role_arn,
            type="MANAGED",
        )

        jobqueue = aws_batch.CfnJobQueue(
            self,
            f"jobqueue",
            priority=1,
            compute_environment_order=[
                aws_batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
                    compute_environment=batch.ref, order=1
                )
            ],
        )

        self.batch = batch
        self.efs = efs
        self.vpc = vpc
        self.jobqueue = jobqueue

        core.CfnOutput(self, f"job_queue", value=jobqueue.ref)
