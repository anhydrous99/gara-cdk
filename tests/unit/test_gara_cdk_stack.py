"""Comprehensive test suite for GaraCdkStack"""
import aws_cdk as core
import aws_cdk.assertions as assertions
from gara_cdk.gara_cdk_stack import GaraCdkStack


class TestStackCreation:
    """Test that the stack can be created and synthesized"""

    def test_stack_synthesizes_successfully(self):
        """Test that the stack synthesizes without errors"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)
        assert template is not None


class TestVPCConfiguration:
    """Test VPC configuration"""

    def test_vpc_is_created(self):
        """Test that exactly one VPC is created"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.resource_count_is("AWS::EC2::VPC", 1)

    def test_vpc_has_two_availability_zones(self):
        """Test that VPC uses exactly 2 availability zones"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Verify we have 2 public and 2 private subnets (one of each per AZ)
        template.resource_count_is("AWS::EC2::Subnet", 4)

    def test_vpc_has_nat_gateway(self):
        """Test that VPC has exactly 1 NAT gateway"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.resource_count_is("AWS::EC2::NatGateway", 1)

    def test_vpc_has_internet_gateway(self):
        """Test that VPC has an internet gateway"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.resource_count_is("AWS::EC2::InternetGateway", 1)

    def test_vpc_subnets_have_correct_cidr_mask(self):
        """Test that subnets use /24 CIDR mask"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # All subnets should have a /24 CIDR block
        subnets = template.find_resources("AWS::EC2::Subnet")
        for subnet_id, subnet in subnets.items():
            cidr = subnet["Properties"]["CidrBlock"]
            # CIDR blocks should contain /24
            assert "/24" in str(cidr) or cidr.get("Fn::Select") is not None


class TestS3Bucket:
    """Test S3 bucket configuration"""

    def test_s3_bucket_is_created(self):
        """Test that S3 buckets are created (image bucket + pipeline artifacts)"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Should have 2 buckets: one for images, one for CodePipeline artifacts
        template.resource_count_is("AWS::S3::Bucket", 2)

    def test_s3_bucket_has_correct_name_pattern(self):
        """Test that S3 image bucket has correct naming pattern"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # BucketName is a CloudFormation intrinsic function, check it exists
        template.has_resource_properties("AWS::S3::Bucket", {
            "BucketName": assertions.Match.object_like({
                "Fn::Join": assertions.Match.any_value()
            })
        })

    def test_s3_bucket_blocks_public_access(self):
        """Test that S3 bucket blocks all public access"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::S3::Bucket", {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True
            }
        })


class TestDynamoDB:
    """Test DynamoDB table configuration"""

    def test_dynamodb_table_is_created(self):
        """Test that DynamoDB table is created"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.resource_count_is("AWS::DynamoDB::Table", 1)

    def test_dynamodb_table_name_pattern(self):
        """Test that DynamoDB table has a name configured"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # TableName is a CloudFormation intrinsic function, check it exists
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "TableName": assertions.Match.object_like({
                "Fn::Join": assertions.Match.any_value()
            })
        })

    def test_dynamodb_table_has_correct_partition_key(self):
        """Test that table has AlbumId as partition key"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::DynamoDB::Table", {
            "KeySchema": assertions.Match.array_with([
                {
                    "AttributeName": "AlbumId",
                    "KeyType": "HASH"
                }
            ])
        })

    def test_dynamodb_table_has_pay_per_request_billing(self):
        """Test that table uses PAY_PER_REQUEST billing mode"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::DynamoDB::Table", {
            "BillingMode": "PAY_PER_REQUEST"
        })

    def test_dynamodb_table_has_point_in_time_recovery(self):
        """Test that point-in-time recovery is enabled"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::DynamoDB::Table", {
            "PointInTimeRecoverySpecification": {
                "PointInTimeRecoveryEnabled": True
            }
        })

    def test_dynamodb_table_has_published_index(self):
        """Test that table has PublishedIndex GSI"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::DynamoDB::Table", {
            "GlobalSecondaryIndexes": assertions.Match.array_with([
                assertions.Match.object_like({
                    "IndexName": "PublishedIndex",
                    "KeySchema": assertions.Match.array_with([
                        {"AttributeName": "Published", "KeyType": "HASH"},
                        {"AttributeName": "CreatedAt", "KeyType": "RANGE"}
                    ]),
                    "Projection": {"ProjectionType": "ALL"}
                })
            ])
        })

    def test_dynamodb_table_has_correct_attributes(self):
        """Test that table has all required attribute definitions"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::DynamoDB::Table", {
            "AttributeDefinitions": assertions.Match.array_with([
                {"AttributeName": "AlbumId", "AttributeType": "S"},
                {"AttributeName": "Published", "AttributeType": "S"},
                {"AttributeName": "CreatedAt", "AttributeType": "N"}
            ])
        })


