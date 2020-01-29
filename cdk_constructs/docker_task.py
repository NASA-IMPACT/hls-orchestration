from aws_cdk import (
    aws_ecs,
    core,
)
import os

dirname = os.path.dirname(os.path.realpath(__file__))


class DockerTask(core.Construct):
    def __init__(
        self, scope: core.Construct, id: str, dockerdir: str, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        volume = aws_ecs.Volume(
            name=f"volume", host={"source_path": "/mnt/efs"}
        )

        task = aws_ecs.Ec2TaskDefinition(
            self, f"laads-task", volumes=[volume],
        )

        container = task.add_container(
            f"laads-container",
            image=aws_ecs.ContainerImage.from_asset(
                directory=os.path.join(dirname, "..", "docker", "laads"),
                target="laads-task-docker",
            ),
            memory_limit_mib=10000,
            cpu=4,
        )

        container.add_mount_points(
            {
                "sourceVolume": f"{id}-volume",
                "containerPath": "/var/lasrc_aux",
                "readOnly": False,
            }
        )
