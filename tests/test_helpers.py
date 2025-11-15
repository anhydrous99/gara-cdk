"""Helper functions for CDK infrastructure tests"""
import aws_cdk.assertions as assertions


def assert_resource_count(template, resource_type: str, expected_count: int):
    """Assert that a specific resource type exists in expected quantity

    Args:
        template: CDK Template object
        resource_type: CloudFormation resource type (e.g., 'AWS::S3::Bucket')
        expected_count: Expected number of resources
    """
    template.resource_count_is(resource_type, expected_count)


def assert_resource_count_at_least(template, resource_type: str, min_count: int):
    """Assert that a resource type exists in at least minimum quantity

    Args:
        template: CDK Template object
        resource_type: CloudFormation resource type
        min_count: Minimum expected number of resources
    """
    resources = template.find_resources(resource_type)
    actual_count = len(resources)
    assert actual_count >= min_count, (
        f"Expected at least {min_count} resources of type {resource_type}, "
        f"but found {actual_count}"
    )


def assert_has_property(template, resource_type: str, properties: dict):
    """Assert that a resource has specific properties

    Args:
        template: CDK Template object
        resource_type: CloudFormation resource type
        properties: Dictionary of expected properties
    """
    template.has_resource_properties(resource_type, properties)


def assert_output_exists(template, output_name: str, description: str = None):
    """Assert that a CloudFormation output exists

    Args:
        template: CDK Template object
        output_name: Name of the output
        description: Optional expected description
    """
    if description:
        template.has_output(output_name, {"Description": description})
    else:
        outputs = template.find_outputs("*")
        assert output_name in outputs, f"Output '{output_name}' not found in template"


def get_resource_count(template, resource_type: str) -> int:
    """Get the count of resources of a specific type

    Args:
        template: CDK Template object
        resource_type: CloudFormation resource type

    Returns:
        Number of resources of the specified type
    """
    resources = template.find_resources(resource_type)
    return len(resources)


def assert_container_definition(template, container_name: str, **expected_properties):
    """Assert container definition properties

    Args:
        template: CDK Template object
        container_name: Name of the container
        **expected_properties: Expected container properties (memory, cpu, port, etc.)
    """
    container_def = {
        "Name": container_name,
    }

    if "memory" in expected_properties:
        container_def["Memory"] = expected_properties["memory"]
    if "cpu" in expected_properties:
        container_def["Cpu"] = expected_properties["cpu"]
    if "port" in expected_properties:
        container_def["PortMappings"] = assertions.Match.array_with([
            assertions.Match.object_like({
                "ContainerPort": expected_properties["port"],
                "HostPort": expected_properties["port"],
                "Protocol": "tcp"
            })
        ])

    template.has_resource_properties("AWS::ECS::TaskDefinition", {
        "ContainerDefinitions": assertions.Match.array_with([
            assertions.Match.object_like(container_def)
        ])
    })


def assert_environment_variable(template, container_name: str, env_var_name: str,
                               env_var_value: str = None):
    """Assert that a container has a specific environment variable

    Args:
        template: CDK Template object
        container_name: Name of the container
        env_var_name: Environment variable name
        env_var_value: Optional expected value
    """
    env_match = {"Name": env_var_name}
    if env_var_value:
        env_match["Value"] = env_var_value

    template.has_resource_properties("AWS::ECS::TaskDefinition", {
        "ContainerDefinitions": assertions.Match.array_with([
            assertions.Match.object_like({
                "Name": container_name,
                "Environment": assertions.Match.array_with([
                    assertions.Match.object_like(env_match)
                ])
            })
        ])
    })


def assert_iam_permission(template, actions: list):
    """Assert that an IAM policy includes specific actions

    Args:
        template: CDK Template object
        actions: List of IAM actions to check
    """
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Action": assertions.Match.array_with(actions)
                })
            ])
        }
    })


def assert_health_check_config(template, path: str, codes: str,
                               interval: int, timeout: int,
                               healthy_threshold: int, unhealthy_threshold: int):
    """Assert target group health check configuration

    Args:
        template: CDK Template object
        path: Health check path
        codes: Expected HTTP codes
        interval: Check interval in seconds
        timeout: Check timeout in seconds
        healthy_threshold: Healthy threshold count
        unhealthy_threshold: Unhealthy threshold count
    """
    template.has_resource_properties("AWS::ElasticLoadBalancingV2::TargetGroup", {
        "HealthCheckPath": path,
        "HealthCheckIntervalSeconds": interval,
        "HealthCheckTimeoutSeconds": timeout,
        "HealthyThresholdCount": healthy_threshold,
        "UnhealthyThresholdCount": unhealthy_threshold,
        "Matcher": {"HttpCode": codes}
    })
