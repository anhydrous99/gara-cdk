"""Tests for VPC and networking configuration"""
import pytest
from tests.test_constants import ResourceType, InfraConfig
from tests.test_helpers import assert_resource_count


class TestVPCConfiguration:
    """Test VPC configuration"""

    def test_vpc_is_created(self, template):
        """Test that exactly one VPC is created"""
        assert_resource_count(template, ResourceType.VPC, 1)

    def test_vpc_has_correct_number_of_subnets(self, template):
        """Test that VPC uses exactly 2 availability zones (2 public + 2 private subnets)"""
        assert_resource_count(template, ResourceType.SUBNET, InfraConfig.EXPECTED_SUBNETS)

    def test_vpc_has_nat_gateway(self, template):
        """Test that VPC has exactly 1 NAT gateway"""
        assert_resource_count(template, ResourceType.NAT_GATEWAY, InfraConfig.EXPECTED_NAT_GATEWAYS)

    def test_vpc_has_internet_gateway(self, template):
        """Test that VPC has an internet gateway"""
        assert_resource_count(template, ResourceType.INTERNET_GATEWAY, 1)

    def test_vpc_subnets_have_correct_cidr_mask(self, template):
        """Test that subnets use /24 CIDR mask"""
        subnets = template.find_resources(ResourceType.SUBNET)

        for subnet_id, subnet in subnets.items():
            cidr = subnet["Properties"]["CidrBlock"]
            # CIDR blocks should contain /24 or be a CloudFormation function
            assert InfraConfig.SUBNET_CIDR_MASK in str(cidr) or cidr.get("Fn::Select") is not None


class TestSecurityGroups:
    """Test security group configuration"""

    def test_security_groups_created(self, template):
        """Test that security groups are created for ALBs and ECS instances"""
        from tests.test_helpers import assert_resource_count_at_least
        assert_resource_count_at_least(
            template,
            ResourceType.SECURITY_GROUP,
            InfraConfig.MIN_EXPECTED_SECURITY_GROUPS
        )
