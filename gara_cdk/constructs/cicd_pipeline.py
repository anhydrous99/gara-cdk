"""CI/CD pipeline construct for CodeBuild and CodePipeline"""
from aws_cdk import (
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_ecr as ecr,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    custom_resources as cr,
    Duration,
    Stack
)
from constructs import Construct

from gara_cdk.config import PipelineConfig


class CicdPipelineConstruct(Construct):
    """
    Construct for creating a complete CI/CD pipeline.

    Creates CodeBuild project for building Docker images and CodePipeline
    for orchestrating source, build, and deployment stages with automatic
    deployment to ECS.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: PipelineConfig,
        ecr_repo: ecr.IRepository,
        ecs_service: ecs.FargateService,
        codebuild_role: iam.IRole,
        github_secret: secretsmanager.ISecret,
        github_token_json_key: str
    ) -> None:
        """
        Initialize the CI/CD pipeline construct.

        Args:
            scope: Parent construct
            construct_id: Unique identifier for this construct
            config: Pipeline configuration settings
            ecr_repo: ECR repository for Docker images
            ecs_service: ECS service to deploy to
            codebuild_role: IAM role for CodeBuild
            github_secret: GitHub token secret
            github_token_json_key: JSON key for GitHub token in secret
        """
        super().__init__(scope, construct_id)

        stack = Stack.of(self)

        github_credentials = codebuild.GitHubSourceCredentials(
            self, "GitHubCreds",
            access_token=github_secret.secret_value_from_json(github_token_json_key)
        )

        self._build_project = self._create_build_project(
            config,
            ecr_repo,
            codebuild_role,
            github_secret,
            stack
        )

        self._pipeline = self._create_pipeline(
            config,
            ecs_service,
            github_secret,
            github_token_json_key
        )

        self._create_pipeline_trigger()

    def _create_build_project(
        self,
        config: PipelineConfig,
        ecr_repo: ecr.IRepository,
        codebuild_role: iam.IRole,
        github_secret: secretsmanager.ISecret,
        stack: Stack
    ) -> codebuild.Project:
        """Create CodeBuild project for building Docker images"""

        # Determine ECR env var name based on project name
        ecr_env_var_name = (
            "FRONTEND_ECR_REPOSITORY_URI"
            if "frontend" in config.codebuild.project_name.lower()
            else "ECR_REPOSITORY_URI"
        )

        build_project = codebuild.Project(
            self, "BuildProject",
            project_name=config.codebuild.project_name,
            role=codebuild_role,
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                privileged=config.codebuild.privileged,
                environment_variables={
                    "AWS_ACCOUNT_ID": codebuild.BuildEnvironmentVariable(
                        value=stack.account
                    ),
                    "AWS_DEFAULT_REGION": codebuild.BuildEnvironmentVariable(
                        value=stack.region
                    ),
                    ecr_env_var_name: codebuild.BuildEnvironmentVariable(
                        value=ecr_repo.repository_uri
                    ),
                    "GITHUB_TOKEN": codebuild.BuildEnvironmentVariable(
                        value=github_secret.secret_arn,
                        type=codebuild.BuildEnvironmentVariableType.SECRETS_MANAGER
                    )
                }
            ),
            source=codebuild.Source.git_hub(
                owner=config.github_source.owner,
                repo=config.github_source.repo,
                branch_or_ref=config.github_source.branch,
                clone_depth=config.codebuild.clone_depth,
                webhook=True,
                webhook_filters=[
                    codebuild.FilterGroup.in_event_of(
                        codebuild.EventAction.PUSH,
                        codebuild.EventAction.PULL_REQUEST_MERGED
                    ).and_branch_is(config.github_source.branch)
                ]
            ),
            build_spec=self._create_build_spec(
                config.container_name,
                config.image_definitions_file,
                ecr_env_var_name
            ),
            timeout=Duration.minutes(config.codebuild.timeout_minutes)
        )

        return build_project

    def _create_build_spec(
        self,
        container_name: str,
        image_definitions_file: str,
        ecr_env_var_name: str
    ) -> codebuild.BuildSpec:
        """Create BuildSpec for CodeBuild project"""
        return codebuild.BuildSpec.from_object({
            "version": "0.2",
            "phases": {
                "pre_build": {
                    "commands": [
                        "echo Logging in to Amazon ECR...",
                        f"echo Repository URI: ${ecr_env_var_name}",
                        "echo AWS Region: $AWS_DEFAULT_REGION",
                        f"aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin ${ecr_env_var_name} || exit 1",
                        "COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)",
                        "IMAGE_TAG=${COMMIT_HASH:=latest}",
                        "echo IMAGE_TAG=$IMAGE_TAG"
                    ]
                },
                "build": {
                    "commands": [
                        "echo Build started on `date`",
                        f"echo Building {container_name} service...",
                        f"docker build -t ${ecr_env_var_name}:latest -t ${ecr_env_var_name}:$IMAGE_TAG . || exit 1"
                    ]
                },
                "post_build": {
                    "commands": [
                        "echo Build completed on `date`",
                        f"echo Pushing the Docker image to ${ecr_env_var_name}...",
                        f"docker push ${ecr_env_var_name}:latest || exit 1",
                        f"docker push ${ecr_env_var_name}:$IMAGE_TAG || exit 1",
                        "echo Writing image definitions file...",
                        f"printf '[{{\"name\":\"{container_name}\",\"imageUri\":\"%s\"}}]' ${ecr_env_var_name}:latest > {image_definitions_file}"
                    ]
                }
            },
            "artifacts": {
                "files": [image_definitions_file]
            }
        })

    def _create_pipeline(
        self,
        config: PipelineConfig,
        ecs_service: ecs.FargateService,
        github_secret: secretsmanager.ISecret,
        github_token_json_key: str
    ) -> codepipeline.Pipeline:
        """Create CodePipeline with source, build, and deploy stages"""
        pipeline = codepipeline.Pipeline(
            self, "Pipeline",
            pipeline_name=config.pipeline_name,
            restart_execution_on_update=True
        )

        source_output = codepipeline.Artifact()
        source_action = codepipeline_actions.GitHubSourceAction(
            action_name="GitHub_Source",
            owner=config.github_source.owner,
            repo=config.github_source.repo,
            oauth_token=github_secret.secret_value_from_json(github_token_json_key),
            output=source_output,
            branch=config.github_source.branch,
            trigger=codepipeline_actions.GitHubTrigger.WEBHOOK
        )

        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

        build_output = codepipeline.Artifact()
        build_action = codepipeline_actions.CodeBuildAction(
            action_name="Build",
            project=self._build_project,
            input=source_output,
            outputs=[build_output]
        )

        pipeline.add_stage(
            stage_name="Build",
            actions=[build_action]
        )

        deploy_action = codepipeline_actions.EcsDeployAction(
            action_name="Deploy",
            service=ecs_service,
            deployment_timeout=Duration.minutes(10),
            image_file=codepipeline.ArtifactPath(
                build_output,
                config.image_definitions_file
            )
        )

        pipeline.add_stage(
            stage_name="Deploy",
            actions=[deploy_action]
        )

        pipeline.node.add_dependency(ecs_service)

        return pipeline

    def _create_pipeline_trigger(self) -> None:
        """Create custom resource to trigger pipeline on stack creation"""
        trigger_resource = cr.AwsCustomResource(
            self, "PipelineTrigger",
            on_create=cr.AwsSdkCall(
                service="CodePipeline",
                action="startPipelineExecution",
                parameters={
                    "name": self._pipeline.pipeline_name
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    f"trigger-{self._pipeline.pipeline_name}-initial"
                )
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    actions=["codepipeline:StartPipelineExecution"],
                    resources=[self._pipeline.pipeline_arn]
                )
            ])
        )

        trigger_resource.node.add_dependency(self._pipeline)

    @property
    def build_project(self) -> codebuild.Project:
        """Get the CodeBuild project"""
        return self._build_project

    @property
    def pipeline(self) -> codepipeline.Pipeline:
        """Get the CodePipeline"""
        return self._pipeline
