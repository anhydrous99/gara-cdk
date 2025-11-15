# CLAUDE.md - AI Assistant Guide for Gara CDK Project

## Project Overview

**Project Name:** Gara CDK Infrastructure
**Type:** Infrastructure as Code (IaC) using AWS CDK
**Language:** Python 3
**Framework:** AWS Cloud Development Kit (CDK) v2.213.0
**Purpose:** Defines and deploys complete AWS infrastructure for the Gara containerized application with automated CI/CD pipeline

### What is Gara?

Gara is a containerized application with:
- **Backend Service** (`gara-image`): Image processing/storage service
- **Frontend Service** (`gara-frontend`): Web frontend application
- **Storage**: S3 for images, DynamoDB for album metadata
- **Deployment**: Fully automated CI/CD pipeline from GitHub to ECS

## Repository Structure

```
/home/user/gara-cdk/
├── app.py                          # CDK application entry point (28 lines)
├── cdk.json                        # CDK Toolkit configuration with feature flags
├── requirements.txt                # Production Python dependencies
├── requirements-dev.txt            # Development dependencies (pytest)
├── source.bat                      # Windows virtualenv activation helper
├── README.md                       # Standard CDK setup documentation
├── .gitignore                      # Python/CDK ignore patterns
├── gara_cdk/                       # Main CDK module
│   ├── __init__.py                # Package initialization
│   └── gara_cdk_stack.py          # Main stack definition (508 lines) ⭐
└── tests/                          # Test directory
    ├── __init__.py
    └── unit/
        ├── __init__.py
        └── test_gara_cdk_stack.py # Stack unit tests (placeholder)
```

### Key Files Reference

- `app.py:10` - Stack instantiation (single stack: "GaraCdkStack")
- `gara_cdk/gara_cdk_stack.py:24` - Main infrastructure class definition
- `gara_cdk/gara_cdk_stack.py:30-46` - VPC configuration
- `gara_cdk/gara_cdk_stack.py:49-55` - S3 bucket for images
- `gara_cdk/gara_cdk_stack.py:58-83` - DynamoDB albums table with GSI
- `gara_cdk/gara_cdk_stack.py:86-99` - ECR repositories

## Infrastructure Architecture

### AWS Services Stack

| Service | Resource Name | Purpose |
|---------|--------------|---------|
| **VPC** | GaraVpc | Network isolation (2 AZs, 1 NAT gateway) |
| **S3** | `gara-images-{account}-{region}` | Image storage with block public access |
| **DynamoDB** | `gara-albums-{account}-{region}` | Album metadata with PublishedIndex GSI |
| **ECR** | `gara-image-app` | Backend Docker image repository |
| **ECR** | `gara-frontend-app` | Frontend Docker image repository |
| **ECS Cluster** | `gara-cluster` | Container orchestration (EC2 launch type) |
| **ASG** | Auto Scaling Group | t3.small instances (1-3 nodes) |
| **ALB** | Backend ALB | Load balancer for backend service |
| **ALB** | Frontend ALB | Load balancer for frontend service (port 3000) |
| **CodeBuild** | `gara-build` | Builds Docker images from GitHub |
| **CodePipeline** | `gara-deployment-pipeline` | 3-stage deployment pipeline |
| **CloudWatch** | Log Groups | Container logs (1-week retention) |
| **Secrets Manager** | GithubToken, gara-api-key | Secrets for CI/CD and API access |

### Network Architecture

- **VPC CIDR**: Auto-assigned by CDK
- **Subnets**: /24 CIDR blocks
  - Public subnets (2 AZs) - For ALBs and NAT gateway
  - Private subnets (2 AZs) - For ECS instances
- **NAT Gateway**: Single NAT for cost optimization
- **Internet Gateway**: For public subnet internet access

### Container Architecture

#### Backend Service (gara-image-service)
- **Task Definition**: EC2 with BRIDGE network mode
- **Resources**: 1942 MiB memory, 256 CPU units
- **Image**: Placeholder `nginx:alpine` until pipeline deploys
- **Port**: Dynamic host port mapping
- **Health Check**: ALB checks HTTP 200-399 status codes
- **Environment Variables**:
  - `S3_BUCKET_NAME`: Injected from S3 bucket
  - `ALBUMS_TABLE_NAME`: Injected from DynamoDB table
  - `GARA_API_KEY`: From Secrets Manager

