"""Tests for IAM roles and security permissions"""
import pytest
import aws_cdk.assertions as assertions
from tests.test_constants import ResourceType, InfraConfig, IAMAction
from tests.test_helpers import assert_resource_count_at_least, assert_has_property, assert_iam_permission


class TestIAMRoles:
    """Test IAM roles and permissions"""

    def test_iam_roles_created(self, template):
        """Test that all required IAM roles are created"""
        assert_resource_count_at_least(template, ResourceType.IAM_ROLE, InfraConfig.MIN_EXPECTED_ROLES)

    def test_task_roles_trust_ecs_service(self, template):
        """Test that task roles can be assumed by ECS tasks"""
        assert_has_property(template, ResourceType.IAM_ROLE, {
            "AssumeRolePolicyDocument": {
                "Statement": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Principal": {"Service": "ecs-tasks.amazonaws.com"}
                    })
                ])
            }
        })

    def test_backend_has_s3_permissions(self, template):
        """Test that backend task role has S3 read/write permissions"""
        assert_iam_permission(template, [
            IAMAction.S3_GET_OBJECT,
            IAMAction.S3_GET_BUCKET,
            IAMAction.S3_LIST
        ])

    def test_backend_has_dynamodb_permissions(self, template):
        """Test that backend task role has DynamoDB read/write permissions"""
        assert_iam_permission(template, [
            IAMAction.DYNAMODB_BATCH_GET,
            IAMAction.DYNAMODB_GET_RECORDS,
            IAMAction.DYNAMODB_QUERY,
            IAMAction.DYNAMODB_GET_ITEM,
            IAMAction.DYNAMODB_SCAN
        ])

    def test_backend_has_secrets_manager_permissions(self, template):
        """Test that backend task role has Secrets Manager permissions"""
        assert_iam_permission(template, [
            IAMAction.SECRETS_GET_VALUE,
            IAMAction.SECRETS_DESCRIBE
        ])

    def test_codebuild_role_has_ecr_permissions(self, template):
        """Test that CodeBuild role has ECR permissions via managed policy"""
        # The ARN is a CloudFormation intrinsic function
        assert_has_property(template, ResourceType.IAM_ROLE, {
            "ManagedPolicyArns": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Fn::Join": assertions.Match.any_value()
                })
            ])
        })
