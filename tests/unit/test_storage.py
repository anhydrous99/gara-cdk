"""Tests for storage services (S3 and DynamoDB)"""
import pytest
import aws_cdk.assertions as assertions
from tests.test_constants import ResourceType, InfraConfig
from tests.test_helpers import assert_resource_count, assert_has_property


class TestS3Bucket:
    """Test S3 bucket configuration"""

    def test_s3_buckets_created(self, template):
        """Test that S3 buckets are created (image bucket + pipeline artifacts)"""
        assert_resource_count(template, ResourceType.S3_BUCKET, InfraConfig.EXPECTED_S3_BUCKETS)

    def test_s3_bucket_has_naming_configuration(self, template):
        """Test that S3 image bucket has correct naming pattern"""
        # BucketName is a CloudFormation intrinsic function, check it exists
        assert_has_property(template, ResourceType.S3_BUCKET, {
            "BucketName": assertions.Match.object_like({
                "Fn::Join": assertions.Match.any_value()
            })
        })

    def test_s3_bucket_blocks_public_access(self, template):
        """Test that S3 bucket blocks all public access"""
        assert_has_property(template, ResourceType.S3_BUCKET, {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True
            }
        })


class TestDynamoDB:
    """Test DynamoDB table configuration"""

    def test_dynamodb_table_created(self, template):
        """Test that DynamoDB table is created"""
        assert_resource_count(template, ResourceType.DYNAMODB_TABLE, 1)

    def test_dynamodb_table_has_name(self, template):
        """Test that DynamoDB table has a name configured"""
        # TableName is a CloudFormation intrinsic function, check it exists
        assert_has_property(template, ResourceType.DYNAMODB_TABLE, {
            "TableName": assertions.Match.object_like({
                "Fn::Join": assertions.Match.any_value()
            })
        })

    def test_dynamodb_table_has_correct_partition_key(self, template):
        """Test that table has AlbumId as partition key"""
        assert_has_property(template, ResourceType.DYNAMODB_TABLE, {
            "KeySchema": assertions.Match.array_with([
                {
                    "AttributeName": "AlbumId",
                    "KeyType": "HASH"
                }
            ])
        })

    def test_dynamodb_table_billing_mode(self, template):
        """Test that table uses PAY_PER_REQUEST billing mode"""
        assert_has_property(template, ResourceType.DYNAMODB_TABLE, {
            "BillingMode": "PAY_PER_REQUEST"
        })

    def test_dynamodb_table_has_point_in_time_recovery(self, template):
        """Test that point-in-time recovery is enabled"""
        assert_has_property(template, ResourceType.DYNAMODB_TABLE, {
            "PointInTimeRecoverySpecification": {
                "PointInTimeRecoveryEnabled": True
            }
        })

    def test_dynamodb_table_has_published_index(self, template):
        """Test that table has PublishedIndex GSI"""
        assert_has_property(template, ResourceType.DYNAMODB_TABLE, {
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

    def test_dynamodb_table_attributes(self, template):
        """Test that table has all required attribute definitions"""
        assert_has_property(template, ResourceType.DYNAMODB_TABLE, {
            "AttributeDefinitions": assertions.Match.array_with([
                {"AttributeName": "AlbumId", "AttributeType": "S"},
                {"AttributeName": "Published", "AttributeType": "S"},
                {"AttributeName": "CreatedAt", "AttributeType": "N"}
            ])
        })