#### Frontend Service (gara-frontend-service)
- **Task Definition**: EC2 with BRIDGE network mode
- **Resources**: 1024 MiB memory, 256 CPU units
- **Image**: Placeholder `nginx:alpine` until pipeline deploys
- **Port**: 3000 (static mapping)
- **Access**: Read-only to S3 and DynamoDB

### CI/CD Pipeline

**Trigger**: GitHub webhook on push/PR merge to `main` branch
**Source Repository**: `anhydrous99/gara` (GitHub)

**Pipeline Stages**:
1. **Source**: GitHub integration with webhook trigger
2. **Build**: CodeBuild compiles and pushes Docker images
   - Builds both `gara-image` and `gara-frontend` directories
   - Tags with commit hash and `latest`
   - Pushes to respective ECR repositories
   - 30-minute timeout
3. **Deploy**: Deploys to ECS services
   - Backend deployment
   - Frontend deployment
   - 10-minute timeout per deployment

**Initial Deployment**: Custom Lambda resource triggers first pipeline execution on stack creation

## Development Workflows

### Initial Setup

```bash
# 1. Create Python virtual environment
python3 -m venv .venv

# 2. Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate.bat  # Windows

# 3. Install production dependencies
pip install -r requirements.txt

# 4. Install development dependencies
pip install -r requirements-dev.txt

# 5. Configure AWS credentials
aws configure  # Or set AWS_PROFILE environment variable
```

### CDK Commands Reference

```bash
# List all stacks
cdk ls

# Synthesize CloudFormation template
cdk synth

# Show diff between deployed and local state
cdk diff

# Deploy to AWS (requires AWS credentials)
cdk deploy

# Deploy with automatic approval (skip confirmation)
cdk deploy --require-approval never

# Destroy the stack
cdk destroy

# Open CDK documentation
cdk docs
```

### Development Iteration

```bash
# 1. Make changes to gara_cdk/gara_cdk_stack.py
# 2. Synthesize to validate syntax
cdk synth

# 3. Preview changes
cdk diff

# 4. Deploy changes
cdk deploy
```

### Watch Mode (Development)

CDK watch mode is configured in `cdk.json`:
- **Includes**: All files (`**`)
- **Excludes**: README, cdk*.json, requirements*.txt, `__pycache__`, tests

```bash
# Auto-deploy on file changes
cdk watch
```

## Coding Conventions and Patterns

### Python Style

- **Class Names**: PascalCase (e.g., `GaraCdkStack`)
- **Variables**: snake_case (e.g., `image_bucket`, `albums_table`)
- **Construct IDs**: PascalCase (e.g., "GaraVpc", "GaraImageBucket")
- **Resource Names**: kebab-case with account/region suffix pattern
  - Example: `f"gara-images-{self.account}-{self.region}"`

### CDK Patterns Used

1. **Resource Naming Convention**:
   ```python
   bucket_name=f"gara-images-{self.account}-{self.region}"
   ```
   - Ensures uniqueness across deployments
   - Uses CDK stack context properties

2. **Removal Policies**:
   - `RemovalPolicy.DESTROY`: For development resources (S3, ECR)
   - `RemovalPolicy.RETAIN`: For data persistence (DynamoDB)

3. **IAM Principle of Least Privilege**:
   - Separate roles for each service type
   - Backend: Full access to S3, DynamoDB, Secrets Manager
   - Frontend: Read-only access to S3 and DynamoDB
   - CodeBuild: ECR push/pull only

4. **Environment Variables**:
   ```python
   environment={
       "S3_BUCKET_NAME": image_bucket.bucket_name,
       "ALBUMS_TABLE_NAME": albums_table.table_name
   }
   ```
   - Inject resource names dynamically (not hardcoded)

5. **Secrets Management**:
   ```python
   secret = secretmanager.Secret.from_secret_name_v2(
       self, "SecretId", "secret-name"
   )
   secrets={
       "SECRET_KEY": ecs.Secret.from_secrets_manager(secret)
   }
   ```
   - Use Secrets Manager for sensitive data
   - Never hardcode secrets in code

### File Organization

