from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_iam as iam,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_ecr as ecr,
    aws_secretsmanager as secretmanager,
    aws_logs as logs,
    custom_resources as cr,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    CfnOutput,
    RemovalPolicy,
    Duration
)
from constructs import Construct


class GaraCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a VPC
        vpc = ec2.Vpc(
            self, "GaraVpc",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ],
            vpc_name="gara-vpc"
        )

        # Create S3 bucket for image storage
        image_bucket = s3.Bucket(
            self, "GaraImageBucket",
            bucket_name=f"gara-images-{self.account}-{self.region}",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Create DynamoDB table for album management
        albums_table = dynamodb.Table(
            self, "GaraAlbumsTable",
            table_name=f"gara-albums-{self.account}-{self.region}",
            partition_key=dynamodb.Attribute(
                name="AlbumId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        # Add Global Secondary Index for querying published albums efficiently
        # This allows filtering by Published status with CreatedAt sorting
        albums_table.add_global_secondary_index(
            index_name="PublishedIndex",
            partition_key=dynamodb.Attribute(
                name="Published",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="CreatedAt",
                type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # Create ECR repository for gara-image service
        ecr_repo = ecr.Repository(
            self, "GaraEcrRepo",
            repository_name="gara-image-app",
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True
        )

        # Create ECR repository for frontend
        frontend_ecr_repo = ecr.Repository(
            self, "GaraFrontendEcrRepo",
            repository_name="gara-frontend-app",
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True
        )

        # Create ECS Cluster (Fargate manages capacity automatically)
        cluster = ecs.Cluster(
            self, "GaraCluster",
            vpc=vpc,
            cluster_name="gara-cluster",
            container_insights=True
        )

        # Reference the existing GitHub token secret
        github_secret = secretmanager.Secret.from_secret_name_v2(
            self, "GithubToken",
            "GithubToken"
        )

        # Reference the gara API key secret
        api_key_secret = secretmanager.Secret.from_secret_name_v2(
            self, "GaraApiKey",
            "gara-api-key"
        )

        # Create task role for gara-image ECS tasks
        task_role = iam.Role(
            self, "GaraTaskRole",
            role_name="gara-backend-task-role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )

        # Grant S3 permissions to task role
        image_bucket.grant_read_write(task_role)

        # Grant Secrets Manager permissions to task role
        api_key_secret.grant_read(task_role)

        # Grant DynamoDB read/write permissions to backend task role
        albums_table.grant_read_write_data(task_role)

        # Create task role for frontend ECS tasks
        frontend_task_role = iam.Role(
            self, "GaraFrontendTaskRole",
            role_name="gara-frontend-task-role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )

        # Grant S3 read-only permissions to frontend task role
        image_bucket.grant_read(frontend_task_role)

        # Grant DynamoDB read-only permissions to frontend task role
        albums_table.grant_read_data(frontend_task_role)

        # Grant API key secret read permission to frontend task role (for proxy authentication)
        api_key_secret.grant_read(frontend_task_role)

        # Create IAM role for CodeBuild
        codebuild_role = iam.Role(
            self, "CodeBuildRole",
            role_name="gara-codebuild-role",
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryPowerUser")
            ]
        )

        # Grant CodeBuild CloudWatch Logs permissions
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

        # Grant CodeBuild access to the secret
        github_secret.grant_read(codebuild_role)

        # Add creds for building and deploying
        codebuild.GitHubSourceCredentials(
            self, "GaraCodeBuildGithubCreds",
            access_token=github_secret.secret_value_from_json('github')
        )

        # Grant CodeBuild permissions to access pipeline artifacts in S3
        # CodeBuild needs access to the pipeline artifact bucket for input/output
        codebuild_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:PutObject",
                    "s3:PutObjectAcl"
                ],
                resources=["arn:aws:s3:::codepipeline-*/*"],
                effect=iam.Effect.ALLOW
            )
        )

        # Grant CodeBuild permissions to list buckets (for artifact management)
        codebuild_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:ListBucket",
                    "s3:GetBucketVersioning"
                ],
                resources=["arn:aws:s3:::codepipeline-*"],
                effect=iam.Effect.ALLOW
            )
        )

        # Grant CodeBuild permissions to push to frontend ECR
        frontend_ecr_repo.grant_pull_push(codebuild_role)

        # Grant CodeBuild permissions for CloudWatch metrics and monitoring
        codebuild_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudwatch:PutMetricData",
                    "cloudwatch:GetMetricData",
                    "cloudwatch:ListMetrics"
                ],
                resources=["*"],
                effect=iam.Effect.ALLOW
            )
        )

        # Create CodeBuild project for gara-image (backend)
        backend_build_project = codebuild.Project(
            self, "GaraImageBuildProject",
            project_name="gara-image-build",
            role=codebuild_role,  # type: ignore
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,  # type: ignore
                privileged=True,
                environment_variables={
                    "AWS_ACCOUNT_ID": codebuild.BuildEnvironmentVariable(
                        value=self.account
                    ),
                    "AWS_DEFAULT_REGION": codebuild.BuildEnvironmentVariable(
                        value=self.region
                    ),
                    "ECR_REPOSITORY_URI": codebuild.BuildEnvironmentVariable(
                        value=ecr_repo.repository_uri
                    ),
                    "GITHUB_TOKEN": codebuild.BuildEnvironmentVariable(
                        value=github_secret.secret_arn,
                        type=codebuild.BuildEnvironmentVariableType.SECRETS_MANAGER
                    )
                }
            ),
            source=codebuild.Source.git_hub(
                owner="anhydrous99",
                repo="gara-image",
                branch_or_ref="main",
                clone_depth=1,
                webhook=True,
                webhook_filters=[
                    codebuild.FilterGroup.in_event_of(
                        codebuild.EventAction.PUSH,
                        codebuild.EventAction.PULL_REQUEST_MERGED
                    ).and_branch_is("main")
                ]
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "pre_build": {
                        "commands": [
                            "echo Logging in to Amazon ECR...",
                            "echo Repository URI: $ECR_REPOSITORY_URI",
                            "echo AWS Region: $AWS_DEFAULT_REGION",
                            "aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URI || exit 1",
                            "COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)",
                            "IMAGE_TAG=${COMMIT_HASH:=latest}",
                            "echo IMAGE_TAG=$IMAGE_TAG"
                        ]
                    },
                    "build": {
                        "commands": [
                            "echo Build started on `date`",
                            "echo Building gara-image service...",
                            "docker build -t $ECR_REPOSITORY_URI:latest -t $ECR_REPOSITORY_URI:$IMAGE_TAG . || exit 1"
                        ]
                    },
                    "post_build": {
                        "commands": [
                            "echo Build completed on `date`",
                            "echo Pushing the Docker image to $ECR_REPOSITORY_URI...",
                            "docker push $ECR_REPOSITORY_URI:latest || exit 1",
                            "docker push $ECR_REPOSITORY_URI:$IMAGE_TAG || exit 1",
                            "echo Writing image definitions file...",
                            "printf '[{\"name\":\"gara-image-container\",\"imageUri\":\"%s\"}]' $ECR_REPOSITORY_URI:latest > gara-image-definitions.json"
                        ]
                    }
                },
                "artifacts": {
                    "files": ["gara-image-definitions.json"]
                }
            }),
            timeout=Duration.minutes(30)
        )

        # Create CodeBuild project for gara-frontend
        frontend_build_project = codebuild.Project(
            self, "GaraFrontendBuildProject",
            project_name="gara-frontend-build",
            role=codebuild_role,  # type: ignore
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,  # type: ignore
                privileged=True,
                environment_variables={
                    "AWS_ACCOUNT_ID": codebuild.BuildEnvironmentVariable(
                        value=self.account
                    ),
                    "AWS_DEFAULT_REGION": codebuild.BuildEnvironmentVariable(
                        value=self.region
                    ),
                    "FRONTEND_ECR_REPOSITORY_URI": codebuild.BuildEnvironmentVariable(
                        value=frontend_ecr_repo.repository_uri
                    ),
                    "GITHUB_TOKEN": codebuild.BuildEnvironmentVariable(
                        value=github_secret.secret_arn,
                        type=codebuild.BuildEnvironmentVariableType.SECRETS_MANAGER
                    )
                }
            ),
            source=codebuild.Source.git_hub(
                owner="anhydrous99",
                repo="gara-frontend",
                branch_or_ref="main",
                clone_depth=1,
                webhook=True,
                webhook_filters=[
                    codebuild.FilterGroup.in_event_of(
                        codebuild.EventAction.PUSH,
                        codebuild.EventAction.PULL_REQUEST_MERGED
                    ).and_branch_is("main")
                ]
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "pre_build": {
                        "commands": [
                            "echo Logging in to Amazon ECR...",
                            "echo Repository URI: $FRONTEND_ECR_REPOSITORY_URI",
                            "echo AWS Region: $AWS_DEFAULT_REGION",
                            "aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $FRONTEND_ECR_REPOSITORY_URI || exit 1",
                            "COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)",
                            "IMAGE_TAG=${COMMIT_HASH:=latest}",
                            "echo IMAGE_TAG=$IMAGE_TAG"
                        ]
                    },
                    "build": {
                        "commands": [
                            "echo Build started on `date`",
                            "echo Building gara-frontend service...",
                            "docker build -t $FRONTEND_ECR_REPOSITORY_URI:latest -t $FRONTEND_ECR_REPOSITORY_URI:$IMAGE_TAG . || exit 1"
                        ]
                    },
                    "post_build": {
                        "commands": [
                            "echo Build completed on `date`",
                            "echo Pushing the Docker image to $FRONTEND_ECR_REPOSITORY_URI...",
                            "docker push $FRONTEND_ECR_REPOSITORY_URI:latest || exit 1",
                            "docker push $FRONTEND_ECR_REPOSITORY_URI:$IMAGE_TAG || exit 1",
                            "echo Writing image definitions file...",
                            "printf '[{\"name\":\"gara-frontend-container\",\"imageUri\":\"%s\"}]' $FRONTEND_ECR_REPOSITORY_URI:latest > gara-frontend-definitions.json"
                        ]
                    }
                },
                "artifacts": {
                    "files": ["gara-frontend-definitions.json"]
                }
            }),
            timeout=Duration.minutes(30)
        )

        # Grant CodeBuild permissions for build state and diagnostics
        codebuild_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "codebuild:BatchGetBuilds",
                    "codebuild:BatchGetBuildBatches"
                ],
                resources=[backend_build_project.project_arn, frontend_build_project.project_arn],
                effect=iam.Effect.ALLOW
            )
        )

        # Grant CodeBuild permissions to push to ECR
        ecr_repo.grant_pull_push(codebuild_role)

        # Create explicit CloudWatch log groups
        backend_log_group = logs.LogGroup(
            self, "GaraBackendLogGroup",
            log_group_name="/ecs/gara-image",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )

        frontend_log_group = logs.LogGroup(
            self, "GaraFrontendLogGroup",
            log_group_name="/ecs/gara-frontend",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create execution role for backend task (ECS uses this to pull images and access secrets)
        backend_execution_role = iam.Role(
            self, "GaraBackendExecutionRole",
            role_name="gara-backend-task-execution-role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ]
        )

        # Grant execution role permissions to pull from ECR
        ecr_repo.grant_pull(backend_execution_role)

        # Create execution role for frontend task (ECS uses this to pull images and access secrets)
        frontend_execution_role = iam.Role(
            self, "GaraFrontendExecutionRole",
            role_name="gara-frontend-task-execution-role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ]
        )

        # Grant execution role permissions to pull from frontend ECR
        frontend_ecr_repo.grant_pull(frontend_execution_role)

        # Grant execution roles permissions to read secrets from Secrets Manager
        api_key_secret.grant_read(frontend_execution_role)

        # Create Task Definition for Fargate
        task_definition = ecs.FargateTaskDefinition(
            self, "GaraTaskDef",
            family="gara-backend-task",
            task_role=task_role,
            execution_role=backend_execution_role,
            cpu=512,
            memory_limit_mib=1024
        )

        # Add container to task definition
        # Use nginx as placeholder - it stays running and responds to health checks
        # The pipeline will update this with the actual image
        task_definition.add_container(
            "gara-image-container",
            image=ecs.ContainerImage.from_registry("nginx:alpine"),
            logging=ecs.LogDrivers.aws_logs(
                log_group=backend_log_group,
                stream_prefix="gara-image"
            ),
            port_mappings=[
                ecs.PortMapping(
                    container_port=8080,  # Non-root user needs port > 1024
                    protocol=ecs.Protocol.TCP
                )
            ],
            environment={
                "S3_BUCKET_NAME": image_bucket.bucket_name,
                "AWS_REGION": self.region,
                "SECRETS_MANAGER_API_KEY_NAME": "gara-api-key",
                "PORT": "8080",
                "DYNAMODB_TABLE_NAME": albums_table.table_name
            }
        )

        # Create Fargate ECS Service with Application Load Balancer
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "GaraService",
            cluster=cluster,
            service_name="gara-image-service",
            task_definition=task_definition,
            desired_count=1,
            public_load_balancer=True,
            listener_port=80,
            health_check_grace_period=Duration.seconds(60)
        )

        # Configure health check for the target group
        fargate_service.target_group.configure_health_check(
            path="/",
            healthy_http_codes="200-399",
            interval=Duration.seconds(60),
            timeout=Duration.seconds(10),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3
        )

        # Create Frontend Task Definition for Fargate
        frontend_task_definition = ecs.FargateTaskDefinition(
            self, "GaraFrontendTaskDef",
            family="gara-frontend-task",
            task_role=frontend_task_role,
            execution_role=frontend_execution_role,
            cpu=512,
            memory_limit_mib=1024
        )

        # Add container to frontend task definition
        frontend_container = frontend_task_definition.add_container(
            "gara-frontend-container",
            image=ecs.ContainerImage.from_registry("nginx:alpine"),
            logging=ecs.LogDrivers.aws_logs(
                log_group=frontend_log_group,
                stream_prefix="gara-frontend"
            ),
            port_mappings=[
                ecs.PortMapping(
                    container_port=80,  # Next.js port standardized to 80
                    protocol=ecs.Protocol.TCP
                )
            ],
            environment={
                "NEXT_PUBLIC_API_URL": f"http://{fargate_service.load_balancer.load_balancer_dns_name}",
                "NEXTAUTH_SECRET": "change-me-in-production",
                "S3_BUCKET_NAME": image_bucket.bucket_name,
                "AWS_REGION": self.region,
            },
            secrets={
                "GARA_API_KEY": ecs.Secret.from_secrets_manager(api_key_secret)
            }
        )

        # Create Fargate Frontend ECS Service with Application Load Balancer
        frontend_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "GaraFrontendService",
            cluster=cluster,
            service_name="gara-frontend-service",
            task_definition=frontend_task_definition,
            desired_count=1,
            public_load_balancer=True,
            listener_port=80,
            health_check_grace_period=Duration.seconds(60)
        )

        # Configure health check for the frontend target group
        frontend_service.target_group.configure_health_check(
            path="/",
            healthy_http_codes="200-399",
            interval=Duration.seconds(60),
            timeout=Duration.seconds(10),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3
        )

        # Update frontend container with NEXTAUTH_URL (set after service is created to get ALB DNS)
        frontend_container.add_environment(
            "NEXTAUTH_URL",
            f"http://{frontend_service.load_balancer.load_balancer_dns_name}"
        )

        # Create Backend CodePipeline for gara-image
        backend_pipeline = codepipeline.Pipeline(
            self, "GaraBackendPipeline",
            pipeline_name="gara-backend-pipeline",
            restart_execution_on_update=True
        )

        # Backend Source stage
        backend_source_output = codepipeline.Artifact()
        backend_source_action = codepipeline_actions.GitHubSourceAction(
            action_name="GitHub_Source",
            owner="anhydrous99",
            repo="gara-image",
            oauth_token=github_secret.secret_value_from_json("github"),
            output=backend_source_output,
            branch="main",
            trigger=codepipeline_actions.GitHubTrigger.WEBHOOK
        )

        backend_pipeline.add_stage(
            stage_name="Source",
            actions=[backend_source_action]  # type: ignore
        )

        # Backend Build stage
        backend_build_output = codepipeline.Artifact()
        backend_build_action = codepipeline_actions.CodeBuildAction(
            action_name="Build",
            project=backend_build_project,  # type: ignore
            input=backend_source_output,
            outputs=[backend_build_output]
        )

        backend_pipeline.add_stage(
            stage_name="Build",
            actions=[backend_build_action]  # type: ignore
        )

        # Backend Deploy stage
        deploy_backend_action = codepipeline_actions.EcsDeployAction(
            action_name="DeployBackend",
            service=fargate_service.service,
            deployment_timeout=Duration.minutes(10),
            image_file=codepipeline.ArtifactPath(backend_build_output, "gara-image-definitions.json")
        )

        backend_pipeline.add_stage(
            stage_name="Deploy",
            actions=[deploy_backend_action]  # type: ignore
        )

        # Add dependency to ensure backend pipeline triggers after initial deployment
        backend_pipeline.node.add_dependency(fargate_service)  # type: ignore

        # Create Frontend CodePipeline for gara-frontend
        frontend_pipeline = codepipeline.Pipeline(
            self, "GaraFrontendPipeline",
            pipeline_name="gara-frontend-pipeline",
            restart_execution_on_update=True
        )

        # Frontend Source stage
        frontend_source_output = codepipeline.Artifact()
        frontend_source_action = codepipeline_actions.GitHubSourceAction(
            action_name="GitHub_Source",
            owner="anhydrous99",
            repo="gara-frontend",
            oauth_token=github_secret.secret_value_from_json("github"),
            output=frontend_source_output,
            branch="main",
            trigger=codepipeline_actions.GitHubTrigger.WEBHOOK
        )

        frontend_pipeline.add_stage(
            stage_name="Source",
            actions=[frontend_source_action]  # type: ignore
        )

        # Frontend Build stage
        frontend_build_output = codepipeline.Artifact()
        frontend_build_action = codepipeline_actions.CodeBuildAction(
            action_name="Build",
            project=frontend_build_project,  # type: ignore
            input=frontend_source_output,
            outputs=[frontend_build_output]
        )

        frontend_pipeline.add_stage(
            stage_name="Build",
            actions=[frontend_build_action]  # type: ignore
        )

        # Frontend Deploy stage
        deploy_frontend_action = codepipeline_actions.EcsDeployAction(
            action_name="DeployFrontend",
            service=frontend_service.service,
            deployment_timeout=Duration.minutes(10),
            image_file=codepipeline.ArtifactPath(frontend_build_output, "gara-frontend-definitions.json")
        )

        frontend_pipeline.add_stage(
            stage_name="Deploy",
            actions=[deploy_frontend_action]  # type: ignore
        )

        # Add dependency to ensure frontend pipeline triggers after initial deployment
        frontend_pipeline.node.add_dependency(frontend_service)  # type: ignore

        # Create custom resource to trigger the backend pipeline on stack creation
        backend_trigger_resource = cr.AwsCustomResource(
            self, "TriggerBackendPipelineResource",
            on_create=cr.AwsSdkCall(
                service="CodePipeline",
                action="startPipelineExecution",
                parameters={
                    "name": backend_pipeline.pipeline_name
                },
                physical_resource_id=cr.PhysicalResourceId.of("trigger-backend-pipeline-initial")
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    actions=["codepipeline:StartPipelineExecution"],
                    resources=[backend_pipeline.pipeline_arn]
                )
            ])
        )

        # Ensure the custom resource runs after the backend pipeline is created
        backend_trigger_resource.node.add_dependency(backend_pipeline)  # type: ignore

        # Create custom resource to trigger the frontend pipeline on stack creation
        frontend_trigger_resource = cr.AwsCustomResource(
            self, "TriggerFrontendPipelineResource",
            on_create=cr.AwsSdkCall(
                service="CodePipeline",
                action="startPipelineExecution",
                parameters={
                    "name": frontend_pipeline.pipeline_name
                },
                physical_resource_id=cr.PhysicalResourceId.of("trigger-frontend-pipeline-initial")
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    actions=["codepipeline:StartPipelineExecution"],
                    resources=[frontend_pipeline.pipeline_arn]
                )
            ])
        )

        # Ensure the custom resource runs after the frontend pipeline is created
        frontend_trigger_resource.node.add_dependency(frontend_pipeline)  # type: ignore

        # Output the Backend Load Balancer URL
        CfnOutput(
            self, "BackendLoadBalancerDNS",
            value=fargate_service.load_balancer.load_balancer_dns_name,
            description="URL of the Application Load Balancer for gara-image service"
        )

        # Output the Frontend Load Balancer URL
        CfnOutput(
            self, "FrontendLoadBalancerDNS",
            value=frontend_service.load_balancer.load_balancer_dns_name,
            description="URL of the Application Load Balancer for gara-frontend service"
        )

        # Output the ECR Repository URI
        CfnOutput(
            self, "ECRRepositoryURI",
            value=ecr_repo.repository_uri,
            description="URI of the ECR repository for gara-image"
        )

        # Output the Frontend ECR Repository URI
        CfnOutput(
            self, "FrontendECRRepositoryURI",
            value=frontend_ecr_repo.repository_uri,
            description="URI of the ECR repository for gara-frontend"
        )

        # Output the S3 bucket name
        CfnOutput(
            self, "ImageBucketName",
            value=image_bucket.bucket_name,
            description="Name of the S3 bucket for image storage"
        )

        # Output the DynamoDB table name
        CfnOutput(
            self, "AlbumsTableName",
            value=albums_table.table_name,
            description="DynamoDB table name for albums"
        )
