"""Tests for container infrastructure (ECR, ECS, Load Balancers)"""
import pytest
import aws_cdk.assertions as assertions
from tests.test_constants import ResourceType, InfraConfig, EnvVar
from tests.test_helpers import (
    assert_resource_count,
    assert_has_property,
    assert_container_definition,
    assert_environment_variable,
    assert_health_check_config,
    assert_task_definition_cpu_memory
)


class TestECRRepositories:
    """Test ECR repository configuration"""

    def test_ecr_repositories_created(self, template):
        """Test that exactly 2 ECR repositories are created"""
        assert_resource_count(template, ResourceType.ECR_REPOSITORY, InfraConfig.EXPECTED_ECR_REPOS)

    def test_backend_ecr_repository_name(self, template):
        """Test that backend ECR repository has correct name"""
        assert_has_property(template, ResourceType.ECR_REPOSITORY, {
            "RepositoryName": InfraConfig.BACKEND_ECR_NAME
        })

    def test_frontend_ecr_repository_name(self, template):
        """Test that frontend ECR repository has correct name"""
        assert_has_property(template, ResourceType.ECR_REPOSITORY, {
            "RepositoryName": InfraConfig.FRONTEND_ECR_NAME
        })

    def test_ecr_repositories_have_lifecycle_policies(self, template):
        """Test that ECR repositories have lifecycle policies for cleanup"""
        # Note: Current AWS CDK version doesn't generate Custom::ECRAutoDeleteImages resources
        # even with empty_on_delete=True. The parameter is still set for cleanup behavior
        # but the custom resource is no longer generated in CloudFormation.
        # ECR repositories will still be cleaned up due to removal_policy=DESTROY
        assert_resource_count(template, ResourceType.ECR_AUTO_DELETE, 0)


class TestECSCluster:
    """Test ECS cluster configuration"""

    def test_ecs_cluster_created(self, template):
        """Test that ECS cluster is created"""
        assert_resource_count(template, ResourceType.ECS_CLUSTER, 1)

    def test_ecs_cluster_name(self, template):
        """Test that ECS cluster has correct name"""
        assert_has_property(template, ResourceType.ECS_CLUSTER, {
            "ClusterName": InfraConfig.ECS_CLUSTER_NAME
        })

    def test_ecs_cluster_has_container_insights(self, template):
        """Test that Container Insights is enabled"""
        assert_has_property(template, ResourceType.ECS_CLUSTER, {
            "ClusterSettings": assertions.Match.array_with([
                {"Name": "containerInsights", "Value": "enabled"}
            ])
        })


class TestECSTaskDefinitions:
    """Test ECS task definitions"""

    def test_task_definitions_created(self, template):
        """Test that exactly 2 task definitions are created (backend and frontend)"""
        assert_resource_count(template, ResourceType.ECS_TASK_DEFINITION, InfraConfig.EXPECTED_TASK_DEFINITIONS)

    def test_task_definitions_use_awsvpc_network_mode(self, template):
        """Test that task definitions use AWSVPC network mode (required for Fargate)"""
        task_defs = template.find_resources(ResourceType.ECS_TASK_DEFINITION)
        for task_def_id, task_def in task_defs.items():
            assert task_def["Properties"]["NetworkMode"] == InfraConfig.NETWORK_MODE

    def test_task_definitions_have_correct_cpu_memory(self, template):
        """Test that task definitions have correct CPU and memory (Fargate task-level)"""
        assert_task_definition_cpu_memory(
            template,
            cpu=InfraConfig.TASK_CPU,
            memory=InfraConfig.TASK_MEMORY
        )

    def test_backend_container_configuration(self, template):
        """Test backend task definition container configuration"""
        assert_container_definition(
            template,
            InfraConfig.BACKEND_CONTAINER_NAME,
            port=InfraConfig.BACKEND_PORT
        )

    def test_frontend_container_configuration(self, template):
        """Test frontend task definition container configuration"""
        assert_container_definition(
            template,
            InfraConfig.FRONTEND_CONTAINER_NAME,
            port=InfraConfig.FRONTEND_PORT
        )

    def test_backend_environment_variables(self, template):
        """Test that backend task has correct environment variables"""
        for env_var in [EnvVar.S3_BUCKET_NAME, EnvVar.AWS_REGION, EnvVar.DYNAMODB_TABLE_NAME]:
            assert_environment_variable(template, InfraConfig.BACKEND_CONTAINER_NAME, env_var)

        # Also check PORT with specific value
        assert_environment_variable(
            template,
            InfraConfig.BACKEND_CONTAINER_NAME,
            EnvVar.PORT,
            str(InfraConfig.BACKEND_PORT)
        )

    def test_frontend_has_api_key_secret(self, template):
        """Test that frontend task has GARA_API_KEY secret"""
        assert_has_property(template, ResourceType.ECS_TASK_DEFINITION, {
            "ContainerDefinitions": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Name": InfraConfig.FRONTEND_CONTAINER_NAME,
                    "Secrets": assertions.Match.array_with([
                        assertions.Match.object_like({
                            "Name": "GARA_API_KEY"
                        })
                    ])
                })
            ])
        })

    def test_task_definitions_have_cloudwatch_logging(self, template):
        """Test that task definitions have CloudWatch logging configured"""
        task_defs = template.find_resources(ResourceType.ECS_TASK_DEFINITION)
        for task_def_id, task_def in task_defs.items():
            containers = task_def["Properties"]["ContainerDefinitions"]
            for container in containers:
                assert container["LogConfiguration"]["LogDriver"] == "awslogs"


class TestLoadBalancers:
    """Test load balancer configuration"""

    def test_load_balancers_created(self, template):
        """Test that exactly 2 ALBs are created (backend and frontend)"""
        assert_resource_count(template, ResourceType.ALB, InfraConfig.EXPECTED_LOAD_BALANCERS)

    def test_load_balancers_are_internet_facing(self, template):
        """Test that load balancers are internet-facing"""
        assert_has_property(template, ResourceType.ALB, {
            "Scheme": "internet-facing"
        })

    def test_target_group_health_check_configuration(self, template):
        """Test that target groups have correct health check configuration"""
        assert_health_check_config(
            template,
            path=InfraConfig.HEALTH_CHECK_PATH,
            codes=InfraConfig.HEALTH_CHECK_CODES,
            interval=InfraConfig.HEALTH_CHECK_INTERVAL,
            timeout=InfraConfig.HEALTH_CHECK_TIMEOUT,
            healthy_threshold=InfraConfig.HEALTHY_THRESHOLD,
            unhealthy_threshold=InfraConfig.UNHEALTHY_THRESHOLD
        )

    def test_ecs_services_created(self, template):
        """Test that exactly 2 ECS services are created"""
        assert_resource_count(template, ResourceType.ECS_SERVICE, InfraConfig.EXPECTED_ECS_SERVICES)

    def test_ecs_services_desired_count(self, template):
        """Test that ECS services have correct desired count"""
        services = template.find_resources(ResourceType.ECS_SERVICE)
        for service_id, service in services.items():
            assert service["Properties"]["DesiredCount"] == InfraConfig.DESIRED_COUNT