- **Single Stack Pattern**: All infrastructure in one stack (`GaraCdkStack`)
- **Single File Pattern**: All resources in `gara_cdk_stack.py`
- **Top-to-Bottom Dependency Order**: Resources defined in dependency order:
  1. VPC and networking
  2. Storage (S3, DynamoDB)
  3. Container repositories (ECR)
  4. Secrets and IAM roles
  5. ECS cluster and services
  6. CodeBuild and CodePipeline

## Testing Guidelines

### Unit Testing

Test files use AWS CDK assertions library:

```python
from aws_cdk import assertions

def test_resource_created():
    app = cdk.App()
    stack = GaraCdkStack(app, "test")
    template = assertions.Template.from_stack(stack)

    # Example: Check resource count
    template.resource_count_is("AWS::S3::Bucket", 1)

    # Example: Check resource properties
    template.has_resource_properties("AWS::S3::Bucket", {
        "BucketName": assertions.Match.string_like_regexp("gara-images-*")
    })
```

### Running Tests

```bash
# Run all unit tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_gara_cdk_stack.py
```

### Test Coverage Areas

When modifying infrastructure, ensure tests cover:
1. **Resource Creation**: Verify resources are created
2. **Resource Count**: Ensure expected number of resources
3. **Resource Properties**: Validate critical configurations
4. **IAM Policies**: Verify permissions are correct
5. **Outputs**: Check CloudFormation outputs

## Deployment Process

### Prerequisites

1. **AWS Account Setup**:
   - Valid AWS account with appropriate permissions
   - IAM user/role with CDK deployment permissions
   - AWS credentials configured locally

2. **Secrets Manager Setup** (Required before deployment):
   ```bash
   # Create GitHub token secret
   aws secretsmanager create-secret \
       --name GithubToken \
       --secret-string "ghp_your_github_token"

   # Create Gara API key secret
   aws secretsmanager create-secret \
       --name gara-api-key \
       --secret-string "your_api_key"
   ```

3. **GitHub Repository**:
   - Repository: `anhydrous99/gara`
   - Branch: `main`
   - Contains `gara-image/` and `gara-frontend/` directories
   - Each directory has a Dockerfile

### First-Time Deployment

```bash
# 1. Bootstrap CDK (one-time per account/region)
cdk bootstrap

# 2. Synthesize template (validate)
cdk synth

# 3. Deploy stack
cdk deploy
```

### Post-Deployment

After deployment:
1. **Pipeline Execution**: Custom resource triggers initial pipeline run
2. **Docker Image Build**: CodeBuild builds images from GitHub
3. **ECR Push**: Images pushed to ECR repositories
4. **ECS Deployment**: Services update with real application images
5. **First deployment takes ~10-15 minutes**

### Stack Updates

```bash
# Preview changes
cdk diff

# Deploy updates
cdk deploy

# If only application code changed, trigger pipeline manually:
aws codepipeline start-pipeline-execution \
    --name gara-deployment-pipeline
```

### Rollback

```bash
# Deploy previous version of stack
git checkout <previous-commit>
cdk deploy

# Or destroy and recreate
cdk destroy
cdk deploy
```

## Common Tasks

### Adding a New Environment Variable to Backend

1. Locate backend task definition in `gara_cdk_stack.py`
2. Add to `environment` dictionary:
   ```python
   environment={
       "S3_BUCKET_NAME": image_bucket.bucket_name,
       "ALBUMS_TABLE_NAME": albums_table.table_name,
       "NEW_VAR": "value"  # Add here
   }
   ```
3. Deploy: `cdk deploy`

### Adding a New Secret

1. Create secret in AWS Secrets Manager:
   ```bash
   aws secretsmanager create-secret \
       --name my-new-secret \
       --secret-string "secret_value"
   ```

2. Reference in stack:
   ```python
   my_secret = secretmanager.Secret.from_secret_name_v2(
       self, "MySecret", "my-new-secret"
   )
   ```

3. Add to task definition:
   ```python
   secrets={
       "MY_SECRET": ecs.Secret.from_secrets_manager(my_secret)
   }
   ```

4. Grant read permissions:
   ```python
   my_secret.grant_read(task_role)
   ```

### Modifying Container Resources

Edit task definition in `gara_cdk_stack.py`:

```python
backend_task_definition.add_container(
    "gara-image",
    memory_limit_mib=2048,  # Increase memory
    cpu=512,                # Increase CPU
    # ... other properties
)
```

### Adding DynamoDB Table or GSI