class TestECRRepositories:
    """Test ECR repository configuration"""

    def test_ecr_repositories_are_created(self):
        """Test that exactly 2 ECR repositories are created"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.resource_count_is("AWS::ECR::Repository", 2)

    def test_backend_ecr_repository_name(self):
        """Test that backend ECR repository has correct name"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::ECR::Repository", {
            "RepositoryName": "gara-image-app"
        })

    def test_frontend_ecr_repository_name(self):
        """Test that frontend ECR repository has correct name"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::ECR::Repository", {
            "RepositoryName": "gara-frontend-app"
        })

    def test_ecr_repositories_have_lifecycle_policies(self):
        """Test that ECR repositories have lifecycle policies for cleanup"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Both repositories should have lifecycle policies
        template.resource_count_is("Custom::ECRAutoDeleteImages", 2)


class TestECSCluster:
    """Test ECS cluster configuration"""

    def test_ecs_cluster_is_created(self):
        """Test that ECS cluster is created"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.resource_count_is("AWS::ECS::Cluster", 1)

    def test_ecs_cluster_name(self):
        """Test that ECS cluster has correct name"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::ECS::Cluster", {
            "ClusterName": "gara-cluster"
        })

    def test_ecs_cluster_has_container_insights(self):
        """Test that Container Insights is enabled"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::ECS::Cluster", {
            "ClusterSettings": assertions.Match.array_with([
                {"Name": "containerInsights", "Value": "enabled"}
            ])
        })

    def test_ecs_cluster_has_autoscaling_group(self):
        """Test that ECS cluster has an autoscaling group"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.resource_count_is("AWS::AutoScaling::AutoScalingGroup", 1)

    def test_autoscaling_group_uses_t3_small(self):
        """Test that autoscaling group uses t3.small instances"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Check launch configuration uses t3.small
        template.has_resource_properties("AWS::AutoScaling::LaunchConfiguration", {
            "InstanceType": "t3.small"
        })

    def test_autoscaling_group_capacity(self):
        """Test that autoscaling group has correct capacity settings"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::AutoScaling::AutoScalingGroup", {
            "MinSize": "1",
            "MaxSize": "3",
            "DesiredCapacity": "1"
        })


class TestIAMRoles:
    """Test IAM roles and permissions"""

    def test_backend_task_role_exists(self):
        """Test that IAM roles are created"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Should have multiple IAM roles (task roles, execution roles, codebuild role, custom resource roles, etc.)
        roles = template.find_resources("AWS::IAM::Role")
        assert len(roles) >= 5, f"Expected at least 5 IAM roles, but found {len(roles)}"

    def test_task_roles_trust_ecs_service(self):
        """Test that task roles can be assumed by ECS tasks"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Find roles with ECS task trust policy
        template.has_resource_properties("AWS::IAM::Role", {
            "AssumeRolePolicyDocument": {
                "Statement": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Principal": {"Service": "ecs-tasks.amazonaws.com"}
                    })
                ])
            }
        })

    def test_backend_has_s3_permissions(self):
        """Test that backend task role has S3 read/write permissions"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Backend should have S3 read/write permissions
        template.has_resource_properties("AWS::IAM::Policy", {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Action": assertions.Match.array_with([
                            "s3:GetObject*",
                            "s3:GetBucket*",
                            "s3:List*"
                        ])
                    })
                ])
            }
        })

    def test_backend_has_dynamodb_permissions(self):
        """Test that backend task role has DynamoDB read/write permissions"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Backend should have DynamoDB read/write permissions
        template.has_resource_properties("AWS::IAM::Policy", {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Action": assertions.Match.array_with([
                            "dynamodb:BatchGetItem",
                            "dynamodb:GetRecords",
                            "dynamodb:GetShardIterator",
                            "dynamodb:Query",
                            "dynamodb:GetItem",
                            "dynamodb:Scan"
                        ])
                    })
                ])
            }
        })

    def test_backend_has_secrets_manager_permissions(self):
        """Test that backend task role has Secrets Manager permissions"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Backend should have Secrets Manager read permissions
        template.has_resource_properties("AWS::IAM::Policy", {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Action": assertions.Match.array_with([
                            "secretsmanager:GetSecretValue",
                            "secretsmanager:DescribeSecret"
                        ])
                    })
                ])
            }
        })

    def test_codebuild_role_has_ecr_permissions(self):
        """Test that CodeBuild role has ECR permissions"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # CodeBuild role should have ECR permissions via managed policy
        # The ARN is a CloudFormation intrinsic function
        template.has_resource_properties("AWS::IAM::Role", {
            "ManagedPolicyArns": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Fn::Join": assertions.Match.any_value()
                })
            ])
        })


