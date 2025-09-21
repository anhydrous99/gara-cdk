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
    aws_lambda as lambda_,
    custom_resources as cr,
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
            ]
        )

        # Create ECR repository for Docker images
        ecr_repo = ecr.Repository(
            self, "GaraEcrRepo",
            repository_name="gara-app",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_images=True
        )

        # Create ECS Cluster
        cluster = ecs.Cluster(
            self, "GaraCluster",
            vpc=vpc,
            cluster_name="gara-cluster",
            container_insights=True
        )

        # Add capacity to cluster (t3.small instances)
        cluster.add_capacity(
            "GaraAutoScalingGroup",
            instance_type=ec2.InstanceType("t3.small"),
            min_capacity=1,
            max_capacity=3,
            desired_capacity=1,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            )
        )

        # Reference the existing GitHub token secret
        github_secret = secretmanager.Secret.from_secret_name_v2(
            self, "GithubToken",
            "GithubToken"
        )

        # Create IAM role for CodeBuild
        codebuild_role = iam.Role(
            self, "CodeBuidRole",
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryPowerUser")
            ]
        )

        # Grant CodeBuild access to the secret
        github_secret.grant_read(codebuild_role)

        # Add creds for building and deploying
        codebuild.GitHubSourceCredentials(
            self, "GaraCodeBuildGithubCreds",
            access_token=github_secret.secret_value_from_json('github')
        )

        # Create CodeBuild project
        build_project = codebuild.Project(
            self, "GaraBuildProject",
            project_name="gara-build",
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
                repo="gara",
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
                            "aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URI",
                            "COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)",
                            "IMAGE_TAG=${COMMIT_HASH:=latest}"
                        ]
                    },
                    "build": {
                        "commands": [
                            "echo Build started on `date`",
                            "echo Building the Docker image...",
                            "docker build -t $ECR_REPOSITORY_URI:latest .",
                            "docker tag $ECR_REPOSITORY_URI:latest $ECR_REPOSITORY_URI:$IMAGE_TAG"
                        ]
                    },
                    "post_build": {
                        "commands": [
                            "echo Build completed on `date`",
                            "echo Pushing the Docker images...",
                            "docker push $ECR_REPOSITORY_URI:latest",
                            "docker push $ECR_REPOSITORY_URI:$IMAGE_TAG",
                            "echo Writing image definitions file...",
                            "printf '[{\"name\":\"gara-container\",\"imageUri\":\"%s\"}]' $ECR_REPOSITORY_URI:latest > imagedefinitions.json"
                        ]
                    }
                },
                "artifacts": {
                    "files": ["imagedefinitions.json"]
                }
            }),
            timeout=Duration.minutes(30)
        )

        # Grant CodeBuild permissions to push to ECR
        ecr_repo.grant_pull_push(codebuild_role)

        # Create Task Definition
        task_definition = ecs.Ec2TaskDefinition(
            self, "GaraTaskDef",
            network_mode=ecs.NetworkMode.BRIDGE
        )

        # Add container to task definition
        # Use nginx as placeholder - it stays running and responds to health checks
        # The pipeline will update this with the actual image
        task_definition.add_container(
            "gara-container",
            image=ecs.ContainerImage.from_registry("nginx:alpine"),
            memory_limit_mib=1942,
            cpu=256,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="gara",
                log_retention=logs.RetentionDays.ONE_WEEK
            ),
            port_mappings=[
                ecs.PortMapping(
                    container_port=80,  # nginx listens on port 80
                    host_port=80,
                    protocol=ecs.Protocol.TCP
                )
            ]
        )

        # Create ECS Service with Application Load Balancer
        # Start with 0 desired count to avoid running placeholder
        fargate_service = ecs_patterns.ApplicationLoadBalancedEc2Service(
            self, "GaraService",
            cluster=cluster,
            service_name="gara-service",
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

        # Create CodePipeline for continuous deployment
        pipeline = codepipeline.Pipeline(
            self, "GaraPipeline",
            pipeline_name="gara-deployment-pipeline",
            restart_execution_on_update=True
        )

        # Source stage
        source_output = codepipeline.Artifact()
        source_action = codepipeline_actions.GitHubSourceAction(
            action_name="GitHub_Source",
            owner="anhydrous99",
            repo="gara",
            oauth_token=github_secret.secret_value_from_json("github"),
            output=source_output,
            branch="main",
            trigger=codepipeline_actions.GitHubTrigger.WEBHOOK
        )

        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]  # type: ignore
        )

        # Build stage
        build_output = codepipeline.Artifact()
        build_action = codepipeline_actions.CodeBuildAction(
            action_name="Build",
            project=build_project,  # type: ignore
            input=source_output,
            outputs=[build_output]
        )

        pipeline.add_stage(
            stage_name="Build",
            actions=[build_action]  # type: ignore
        )

        # Deploy stage - this will update the task definition and scale the service
        deploy_action = codepipeline_actions.EcsDeployAction(
            action_name="Deploy",
            service=fargate_service.service,
            input=build_output,
            deployment_timeout=Duration.minutes(10)
        )

        pipeline.add_stage(
            stage_name="Deploy",
            actions=[deploy_action]  # type: ignore
        )


        # Add dependency to ensure pipeline triggers after initial deployment
        pipeline.node.add_dependency(fargate_service)  # type: ignore

        # Create custom resource to trigger the pipeline on stack creation
        trigger_resource = cr.AwsCustomResource(
            self, "TriggerPipelineResource",
            on_create=cr.AwsSdkCall(
                service="CodePipeline",
                action="startPipelineExecution",
                parameters={
                    "name": pipeline.pipeline_name
                },
                physical_resource_id=cr.PhysicalResourceId.of("trigger-pipeline-initial")
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    actions=["codepipeline:StartPipelineExecution"],
                    resources=[pipeline.pipeline_arn]
                )
            ])
        )

        # Ensure the custom resource runs after the pipeline is created
        trigger_resource.node.add_dependency(pipeline)  # type: ignore

        # Output the Load Balancer URL
        CfnOutput(
            self, "LoadBalancerDNS",
            value=fargate_service.load_balancer.load_balancer_dns_name,
            description="URL of the Application Load Balancer"
        )

        # Output the ECR Repository URI
        CfnOutput(
            self, "ECRRepositoryURI",
            value=ecr_repo.repository_uri,
            description="URI of the ECR repository"
        )