Pattern for new table:
```python
new_table = dynamodb.Table(
    self, "MyTable",
    table_name=f"my-table-{self.account}-{self.region}",
    partition_key=dynamodb.Attribute(
        name="Id",
        type=dynamodb.AttributeType.STRING
    ),
    billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
    removal_policy=RemovalPolicy.RETAIN
)

# Grant permissions to task role
new_table.grant_read_write_data(task_role)

# Add environment variable
environment={"TABLE_NAME": new_table.table_name}
```

### Changing Auto Scaling Configuration

Locate Auto Scaling Group configuration:
```python
cluster.add_capacity(
    "DefaultAutoScalingGroup",
    instance_type=ec2.InstanceType("t3.medium"),  # Change instance type
    min_capacity=2,                                # Change minimum
    max_capacity=5,                                # Change maximum
    # ... other properties
)
```

### Viewing Logs

```bash
# List log groups
aws logs describe-log-groups --log-group-name-prefix /ecs/gara

# Tail backend logs
aws logs tail /ecs/gara-image-service --follow

# Tail frontend logs
aws logs tail /ecs/gara-frontend-service --follow

# View pipeline execution
aws codepipeline get-pipeline-execution \
    --pipeline-name gara-deployment-pipeline
```

## AWS-Specific Considerations

### Account and Region Configuration

**Current**: Environment-agnostic deployment
- Stack can deploy to any account/region based on AWS credentials

**To Specialize** (edit `app.py:18` or `app.py:23`):
```python
# Option 1: Use current CLI configuration
env=cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')
)

# Option 2: Hardcode account/region
env=cdk.Environment(
    account='123456789012',
    region='us-east-1'
)
```

### Cost Optimization Notes

1. **NAT Gateway**: Single NAT gateway (~$32/month + data transfer)
   - Consider removing for dev environments
   - Use multiple NAT gateways for production HA

2. **EC2 Instances**: t3.small instances in ASG
   - Consider Fargate for variable workloads
   - Use Spot instances for cost savings (dev environments)

3. **DynamoDB**: Pay-per-request billing
   - Good for variable workloads
   - Consider provisioned capacity for predictable traffic

4. **S3**: Standard storage class
   - Consider lifecycle policies for old images
   - Use Intelligent-Tiering for variable access patterns

### Multi-Region Considerations

For multi-region deployment:
1. Deploy separate stacks per region
2. Update `app.py` to create multiple stacks
3. Consider cross-region replication for S3/DynamoDB
4. Update pipeline to deploy to multiple regions

### Security Best Practices

1. **Secrets**: Never commit secrets to version control
2. **IAM Roles**: Follow principle of least privilege
3. **VPC**: Keep ECS instances in private subnets
4. **ALB**: Consider adding WAF for production
5. **S3**: Block public access enabled (default in this stack)
6. **ECR**: Image scanning enabled automatically
7. **HTTPS**: Consider adding ACM certificates to ALBs

## Troubleshooting

### Common Issues

#### 1. CDK Deploy Fails: "Secret not found"

**Cause**: Required secrets not created in Secrets Manager
**Solution**: Create secrets before deployment:
```bash
aws secretsmanager create-secret --name GithubToken --secret-string "token"
aws secretsmanager create-secret --name gara-api-key --secret-string "key"
```

#### 2. ECS Tasks Failing to Start

**Check**:
```bash
# View task failures
aws ecs describe-tasks --cluster gara-cluster --tasks <task-id>

# Check service events
aws ecs describe-services --cluster gara-cluster --services gara-image-service
```

**Common causes**:
- Insufficient memory/CPU
- Missing environment variables
- IAM permission issues
- Container image pull failures

#### 3. Pipeline Execution Fails

**Check**:
```bash
# View pipeline execution details
aws codepipeline get-pipeline-execution --pipeline-name gara-deployment-pipeline

# View CodeBuild logs
aws codebuild batch-get-builds --ids <build-id>
```

**Common causes**:
- GitHub webhook not configured
- Missing Dockerfile in repository
- ECR push permission issues
- Build timeout (increase in stack definition)

#### 4. CDK Diff Shows Unexpected Changes

**Cause**: CDK context changes or dependency updates
**Solution**:
```bash
# Clear CDK context cache
rm cdk.context.json

# Re-synthesize
cdk synth
```

## Important Reminders for AI Assistants

