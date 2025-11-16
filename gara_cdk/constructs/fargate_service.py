"""Fargate service construct with Application Load Balancer"""
from typing import Dict, Optional
from aws_cdk import (
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_iam as iam,
    aws_logs as logs,
    aws_secretsmanager as secretsmanager,
    Duration,
    RemovalPolicy,
    Stack
)
from constructs import Construct

from gara_cdk.config import ServiceConfig


class FargateServiceConstruct(Construct):
    """
    Construct for creating a Fargate service with Application Load Balancer.

    Creates a complete Fargate service including task definition, container,
    log group, ALB, and target group with health checks.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        cluster: ecs.ICluster,
        config: ServiceConfig,
        task_role: iam.IRole,
        execution_role: iam.IRole,
        additional_environment: Optional[Dict[str, str]] = None,
        secrets: Optional[Dict[str, ecs.Secret]] = None
    ) -> None:
        """
        Initialize the Fargate service construct.

        Args:
            scope: Parent construct
            construct_id: Unique identifier for this construct
            cluster: ECS cluster to deploy the service to
            config: Service configuration settings
            task_role: IAM role for the task
            execution_role: IAM execution role for the task
            additional_environment: Additional environment variables to add
            secrets: Secrets to inject into the container
        """
        super().__init__(scope, construct_id)

        stack = Stack.of(self)

        log_group = logs.LogGroup(
            self, "LogGroup",
            log_group_name=config.log_group_name,
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )

        task_definition = ecs.FargateTaskDefinition(
            self, "TaskDef",
            family=config.family,
            task_role=task_role,
            execution_role=execution_role,
            cpu=config.task_definition.cpu,
            memory_limit_mib=config.task_definition.memory_limit_mib
        )

        environment = config.environment_variables.copy()
        if additional_environment:
            environment.update(additional_environment)

        container_kwargs = {
            "image": ecs.ContainerImage.from_registry("nginx:alpine"),
            "logging": ecs.LogDrivers.aws_logs(
                log_group=log_group,
                stream_prefix=config.family
            ),
            "port_mappings": [
                ecs.PortMapping(
                    container_port=config.container_port,
                    protocol=ecs.Protocol.TCP
                )
            ],
            "environment": environment
        }

        if secrets:
            container_kwargs["secrets"] = secrets

        self._container = task_definition.add_container(
            config.container_name,
            **container_kwargs
        )

        self._service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "Service",
            cluster=cluster,
            service_name=config.service_name,
            task_definition=task_definition,
            desired_count=config.desired_count,
            public_load_balancer=True,
            listener_port=config.listener_port,
            health_check_grace_period=Duration.seconds(
                config.health_check.grace_period_seconds
            )
        )

        self._service.target_group.configure_health_check(
            path=config.health_check.path,
            healthy_http_codes=config.health_check.healthy_http_codes,
            interval=Duration.seconds(config.health_check.interval_seconds),
            timeout=Duration.seconds(config.health_check.timeout_seconds),
            healthy_threshold_count=config.health_check.healthy_threshold_count,
            unhealthy_threshold_count=config.health_check.unhealthy_threshold_count
        )

    def add_environment_variable(self, name: str, value: str) -> None:
        """
        Add an environment variable to the container.

        Args:
            name: Environment variable name
            value: Environment variable value
        """
        self._container.add_environment(name, value)

    @property
    def service(self) -> ecs.FargateService:
        """Get the Fargate service"""
        return self._service.service

    @property
    def load_balancer_dns_name(self) -> str:
        """Get the load balancer DNS name"""
        return self._service.load_balancer.load_balancer_dns_name

    @property
    def container(self) -> ecs.ContainerDefinition:
        """Get the container definition"""
        return self._container

    @property
    def fargate_service(self) -> ecs_patterns.ApplicationLoadBalancedFargateService:
        """Get the ApplicationLoadBalancedFargateService pattern"""
        return self._service
