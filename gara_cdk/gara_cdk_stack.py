"""Main CDK stack for Gara infrastructure"""
from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    CfnOutput
)
from constructs import Construct

from gara_cdk.config import GaraConfig
from gara_cdk.constructs.networking import NetworkingConstruct
from gara_cdk.constructs.storage import StorageConstruct
from gara_cdk.constructs.container_registry import ContainerRegistryConstruct
from gara_cdk.constructs.secrets import SecretsConstruct
from gara_cdk.constructs.ecs_cluster import EcsClusterConstruct
from gara_cdk.constructs.iam_roles import IamRolesConstruct
from gara_cdk.constructs.fargate_service import FargateServiceConstruct
from gara_cdk.constructs.cicd_pipeline import CicdPipelineConstruct


class GaraCdkStack(Stack):
    """
    Main CDK stack for Gara image management application.

    Creates a complete infrastructure including:
    - VPC with public and private subnets
    - S3 bucket for image storage
    - DynamoDB table for album metadata
    - ECS Fargate services for backend and frontend
    - Application Load Balancers
    - CI/CD pipelines with CodeBuild and CodePipeline
    - IAM roles and permissions
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        config = GaraConfig.default()

        networking = NetworkingConstruct(
            self, "Networking",
            config=config.vpc
        )

        storage = StorageConstruct(
            self, "Storage",
            config=config.storage
        )

        registry = ContainerRegistryConstruct(
            self, "Registry",
            config=config.container_registry
        )

        secrets = SecretsConstruct(
            self, "Secrets",
            config=config.secrets
        )

        cluster = EcsClusterConstruct(
            self, "Cluster",
            vpc=networking.vpc,
            config=config.ecs_cluster
        )

        iam_roles = IamRolesConstruct(
            self, "IamRoles",
            config=config.iam,
            image_bucket=storage.image_bucket,
            albums_table=storage.albums_table,
            api_key_secret=secrets.api_key_secret,
            backend_ecr_repo=registry.backend_repo,
            frontend_ecr_repo=registry.frontend_repo,
            github_secret=secrets.github_secret
        )

        backend_additional_env = {
            "S3_BUCKET_NAME": storage.image_bucket.bucket_name,
            "AWS_REGION": self.region,
            "SECRETS_MANAGER_API_KEY_NAME": secrets.api_key_secret_name,
            "DYNAMODB_TABLE_NAME": storage.albums_table.table_name,
            "LOG_LEVEL": "info",
            "LOG_FORMAT": "json",
            "ENVIRONMENT": "production",
            "METRICS_ENABLED": "true",
            "METRICS_NAMESPACE": "GaraImage"
        }

        backend_service = FargateServiceConstruct(
            self, "BackendService",
            cluster=cluster.cluster,
            config=config.backend_service,
            task_role=iam_roles.backend_task_role,
            execution_role=iam_roles.backend_execution_role,
            additional_environment=backend_additional_env
        )

        frontend_additional_env = {
            "NEXT_PUBLIC_API_URL": f"http://{backend_service.load_balancer_dns_name}",
            "S3_BUCKET_NAME": storage.image_bucket.bucket_name,
            "AWS_REGION": self.region,
            "LOG_LEVEL": "info",
            "ENABLE_METRICS": "true",
            "ENABLE_REQUEST_LOGGING": "true",
            "CLOUDWATCH_NAMESPACE": "GaraFrontend",
            "NODE_ENV": "production"
        }

        frontend_secrets = {
            "GARA_API_KEY": ecs.Secret.from_secrets_manager(secrets.api_key_secret)
        }

        frontend_service = FargateServiceConstruct(
            self, "FrontendService",
            cluster=cluster.cluster,
            config=config.frontend_service,
            task_role=iam_roles.frontend_task_role,
            execution_role=iam_roles.frontend_execution_role,
            additional_environment=frontend_additional_env,
            secrets=frontend_secrets
        )

        frontend_service.add_environment_variable(
            "NEXTAUTH_URL",
            f"http://{frontend_service.load_balancer_dns_name}"
        )

        backend_pipeline = CicdPipelineConstruct(
            self, "BackendPipeline",
            config=config.backend_pipeline,
            ecr_repo=registry.backend_repo,
            ecs_service=backend_service.service,
            codebuild_role=iam_roles.codebuild_role,
            github_secret=secrets.github_secret,
            github_token_json_key=secrets.github_token_json_key
        )

        frontend_pipeline = CicdPipelineConstruct(
            self, "FrontendPipeline",
            config=config.frontend_pipeline,
            ecr_repo=registry.frontend_repo,
            ecs_service=frontend_service.service,
            codebuild_role=iam_roles.codebuild_role,
            github_secret=secrets.github_secret,
            github_token_json_key=secrets.github_token_json_key
        )

        iam_roles.add_codebuild_diagnostics_permission(
            backend_pipeline.build_project,
            frontend_pipeline.build_project
        )

        self._create_outputs(
            backend_service,
            frontend_service,
            registry,
            storage
        )

    def _create_outputs(
        self,
        backend_service: FargateServiceConstruct,
        frontend_service: FargateServiceConstruct,
        registry: ContainerRegistryConstruct,
        storage: StorageConstruct
    ) -> None:
        """Create CloudFormation outputs"""
        CfnOutput(
            self, "BackendLoadBalancerDNS",
            value=backend_service.load_balancer_dns_name,
            description="URL of the Application Load Balancer for gara-image service"
        )

        CfnOutput(
            self, "FrontendLoadBalancerDNS",
            value=frontend_service.load_balancer_dns_name,
            description="URL of the Application Load Balancer for gara-frontend service"
        )

        CfnOutput(
            self, "ECRRepositoryURI",
            value=registry.backend_repo.repository_uri,
            description="URI of the ECR repository for gara-image"
        )

        CfnOutput(
            self, "FrontendECRRepositoryURI",
            value=registry.frontend_repo.repository_uri,
            description="URI of the ECR repository for gara-frontend"
        )

        CfnOutput(
            self, "ImageBucketName",
            value=storage.image_bucket.bucket_name,
            description="Name of the S3 bucket for image storage"
        )

        CfnOutput(
            self, "AlbumsTableName",
            value=storage.albums_table.table_name,
            description="DynamoDB table name for albums"
        )
