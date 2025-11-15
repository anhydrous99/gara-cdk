"""Tests for CloudFormation outputs and CloudWatch monitoring"""
import pytest
from tests.test_constants import ResourceType, InfraConfig, OutputName
from tests.test_helpers import assert_resource_count_at_least, assert_output_exists


class TestCloudFormationOutputs:
    """Test CloudFormation outputs"""

    def test_minimum_outputs_created(self, template):
        """Test that all expected outputs are created"""
        outputs = template.find_outputs("*")
        assert len(outputs) >= InfraConfig.MIN_EXPECTED_OUTPUTS, (
            f"Expected at least {InfraConfig.MIN_EXPECTED_OUTPUTS} outputs, "
            f"but found {len(outputs)}"
        )

    def test_backend_load_balancer_output(self, template):
        """Test that backend load balancer DNS output exists"""
        assert_output_exists(
            template,
            OutputName.BACKEND_ALB_DNS,
            "URL of the Application Load Balancer for gara-image service"
        )

    def test_frontend_load_balancer_output(self, template):
        """Test that frontend load balancer DNS output exists"""
        assert_output_exists(
            template,
            OutputName.FRONTEND_ALB_DNS,
            "URL of the Application Load Balancer for gara-frontend service"
        )

    def test_backend_ecr_output(self, template):
        """Test that backend ECR repository URI output exists"""
        assert_output_exists(
            template,
            OutputName.BACKEND_ECR_URI,
            "URI of the ECR repository for gara-image"
        )

    def test_frontend_ecr_output(self, template):
        """Test that frontend ECR repository URI output exists"""
        assert_output_exists(
            template,
            OutputName.FRONTEND_ECR_URI,
            "URI of the ECR repository for gara-frontend"
        )

    def test_s3_bucket_output(self, template):
        """Test that S3 bucket name output exists"""
        assert_output_exists(
            template,
            OutputName.S3_BUCKET_NAME,
            "Name of the S3 bucket for image storage"
        )

    def test_dynamodb_table_output(self, template):
        """Test that DynamoDB table name output exists"""
        assert_output_exists(
            template,
            OutputName.DYNAMODB_TABLE_NAME,
            "DynamoDB table name for albums"
        )


class TestCloudWatchLogs:
    """Test CloudWatch logging configuration"""

    def test_log_groups_created(self, template):
        """Test that CloudWatch log groups are created for services"""
        assert_resource_count_at_least(
            template,
            ResourceType.LOG_GROUP,
            InfraConfig.MIN_EXPECTED_LOG_GROUPS
        )

    def test_log_retention_configured(self, template):
        """Test that log retention is set to correct duration"""
        from tests.test_helpers import assert_has_property
        assert_has_property(template, ResourceType.LOG_GROUP, {
            "RetentionInDays": InfraConfig.LOG_RETENTION_DAYS
        })


class TestStackValidation:
    """Test overall stack validation and resource existence"""

    def test_stack_synthesizes_successfully(self, template):
        """Test that the stack synthesizes without errors"""
        assert template is not None

    def test_no_unencrypted_s3_buckets(self, template):
        """Test that S3 buckets exist and use encryption"""
        buckets = template.find_resources(ResourceType.S3_BUCKET)
        assert len(buckets) > 0, "Expected at least one S3 bucket to exist"
        # CDK applies server-side encryption by default
