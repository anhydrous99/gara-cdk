"""Configuration management for Gara CDK infrastructure"""
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class VpcConfig:
    """VPC and networking configuration"""
    max_azs: int = 2
    nat_gateways: int = 1
    public_subnet_cidr_mask: int = 24
    private_subnet_cidr_mask: int = 24
    vpc_name: str = "gara-vpc"


@dataclass
class StorageConfig:
    """S3 and DynamoDB configuration"""
    s3_bucket_prefix: str = "gara-images"
    dynamodb_table_prefix: str = "gara-albums"
    partition_key: str = "AlbumId"
    gsi_partition_key: str = "Published"
    gsi_sort_key: str = "CreatedAt"
    gsi_name: str = "PublishedIndex"
    log_retention_days: int = 7


@dataclass
class ContainerRegistryConfig:
    """ECR repository configuration"""
    backend_repo_name: str = "gara-image-app"
    frontend_repo_name: str = "gara-frontend-app"


@dataclass
class EcsClusterConfig:
    """ECS cluster configuration"""
    cluster_name: str = "gara-cluster"
    enable_container_insights: bool = True


@dataclass
class TaskDefinitionConfig:
    """ECS task definition configuration"""
    cpu: int = 512
    memory_limit_mib: int = 1024


@dataclass
class HealthCheckConfig:
    """Application Load Balancer health check configuration"""
    path: str = "/"
    healthy_http_codes: str = "200-399"
    interval_seconds: int = 60
    timeout_seconds: int = 10
    healthy_threshold_count: int = 2
    unhealthy_threshold_count: int = 3
    grace_period_seconds: int = 60


@dataclass
class ServiceConfig:
    """Fargate service configuration"""
    family: str
    container_name: str
    container_port: int
    log_group_name: str
    service_name: str
    desired_count: int = 1
    listener_port: int = 80
    task_definition: TaskDefinitionConfig = None
    health_check: HealthCheckConfig = None
    environment_variables: Dict[str, str] = None

    def __post_init__(self):
        if self.task_definition is None:
            self.task_definition = TaskDefinitionConfig()
        if self.health_check is None:
            self.health_check = HealthCheckConfig()
        if self.environment_variables is None:
            self.environment_variables = {}


@dataclass
class GitHubSourceConfig:
    """GitHub source repository configuration"""
    owner: str
    repo: str
    branch: str = "main"


@dataclass
class CodeBuildConfig:
    """CodeBuild project configuration"""
    project_name: str
    build_image: str = "aws/codebuild/standard:7.0"
    privileged: bool = True
    timeout_minutes: int = 30
    clone_depth: int = 1


@dataclass
class PipelineConfig:
    """CI/CD pipeline configuration"""
    pipeline_name: str
    github_source: GitHubSourceConfig
    codebuild: CodeBuildConfig
    container_name: str
    image_definitions_file: str


@dataclass
class SecretsConfig:
    """Secrets Manager configuration"""
    github_token_secret_name: str = "GithubToken"
    github_token_json_key: str = "github"
    api_key_secret_name: str = "gara-api-key"


@dataclass
class IamConfig:
    """IAM role naming configuration"""
    backend_task_role_name: str = "gara-backend-task-role"
    frontend_task_role_name: str = "gara-frontend-task-role"
    backend_execution_role_name: str = "gara-backend-task-execution-role"
    frontend_execution_role_name: str = "gara-frontend-task-execution-role"
    codebuild_role_name: str = "gara-codebuild-role"


@dataclass
class GaraConfig:
    """Main configuration for Gara CDK infrastructure"""
    vpc: VpcConfig
    storage: StorageConfig
    container_registry: ContainerRegistryConfig
    ecs_cluster: EcsClusterConfig
    backend_service: ServiceConfig
    frontend_service: ServiceConfig
    backend_pipeline: PipelineConfig
    frontend_pipeline: PipelineConfig
    secrets: SecretsConfig
    iam: IamConfig

    @classmethod
    def default(cls) -> "GaraConfig":
        """Create default configuration matching current infrastructure"""

        # Backend service configuration
        backend_service = ServiceConfig(
            family="gara-backend-task",
            container_name="gara-image-container",
            container_port=8080,
            log_group_name="/ecs/gara-image",
            service_name="gara-image-service",
            environment_variables={
                "PORT": "8080"
            }
        )

        # Frontend service configuration
        frontend_service = ServiceConfig(
            family="gara-frontend-task",
            container_name="gara-frontend-container",
            container_port=80,
            log_group_name="/ecs/gara-frontend",
            service_name="gara-frontend-service",
            environment_variables={
                "NEXTAUTH_SECRET": "change-me-in-production"
            }
        )

        # Backend pipeline configuration
        backend_pipeline = PipelineConfig(
            pipeline_name="gara-backend-pipeline",
            github_source=GitHubSourceConfig(
                owner="anhydrous99",
                repo="gara-image"
            ),
            codebuild=CodeBuildConfig(
                project_name="gara-image-build"
            ),
            container_name="gara-image-container",
            image_definitions_file="gara-image-definitions.json"
        )

        # Frontend pipeline configuration
        frontend_pipeline = PipelineConfig(
            pipeline_name="gara-frontend-pipeline",
            github_source=GitHubSourceConfig(
                owner="anhydrous99",
                repo="gara-frontend"
            ),
            codebuild=CodeBuildConfig(
                project_name="gara-frontend-build"
            ),
            container_name="gara-frontend-container",
            image_definitions_file="gara-frontend-definitions.json"
        )

        return cls(
            vpc=VpcConfig(),
            storage=StorageConfig(),
            container_registry=ContainerRegistryConfig(),
            ecs_cluster=EcsClusterConfig(),
            backend_service=backend_service,
            frontend_service=frontend_service,
            backend_pipeline=backend_pipeline,
            frontend_pipeline=frontend_pipeline,
            secrets=SecretsConfig(),
            iam=IamConfig()
        )