### Do's ✅

1. **Always read files before editing** - Use Read tool first
2. **Validate CDK syntax** - Run `cdk synth` after changes
3. **Check dependencies** - Ensure resources are created in correct order
4. **Use resource references** - Never hardcode resource names/ARNs
5. **Follow naming conventions** - Use `{resource}-{account}-{region}` pattern
6. **Preserve IAM permissions** - Don't remove existing grants
7. **Test locally** - `cdk synth` and `cdk diff` before deploy
8. **Update tests** - Modify unit tests when changing infrastructure
9. **Consider costs** - Evaluate cost impact of changes
10. **Document changes** - Add comments for complex infrastructure

### Don'ts ❌

1. **Don't hardcode secrets** - Always use Secrets Manager
2. **Don't skip validation** - Always run `cdk synth` before deploy
3. **Don't remove resources carelessly** - Check RemovalPolicy first
4. **Don't expose sensitive data** - Keep S3 buckets private
5. **Don't create unnecessary resources** - Keep infrastructure minimal
6. **Don't ignore CDK warnings** - Address deprecation notices
7. **Don't deploy without diff** - Always preview changes with `cdk diff`
8. **Don't modify bootstrapped resources** - CDK manages these
9. **Don't use wildcards in IAM** - Be specific with permissions
10. **Don't commit `cdk.out/`** - Already in .gitignore

### When Making Changes

**Before**:
- [ ] Understand current infrastructure state
- [ ] Read relevant sections of `gara_cdk_stack.py`
- [ ] Check resource dependencies
- [ ] Review IAM permissions required

**During**:
- [ ] Make minimal, focused changes
- [ ] Add comments for complex logic
- [ ] Update environment variables if needed
- [ ] Maintain consistent naming conventions

**After**:
- [ ] Run `cdk synth` to validate
- [ ] Run `cdk diff` to preview changes
- [ ] Update unit tests if applicable
- [ ] Update this CLAUDE.md if workflow changes
- [ ] Test deployment in dev environment first

## Key Infrastructure Decisions

### Why EC2 Launch Type (Not Fargate)?
- **Cost efficiency** for constant workloads
- **Greater control** over instance types
- **Existing choice** - maintain consistency

### Why Bridge Network Mode?
- **Compatibility** with EC2 launch type
- **Dynamic port mapping** for backend
- **Container-to-host** communication

### Why Pay-Per-Request DynamoDB?
- **Variable workload** patterns
- **No capacity planning** needed
- **Cost-effective** for sporadic access

### Why Single NAT Gateway?
- **Cost optimization** (~$32/month savings)
- **Acceptable** for dev/staging environments
- **Consider multiple** for production HA

### Why Placeholder Images?
- **Stack deployment** succeeds without application code
- **Pipeline replaces** with real images after first run
- **Separation of concerns** - infrastructure vs application

## Additional Resources

### CDK Documentation
- [AWS CDK Python Reference](https://docs.aws.amazon.com/cdk/api/v2/python/)
- [CDK Best Practices](https://docs.aws.amazon.com/cdk/v2/guide/best-practices.html)
- [CDK Examples](https://github.com/aws-samples/aws-cdk-examples/tree/master/python)

### AWS Service Documentation
- [ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [CodePipeline User Guide](https://docs.aws.amazon.com/codepipeline/latest/userguide/)

### Internal References
- Main stack definition: `gara_cdk/gara_cdk_stack.py:24-508`
- CDK app entry point: `app.py:9-28`
- CDK configuration: `cdk.json`

## Version Information

- **CDK Version**: 2.213.0
- **Python Version**: 3.x (no specific version pinned)
- **Boto3 Version**: ~1.37.10
- **Pytest Version**: 6.2.5 (dev)

## Recent Changes

Based on commit history:
- `dd2f2b2`: Added DynamoDB albums table with PublishedIndex GSI
- `6cbc464`: General modifications
- `1412436`: Progressive updates
- `3e31ed2`: Initial CDK setup
- `2506204`: Repository initialization

---

**Last Updated**: 2025-11-15
**Stack Name**: GaraCdkStack
**Current Branch**: `claude/claude-md-mhzs0a90qo0fu6cy-01WhcbpZmmxMRrkvTe2MeNxc`

*This document is maintained for AI assistants working with this codebase. Update when infrastructure changes significantly.*