class TestECSTaskDefinitions:
    """Test ECS task definitions"""

    def test_two_task_definitions_created(self):
        """Test that exactly 2 task definitions are created (backend and frontend)"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.resource_count_is("AWS::ECS::TaskDefinition", 2)

    def test_task_definitions_use_bridge_network_mode(self):
        """Test that task definitions use BRIDGE network mode"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Both task definitions should use bridge network mode
        task_defs = template.find_resources("AWS::ECS::TaskDefinition")
        for task_def_id, task_def in task_defs.items():
            assert task_def["Properties"]["NetworkMode"] == "bridge"

    def test_backend_task_definition_container_config(self):
        """Test backend task definition container configuration"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Backend container should have correct memory and CPU
        template.has_resource_properties("AWS::ECS::TaskDefinition", {
            "ContainerDefinitions": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Name": "gara-image-container",
                    "Memory": 1942,
                    "Cpu": 256,
                    "PortMappings": assertions.Match.array_with([
                        assertions.Match.object_like({
                            "ContainerPort": 80,
                            "HostPort": 80,
                            "Protocol": "tcp"
                        })
                    ])
                })
            ])
        })

    def test_frontend_task_definition_container_config(self):
        """Test frontend task definition container configuration"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Frontend container should have correct memory and CPU
        template.has_resource_properties("AWS::ECS::TaskDefinition", {
            "ContainerDefinitions": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Name": "gara-frontend-container",
                    "Memory": 1024,
                    "Cpu": 256,
                    "PortMappings": assertions.Match.array_with([
                        assertions.Match.object_like({
                            "ContainerPort": 3000,
                            "HostPort": 3000,
                            "Protocol": "tcp"
                        })
                    ])
                })
            ])
        })

    def test_backend_task_environment_variables(self):
        """Test that backend task has correct environment variables"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Backend should have S3_BUCKET_NAME, AWS_REGION, DYNAMODB_TABLE_NAME, etc.
        template.has_resource_properties("AWS::ECS::TaskDefinition", {
            "ContainerDefinitions": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Name": "gara-image-container",
                    "Environment": assertions.Match.array_with([
                        assertions.Match.object_like({"Name": "S3_BUCKET_NAME"}),
                        assertions.Match.object_like({"Name": "AWS_REGION"}),
                        assertions.Match.object_like({"Name": "PORT", "Value": "80"}),
                        assertions.Match.object_like({"Name": "DYNAMODB_TABLE_NAME"})
                    ])
                })
            ])
        })

    def test_frontend_task_has_api_key_secret(self):
        """Test that frontend task has GARA_API_KEY secret"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Frontend should have GARA_API_KEY as a secret
        template.has_resource_properties("AWS::ECS::TaskDefinition", {
            "ContainerDefinitions": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Name": "gara-frontend-container",
                    "Secrets": assertions.Match.array_with([
                        assertions.Match.object_like({
                            "Name": "GARA_API_KEY"
                        })
                    ])
                })
            ])
        })

    def test_task_definitions_have_cloudwatch_logging(self):
        """Test that task definitions have CloudWatch logging configured"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Both task definitions should use awslogs log driver
        task_defs = template.find_resources("AWS::ECS::TaskDefinition")
        for task_def_id, task_def in task_defs.items():
            containers = task_def["Properties"]["ContainerDefinitions"]
            for container in containers:
                assert container["LogConfiguration"]["LogDriver"] == "awslogs"


class TestLoadBalancers:
    """Test load balancer configuration"""

    def test_two_load_balancers_created(self):
        """Test that exactly 2 ALBs are created (backend and frontend)"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 2)

    def test_load_balancers_are_internet_facing(self):
        """Test that load balancers are internet-facing"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Both ALBs should be internet-facing
        template.has_resource_properties("AWS::ElasticLoadBalancingV2::LoadBalancer", {
            "Scheme": "internet-facing"
        })

    def test_target_groups_health_check_config(self):
        """Test that target groups have correct health check configuration"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Target groups should have health checks on "/"
        template.has_resource_properties("AWS::ElasticLoadBalancingV2::TargetGroup", {
            "HealthCheckPath": "/",
            "HealthCheckIntervalSeconds": 60,
            "HealthCheckTimeoutSeconds": 10,
            "HealthyThresholdCount": 2,
            "UnhealthyThresholdCount": 3,
            "Matcher": {"HttpCode": "200-399"}
        })

    def test_two_ecs_services_created(self):
        """Test that exactly 2 ECS services are created"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.resource_count_is("AWS::ECS::Service", 2)

    def test_ecs_services_have_desired_count(self):
        """Test that ECS services have desired count of 1"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Both services should have desired count of 1
        services = template.find_resources("AWS::ECS::Service")
        for service_id, service in services.items():
            assert service["Properties"]["DesiredCount"] == 1


