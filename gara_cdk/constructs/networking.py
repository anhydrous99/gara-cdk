"""Networking construct for VPC and related resources"""
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from gara_cdk.config import VpcConfig


class NetworkingConstruct(Construct):
    """
    Construct for creating VPC and networking infrastructure.

    Creates a VPC with public and private subnets across multiple availability zones,
    NAT gateway for private subnet egress, and internet gateway for public access.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: VpcConfig
    ) -> None:
        """
        Initialize the networking construct.

        Args:
            scope: Parent construct
            construct_id: Unique identifier for this construct
            config: VPC configuration settings
        """
        super().__init__(scope, construct_id)

        self._vpc = ec2.Vpc(
            self, "Vpc",
            max_azs=config.max_azs,
            nat_gateways=config.nat_gateways,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=config.public_subnet_cidr_mask
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=config.private_subnet_cidr_mask
                )
            ],
            vpc_name=config.vpc_name
        )

    @property
    def vpc(self) -> ec2.Vpc:
        """Get the VPC resource"""
        return self._vpc
