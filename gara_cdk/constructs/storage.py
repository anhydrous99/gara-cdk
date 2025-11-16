"""Storage construct for S3 and DynamoDB resources"""
from aws_cdk import (
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
    Stack
)
from constructs import Construct

from gara_cdk.config import StorageConfig


class StorageConstruct(Construct):
    """
    Construct for creating S3 and DynamoDB storage resources.

    Creates an S3 bucket for image storage and a DynamoDB table for album metadata
    with a Global Secondary Index for efficient querying of published albums.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: StorageConfig
    ) -> None:
        """
        Initialize the storage construct.

        Args:
            scope: Parent construct
            construct_id: Unique identifier for this construct
            config: Storage configuration settings
        """
        super().__init__(scope, construct_id)

        stack = Stack.of(self)

        self._image_bucket = s3.Bucket(
            self, "ImageBucket",
            bucket_name=f"{config.s3_bucket_prefix}-{stack.account}-{stack.region}",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        self._albums_table = dynamodb.Table(
            self, "AlbumsTable",
            table_name=f"{config.dynamodb_table_prefix}-{stack.account}-{stack.region}",
            partition_key=dynamodb.Attribute(
                name=config.partition_key,
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        self._albums_table.add_global_secondary_index(
            index_name=config.gsi_name,
            partition_key=dynamodb.Attribute(
                name=config.gsi_partition_key,
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name=config.gsi_sort_key,
                type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

    @property
    def image_bucket(self) -> s3.Bucket:
        """Get the S3 bucket for image storage"""
        return self._image_bucket

    @property
    def albums_table(self) -> dynamodb.Table:
        """Get the DynamoDB table for album metadata"""
        return self._albums_table