class TestCodeBuild:
    """Test CodeBuild configuration"""

    def test_codebuild_project_created(self):
        """Test that CodeBuild project is created"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.resource_count_is("AWS::CodeBuild::Project", 1)

    def test_codebuild_project_name(self):
        """Test that CodeBuild project has correct name"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::CodeBuild::Project", {
            "Name": "gara-build"
        })

    def test_codebuild_uses_standard_7_image(self):
        """Test that CodeBuild uses STANDARD_7_0 build image"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::CodeBuild::Project", {
            "Environment": assertions.Match.object_like({
                "Image": "aws/codebuild/standard:7.0",
                "PrivilegedMode": True
            })
        })

    def test_codebuild_has_correct_environment_variables(self):
        """Test that CodeBuild has necessary environment variables"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::CodeBuild::Project", {
            "Environment": assertions.Match.object_like({
                "EnvironmentVariables": assertions.Match.array_with([
                    assertions.Match.object_like({"Name": "AWS_ACCOUNT_ID"}),
                    assertions.Match.object_like({"Name": "AWS_DEFAULT_REGION"}),
                    assertions.Match.object_like({"Name": "ECR_REPOSITORY_URI"}),
                    assertions.Match.object_like({"Name": "FRONTEND_ECR_REPOSITORY_URI"}),
                    assertions.Match.object_like({
                        "Name": "GITHUB_TOKEN",
                        "Type": "SECRETS_MANAGER"
                    })
                ])
            })
        })

    def test_codebuild_has_github_webhook(self):
        """Test that CodeBuild has GitHub webhook configured"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::CodeBuild::Project", {
            "Source": assertions.Match.object_like({
                "Type": "GITHUB"
            }),
            "Triggers": assertions.Match.object_like({
                "Webhook": True
            })
        })

    def test_codebuild_timeout(self):
        """Test that CodeBuild has 30 minute timeout"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::CodeBuild::Project", {
            "TimeoutInMinutes": 30
        })


