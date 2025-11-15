# CDK Infrastructure Test Suite

This directory contains comprehensive tests for the Gara CDK infrastructure stack, following Clean Code principles.

## Test Organization

### Test Structure

The test suite is organized into logical modules based on AWS service categories:

```
tests/
├── conftest.py                      # Pytest fixtures (shared test setup)
├── test_constants.py                # Constants and configuration values
├── test_helpers.py                  # Reusable test helper functions
├── unit/
│   ├── test_vpc_networking.py       # VPC and network infrastructure
│   ├── test_storage.py              # S3 and DynamoDB
│   ├── test_containers.py           # ECR, ECS, and Load Balancers
│   ├── test_iam_security.py         # IAM roles and permissions
│   ├── test_cicd.py                 # CodeBuild and CodePipeline
│   └── test_outputs_monitoring.py   # CloudFormation outputs and CloudWatch
└── README.md                        # This file
```

### Design Principles

This test suite follows Clean Code principles:

1. **DRY (Don't Repeat Yourself)**
   - Fixtures in `conftest.py` eliminate duplicate stack creation
   - Helper functions in `test_helpers.py` encapsulate common assertions
   - Constants in `test_constants.py` prevent magic strings/numbers

2. **Single Responsibility**
   - Each test file focuses on one aspect of infrastructure
   - Each test function validates one specific behavior
   - Helper functions have clear, single purposes

3. **Meaningful Names**
   - Test functions describe what they validate
   - Constants have descriptive names (e.g., `InfraConfig.BACKEND_MEMORY`)
   - Helper functions clearly state their purpose

4. **Maintainability**
   - Changes to infrastructure values require updates in one place (constants)
   - New tests can reuse existing fixtures and helpers
   - Modular structure makes it easy to find and update tests

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Module
```bash
pytest tests/unit/test_vpc_networking.py
pytest tests/unit/test_storage.py
```

### Run Tests with Coverage
```bash
pytest --cov=gara_cdk --cov-report=html
```

### Run Tests in Verbose Mode
```bash
pytest -v
```

### Run Specific Test Class
```bash
pytest tests/unit/test_storage.py::TestDynamoDB
```

### Run Specific Test Function
```bash
pytest tests/unit/test_storage.py::TestDynamoDB::test_dynamodb_table_created
```

## Test Coverage

The test suite provides comprehensive coverage across:

- **VPC & Networking** (7 tests): VPC, subnets, NAT gateway, security groups
- **Storage** (10 tests): S3 buckets, DynamoDB tables and indexes
- **Containers** (19 tests): ECR, ECS cluster, task definitions, load balancers
- **IAM & Security** (6 tests): Roles, policies, and permissions
- **CI/CD** (11 tests): CodeBuild and CodePipeline configuration
- **Outputs & Monitoring** (10 tests): CloudFormation outputs, CloudWatch logs

**Total: 63 tests** validating all critical infrastructure components

## Key Files

### `conftest.py`
Contains pytest fixtures that are shared across all tests:
- `cdk_app`: Creates a CDK App instance
- `cdk_stack`: Creates the GaraCdkStack
- `template`: Generates the CloudFormation template

These fixtures are module-scoped for performance (stack created once per test file).

### `test_constants.py`
Central location for all infrastructure configuration values:
- `ResourceType`: CloudFormation resource type strings
- `InfraConfig`: Expected configuration values (counts, sizes, names, etc.)
- `OutputName`: CloudFormation output identifiers
- `EnvVar`: Environment variable names
- `IAMAction`: IAM action identifiers

### `test_helpers.py`
Reusable assertion functions:
- `assert_resource_count()`: Verify exact resource counts
- `assert_resource_count_at_least()`: Verify minimum resource counts
- `assert_has_property()`: Verify resource properties
- `assert_container_definition()`: Verify container configurations
- `assert_environment_variable()`: Verify environment variables
- `assert_iam_permission()`: Verify IAM permissions
- `assert_health_check_config()`: Verify load balancer health checks

## Adding New Tests

### 1. Choose the Appropriate Test File
Place your test in the file that matches its AWS service category.

### 2. Use Existing Fixtures
```python
def test_my_new_test(template):
    # template fixture is automatically available
    assert_resource_count(template, ResourceType.MY_RESOURCE, 1)
```

### 3. Add New Constants
If your test needs new configuration values, add them to `test_constants.py`:
```python
class InfraConfig:
    MY_NEW_CONSTANT = "value"
```

### 4. Create Helper Functions
If you have repeated assertion logic, add a helper to `test_helpers.py`:
```python
def assert_my_custom_check(template, expected_value):
    # Your assertion logic
    pass
```

## Best Practices

1. **Use fixtures instead of setup/teardown**
   - Fixtures are more flexible and composable
   - Module-scoped fixtures improve performance

2. **Extract constants instead of hardcoding values**
   - Makes tests more maintainable
   - Single source of truth for configuration

3. **Use helper functions for common patterns**
   - Reduces code duplication
   - Improves test readability

4. **Write descriptive test names**
   - Test name should describe what is being validated
   - Use `test_<what_is_being_tested>` format

5. **One assertion per test (when possible)**
   - Makes failures easier to diagnose
   - Each test has a clear purpose

6. **Group related tests in classes**
   - Helps organize tests logically
   - Makes it easier to run related tests together

## Troubleshooting

### Tests are slow
- Fixtures are module-scoped for performance
- If still slow, consider splitting into separate test modules
- Use `pytest -v` to see which tests are taking longest

### Import errors
- Ensure you're running pytest from the project root
- Check that all dependencies are installed: `pip install -r requirements-dev.txt`

### Fixture not found
- Fixtures in `conftest.py` are automatically discovered
- Make sure `conftest.py` is in the tests directory

## Further Reading

- [pytest documentation](https://docs.pytest.org/)
- [AWS CDK Testing](https://docs.aws.amazon.com/cdk/v2/guide/testing.html)
- [Clean Code principles](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
