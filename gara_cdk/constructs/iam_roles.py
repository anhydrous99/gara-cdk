"""IAM roles construct for ECS and CodeBuild"""
from typing import List
from aws_cdk import (
    aws_iam as iam,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_secretsmanager as secretsmanager,
    aws_ecr as ecr,
    aws_codebuild as codebuild
)
from constructs import Construct

from gara_cdk.config import IamConfig


class IamRolesConstruct(Construct):
    """
    Construct for creating IAM roles and permissions.

    Creates task roles, execution roles, and CodeBuild roles with appropriate
    permissions following the principle of least privilege.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: IamConfig,
        image_bucket: s3.IBucket,
        albums_table: dynamodb.ITable,
        api_key_secret: secretsmanager.ISecret,
        backend_ecr_repo: ecr.IRepository,
        frontend_ecr_repo: ecr.IRepository,
        github_secret: secretsmanager.ISecret,
        backend_build_project: codebuild.IProject = None,
        frontend_build_project: codebuild.IProject = None
    ) -> None:
        """
        Initialize the IAM roles construct.

        Args:
            scope: Parent construct
            construct_id: Unique identifier for this construct
            config: IAM configuration settings
            image_bucket: S3 bucket for images
            albums_table: DynamoDB table for albums
            api_key_secret: API key secret
            backend_ecr_repo: Backend ECR repository
            frontend_ecr_repo: Frontend ECR repository
            github_secret: GitHub token secret
            backend_build_project: Backend CodeBuild project (optional for late binding)
            frontend_build_project: Frontend CodeBuild project (optional for late binding)
        """
        super().__init__(scope, construct_id)

        self._backend_task_role = self._create_backend_task_role(
            config.backend_task_role_name,
            image_bucket,
            albums_table,
            api_key_secret
        )

        self._frontend_task_role = self._create_frontend_task_role(
            config.frontend_task_role_name,
            image_bucket,
            albums_table,
            api_key_secret
        )

        self._backend_execution_role = self._create_execution_role(
            config.backend_execution_role_name,
            backend_ecr_repo
        )

        self._frontend_execution_role = self._create_execution_role(
            config.frontend_execution_role_name,
            frontend_ecr_repo,
            api_key_secret
        )

        self._codebuild_role = self._create_codebuild_role(
            config.codebuild_role_name,
            backend_ecr_repo,
            frontend_ecr_repo,
            github_secret,
            backend_build_project,
            frontend_build_project
        )

    def _create_backend_task_role(
        self,
        role_name: str,
        image_bucket: s3.IBucket,
        albums_table: dynamodb.ITable,
        api_key_secret: secretsmanager.ISecret
    ) -> iam.Role:
        """Create IAM role for backend ECS tasks"""
        task_role = iam.Role(
            self, "BackendTaskRole",
            role_name=role_name,
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )

        image_bucket.grant_read_write(task_role)
        albums_table.grant_read_write_data(task_role)
        api_key_secret.grant_read(task_role)

        task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
                conditions={
                    "StringEquals": {
                        "cloudwatch:namespace": "GaraImage"
                    }
                }
            )
        )

        return task_role

    def _create_frontend_task_role(
        self,
        role_name: str,
        image_bucket: s3.IBucket,
        albums_table: dynamodb.ITable,
        api_key_secret: secretsmanager.ISecret
    ) -> iam.Role:
        """Create IAM role for frontend ECS tasks"""
        task_role = iam.Role(
            self, "FrontendTaskRole",
            role_name=role_name,
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )

        image_bucket.grant_read(task_role)
        albums_table.grant_read_data(task_role)
        api_key_secret.grant_read(task_role)

        task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
                conditions={
                    "StringEquals": {
                        "cloudwatch:namespace": "GaraFrontend"
                    }
                }
            )
        )

        return task_role

    def _create_execution_role(
        self,
        role_name: str,
        ecr_repo: ecr.IRepository,
        api_key_secret: secretsmanager.ISecret = None
    ) -> iam.Role:
        """Create IAM execution role for ECS tasks"""
        execution_role = iam.Role(
            self, f"ExecutionRole-{role_name}",
            role_name=role_name,
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ]
        )

        ecr_repo.grant_pull(execution_role)

        if api_key_secret:
            api_key_secret.grant_read(execution_role)

        return execution_role

    def _create_codebuild_role(
        self,
        role_name: str,
        backend_ecr_repo: ecr.IRepository,
        frontend_ecr_repo: ecr.IRepository,
        github_secret: secretsmanager.ISecret,
        backend_build_project: codebuild.IProject = None,
        frontend_build_project: codebuild.IProject = None
    ) -> iam.Role:
        """Create IAM role for CodeBuild projects"""
        codebuild_role = iam.Role(
            self, "CodeBuildRole",
            role_name=role_name,
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonEC2ContainerRegistryPowerUser"
                )
            ]
        )

        codebuild_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=[
                    "arn:aws:logs:*:*:log-group:/aws/codebuild/*",
                    "arn:aws:logs:*:*:log-group:/aws/codebuild/*:log-stream:*"
                ]
            )
        )

        github_secret.grant_read(codebuild_role)

        codebuild_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:PutObject",
                    "s3:PutObjectAcl"
                ],
                resources=["arn:aws:s3:::codepipeline-*/*"]
            )
        )

        codebuild_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:ListBucket",
                    "s3:GetBucketVersioning"
                ],
                resources=["arn:aws:s3:::codepipeline-*"]
            )
        )

        backend_ecr_repo.grant_pull_push(codebuild_role)
        frontend_ecr_repo.grant_pull_push(codebuild_role)

        codebuild_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudwatch:PutMetricData",
                    "cloudwatch:GetMetricData",
                    "cloudwatch:ListMetrics"
                ],
                resources=["*"]
            )
        )

        if backend_build_project and frontend_build_project:
            codebuild_role.add_to_policy(
                iam.PolicyStatement(
                    actions=[
                        "codebuild:BatchGetBuilds",
                        "codebuild:BatchGetBuildBatches"
                    ],
                    resources=[
                        backend_build_project.project_arn,
                        frontend_build_project.project_arn
                    ]
                )
            )

        return codebuild_role

    def add_codebuild_diagnostics_permission(
        self,
        backend_build_project: codebuild.IProject,
        frontend_build_project: codebuild.IProject
    ) -> None:
        """
        Add CodeBuild diagnostics permissions after projects are created.

        This is needed because of circular dependency - projects need role,
        but role needs project ARNs for specific permissions.
        """
        self._codebuild_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "codebuild:BatchGetBuilds",
                    "codebuild:BatchGetBuildBatches"
                ],
                resources=[
                    backend_build_project.project_arn,
                    frontend_build_project.project_arn
                ]
            )
        )

    @property
    def backend_task_role(self) -> iam.Role:
        """Get the backend task role"""
        return self._backend_task_role

    @property
    def frontend_task_role(self) -> iam.Role:
        """Get the frontend task role"""
        return self._frontend_task_role

    @property
    def backend_execution_role(self) -> iam.Role:
        """Get the backend execution role"""
        return self._backend_execution_role

    @property
    def frontend_execution_role(self) -> iam.Role:
        """Get the frontend execution role"""
        return self._frontend_execution_role

    @property
    def codebuild_role(self) -> iam.Role:
        """Get the CodeBuild role"""
        return self._codebuild_role