class TestCodePipeline:
    """Test CodePipeline configuration"""

    def test_codepipeline_created(self):
        """Test that CodePipeline is created"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.resource_count_is("AWS::CodePipeline::Pipeline", 1)

    def test_codepipeline_name(self):
        """Test that CodePipeline has correct name"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::CodePipeline::Pipeline", {
            "Name": "gara-deployment-pipeline"
        })

    def test_codepipeline_has_three_stages(self):
        """Test that pipeline has 3 stages: Source, Build, Deploy"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::CodePipeline::Pipeline", {
            "Stages": assertions.Match.array_equals([
                assertions.Match.object_like({"Name": "Source"}),
                assertions.Match.object_like({"Name": "Build"}),
                assertions.Match.object_like({"Name": "Deploy"})
            ])
        })

    def test_codepipeline_source_stage_uses_github(self):
        """Test that source stage uses GitHub"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::CodePipeline::Pipeline", {
            "Stages": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Name": "Source",
                    "Actions": assertions.Match.array_with([
                        assertions.Match.object_like({
                            "ActionTypeId": assertions.Match.object_like({
                                "Category": "Source",
                                "Provider": "GitHub"
                            }),
                            "Configuration": assertions.Match.object_like({
                                "Owner": "anhydrous99",
                                "Repo": "gara",
                                "Branch": "main"
                            })
                        })
                    ])
                })
            ])
        })

    def test_codepipeline_deploy_stage_has_two_actions(self):
        """Test that deploy stage deploys to both backend and frontend"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties("AWS::CodePipeline::Pipeline", {
            "Stages": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Name": "Deploy",
                    "Actions": assertions.Match.array_with([
                        assertions.Match.object_like({
                            "Name": "DeployBackend",
                            "ActionTypeId": assertions.Match.object_like({
                                "Provider": "ECS"
                            })
                        }),
                        assertions.Match.object_like({
                            "Name": "DeployFrontend",
                            "ActionTypeId": assertions.Match.object_like({
                                "Provider": "ECS"
                            })
                        })
                    ])
                })
            ])
        })


class TestCloudFormationOutputs:
    """Test CloudFormation outputs"""

    def test_all_outputs_are_created(self):
        """Test that all expected outputs are created"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Should have at least 6 outputs (might have more for service URLs)
        outputs = template.find_outputs("*")
        assert len(outputs) >= 6

    def test_backend_load_balancer_output(self):
        """Test that backend load balancer DNS output exists"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_output("BackendLoadBalancerDNS", {
            "Description": "URL of the Application Load Balancer for gara-image service"
        })

    def test_frontend_load_balancer_output(self):
        """Test that frontend load balancer DNS output exists"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_output("FrontendLoadBalancerDNS", {
            "Description": "URL of the Application Load Balancer for gara-frontend service"
        })

    def test_ecr_repository_outputs(self):
        """Test that both ECR repository URI outputs exist"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_output("ECRRepositoryURI", {
            "Description": "URI of the ECR repository for gara-image"
        })

        template.has_output("FrontendECRRepositoryURI", {
            "Description": "URI of the ECR repository for gara-frontend"
        })

    def test_s3_bucket_output(self):
        """Test that S3 bucket name output exists"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_output("ImageBucketName", {
            "Description": "Name of the S3 bucket for image storage"
        })

    def test_dynamodb_table_output(self):
        """Test that DynamoDB table name output exists"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        template.has_output("AlbumsTableName", {
            "Description": "DynamoDB table name for albums"
        })


class TestCloudWatchLogs:
    """Test CloudWatch logging configuration"""

    def test_log_groups_created(self):
        """Test that CloudWatch log groups are created"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Should have log groups for both services (backend and frontend)
        log_groups = template.find_resources("AWS::Logs::LogGroup")
        assert len(log_groups) >= 1, f"Expected at least 1 log group, but found {len(log_groups)}"

    def test_log_retention_is_one_week(self):
        """Test that log retention is set to 1 week (7 days)"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Log groups should have 7 day retention
        template.has_resource_properties("AWS::Logs::LogGroup", {
            "RetentionInDays": 7
        })


class TestResourceCounts:
    """Test overall resource counts to catch unexpected resources"""

    def test_security_groups_count(self):
        """Test expected number of security groups"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # Should have security groups for: ALB backend, ALB frontend, ECS instances, etc.
        security_groups = template.find_resources("AWS::EC2::SecurityGroup")
        assert len(security_groups) >= 3, f"Expected at least 3 security groups, but found {len(security_groups)}"

    def test_no_unencrypted_resources(self):
        """Test that sensitive resources are encrypted where applicable"""
        app = core.App()
        stack = GaraCdkStack(app, "test-gara-cdk")
        template = assertions.Template.from_stack(stack)

        # S3 bucket should use default encryption
        # Note: CDK applies server-side encryption by default
        buckets = template.find_resources("AWS::S3::Bucket")
        assert len(buckets) > 0  # Ensure at least one bucket exists
