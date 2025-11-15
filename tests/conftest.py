"""Pytest configuration and shared fixtures for CDK tests"""
import pytest
import aws_cdk as core
import aws_cdk.assertions as assertions
from gara_cdk.gara_cdk_stack import GaraCdkStack


@pytest.fixture(scope="module")
def cdk_app():
    """Create a CDK app for testing (module-scoped for performance)"""
    return core.App()


@pytest.fixture(scope="module")
def cdk_stack(cdk_app):
    """Create the GaraCdkStack for testing (module-scoped for performance)"""
    return GaraCdkStack(cdk_app, "test-gara-cdk")


@pytest.fixture(scope="module")
def template(cdk_stack):
    """Generate CloudFormation template from the stack (module-scoped for performance)"""
    return assertions.Template.from_stack(cdk_stack)
