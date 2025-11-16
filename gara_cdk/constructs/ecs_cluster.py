"""ECS cluster construct"""
from aws_cdk import (
    aws_ecs as ecs,
    aws_ec2 as ec2
)
from constructs import Construct

from gara_cdk.config import EcsClusterConfig


class EcsClusterConstruct(Construct):
    """
    Construct for creating an ECS cluster.

    Creates an ECS cluster for running Fargate tasks with optional Container Insights
    for monitoring and logging.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        config: EcsClusterConfig
    ) -> None:
        """
        Initialize the ECS cluster construct.

        Args:
            scope: Parent construct
            construct_id: Unique identifier for this construct
            vpc: VPC where the cluster will be created
            config: ECS cluster configuration settings
        """
        super().__init__(scope, construct_id)

        self._cluster = ecs.Cluster(
            self, "Cluster",
            vpc=vpc,
            cluster_name=config.cluster_name,
            container_insights=config.enable_container_insights
        )

    @property
    def cluster(self) -> ecs.Cluster:
        """Get the ECS cluster"""
        return self._cluster
