"""Container registry construct for ECR repositories"""
from aws_cdk import (
    aws_ecr as ecr,
    RemovalPolicy
)
from constructs import Construct

from gara_cdk.config import ContainerRegistryConfig


class ContainerRegistryConstruct(Construct):
    """
    Construct for creating ECR repositories for container images.

    Creates separate ECR repositories for backend and frontend Docker images
    with lifecycle policies to automatically remove old images.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: ContainerRegistryConfig
    ) -> None:
        """
        Initialize the container registry construct.

        Args:
            scope: Parent construct
            construct_id: Unique identifier for this construct
            config: Container registry configuration settings
        """
        super().__init__(scope, construct_id)

        self._backend_repo = ecr.Repository(
            self, "BackendRepo",
            repository_name=config.backend_repo_name,
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True
        )

        self._frontend_repo = ecr.Repository(
            self, "FrontendRepo",
            repository_name=config.frontend_repo_name,
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True
        )

    @property
    def backend_repo(self) -> ecr.Repository:
        """Get the backend ECR repository"""
        return self._backend_repo

    @property
    def frontend_repo(self) -> ecr.Repository:
        """Get the frontend ECR repository"""
        return self._frontend_repo
