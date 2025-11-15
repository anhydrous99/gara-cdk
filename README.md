# Gara CDK Infrastructure

![CDK Tests](https://github.com/anhydrous99/gara-cdk/actions/workflows/test.yml/badge.svg)
![CDK Validation](https://github.com/anhydrous99/gara-cdk/actions/workflows/cdk-validate.yml/badge.svg)

AWS CDK infrastructure for the Gara image management application.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Testing

The project includes a comprehensive test suite with 66 tests covering all infrastructure components.

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run tests with coverage
pytest --cov=gara_cdk --cov-report=html

# Run specific test category
pytest tests/unit/test_storage.py
pytest tests/unit/test_containers.py
```

### Test Structure

Tests are organized by AWS service category:
- `test_vpc_networking.py` - VPC, subnets, security groups
- `test_storage.py` - S3 and DynamoDB
- `test_containers.py` - ECR, ECS, and Load Balancers
- `test_iam_security.py` - IAM roles and permissions
- `test_cicd.py` - CodeBuild and CodePipeline
- `test_outputs_monitoring.py` - CloudFormation outputs and CloudWatch

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation
 * `pytest`          run infrastructure tests

Enjoy!
