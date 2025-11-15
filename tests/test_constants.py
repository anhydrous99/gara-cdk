"""Constants for CDK infrastructure tests"""

# CloudFormation Resource Types
class ResourceType:
    """AWS CloudFormation resource type identifiers"""
    VPC = "AWS::EC2::VPC"
    SUBNET = "AWS::EC2::Subnet"
    NAT_GATEWAY = "AWS::EC2::NatGateway"
    INTERNET_GATEWAY = "AWS::EC2::InternetGateway"
    SECURITY_GROUP = "AWS::EC2::SecurityGroup"
    LAUNCH_CONFIGURATION = "AWS::AutoScaling::LaunchConfiguration"
    AUTOSCALING_GROUP = "AWS::AutoScaling::AutoScalingGroup"

    S3_BUCKET = "AWS::S3::Bucket"
    DYNAMODB_TABLE = "AWS::DynamoDB::Table"
    ECR_REPOSITORY = "AWS::ECR::Repository"
    ECR_AUTO_DELETE = "Custom::ECRAutoDeleteImages"

    ECS_CLUSTER = "AWS::ECS::Cluster"
    ECS_TASK_DEFINITION = "AWS::ECS::TaskDefinition"
    ECS_SERVICE = "AWS::ECS::Service"

    IAM_ROLE = "AWS::IAM::Role"
    IAM_POLICY = "AWS::IAM::Policy"

    ALB = "AWS::ElasticLoadBalancingV2::LoadBalancer"
    TARGET_GROUP = "AWS::ElasticLoadBalancingV2::TargetGroup"

    CODEBUILD_PROJECT = "AWS::CodeBuild::Project"
    CODEPIPELINE = "AWS::CodePipeline::Pipeline"

    LOG_GROUP = "AWS::Logs::LogGroup"


# Infrastructure Configuration Constants
class InfraConfig:
    """Expected infrastructure configuration values"""
    # VPC
    EXPECTED_AVAILABILITY_ZONES = 2
    EXPECTED_SUBNETS = 4  # 2 public + 2 private
    EXPECTED_NAT_GATEWAYS = 1
    SUBNET_CIDR_MASK = "/24"

    # S3
    EXPECTED_S3_BUCKETS = 2  # Image bucket + Pipeline artifacts

    # ECR
    EXPECTED_ECR_REPOS = 2  # Backend + Frontend
    BACKEND_ECR_NAME = "gara-image-app"
    FRONTEND_ECR_NAME = "gara-frontend-app"

    # ECS
    ECS_CLUSTER_NAME = "gara-cluster"
    INSTANCE_TYPE = "t3.small"
    MIN_CAPACITY = "1"
    MAX_CAPACITY = "3"
    DESIRED_CAPACITY = "1"

    # Task Definitions
    EXPECTED_TASK_DEFINITIONS = 2
    BACKEND_CONTAINER_NAME = "gara-image-container"
    FRONTEND_CONTAINER_NAME = "gara-frontend-container"
    BACKEND_MEMORY = 1942
    FRONTEND_MEMORY = 1024
    CONTAINER_CPU = 256
    BACKEND_PORT = 80
    FRONTEND_PORT = 3000
    NETWORK_MODE = "bridge"

    # Load Balancers
    EXPECTED_LOAD_BALANCERS = 2
    EXPECTED_ECS_SERVICES = 2
    DESIRED_COUNT = 1

    # Health Checks
    HEALTH_CHECK_PATH = "/"
    HEALTH_CHECK_CODES = "200-399"
    HEALTH_CHECK_INTERVAL = 60
    HEALTH_CHECK_TIMEOUT = 10
    HEALTHY_THRESHOLD = 2
    UNHEALTHY_THRESHOLD = 3

    # CodeBuild
    BUILD_PROJECT_NAME = "gara-build"
    BUILD_IMAGE = "aws/codebuild/standard:7.0"
    BUILD_TIMEOUT = 30

    # CodePipeline
    PIPELINE_NAME = "gara-deployment-pipeline"
    PIPELINE_STAGES = 3
    GITHUB_OWNER = "anhydrous99"
    GITHUB_REPO = "gara"
    GITHUB_BRANCH = "main"

    # CloudWatch Logs
    LOG_RETENTION_DAYS = 7

    # Outputs
    MIN_EXPECTED_OUTPUTS = 6

    # IAM
    MIN_EXPECTED_ROLES = 5
    MIN_EXPECTED_SECURITY_GROUPS = 3
    MIN_EXPECTED_LOG_GROUPS = 1


# CloudFormation Output Names
class OutputName:
    """CloudFormation stack output identifiers"""
    BACKEND_ALB_DNS = "BackendLoadBalancerDNS"
    FRONTEND_ALB_DNS = "FrontendLoadBalancerDNS"
    BACKEND_ECR_URI = "ECRRepositoryURI"
    FRONTEND_ECR_URI = "FrontendECRRepositoryURI"
    S3_BUCKET_NAME = "ImageBucketName"
    DYNAMODB_TABLE_NAME = "AlbumsTableName"


# Environment Variable Names
class EnvVar:
    """Container environment variable names"""
    S3_BUCKET_NAME = "S3_BUCKET_NAME"
    AWS_REGION = "AWS_REGION"
    PORT = "PORT"
    DYNAMODB_TABLE_NAME = "DYNAMODB_TABLE_NAME"
    NEXT_PUBLIC_API_URL = "NEXT_PUBLIC_API_URL"
    NEXTAUTH_URL = "NEXTAUTH_URL"
    NEXTAUTH_SECRET = "NEXTAUTH_SECRET"


# IAM Permissions
class IAMAction:
    """IAM action identifiers for permission testing"""
    # S3
    S3_GET_OBJECT = "s3:GetObject*"
    S3_GET_BUCKET = "s3:GetBucket*"
    S3_LIST = "s3:List*"

    # DynamoDB
    DYNAMODB_BATCH_GET = "dynamodb:BatchGetItem"
    DYNAMODB_GET_RECORDS = "dynamodb:GetRecords"
    DYNAMODB_QUERY = "dynamodb:Query"
    DYNAMODB_GET_ITEM = "dynamodb:GetItem"
    DYNAMODB_SCAN = "dynamodb:Scan"

    # Secrets Manager
    SECRETS_GET_VALUE = "secretsmanager:GetSecretValue"
    SECRETS_DESCRIBE = "secretsmanager:DescribeSecret"
