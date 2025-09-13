from aws_cdk import (
    Stack,
    aws_elasticbeanstalk as eb,
    aws_iam as iam,
    aws_s3_assets as assets,
    CfnOutput
)
from constructs import Construct
import os


class GaraCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create service role for Elastic Beanstalk
        service_role = iam.Role(
            self, "ElasticBeanstalkServiceRole",
            assumed_by=iam.ServicePrincipal("elasticbeanstalk.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSElasticBeanstalkEnhancedHealth"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSElasticBeanstalkManagedUpdatesCustomerRolePolicy")
            ]
        )

        # Create instance profile for EC2 instance
        instance_role = iam.Role(
            self, "ElasticBeanstalkInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSElasticBeanstalkWebTier"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSElasticBeanstalkWorkerTier"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSElasticBeanstalkMulticontainerDocker")
            ]
        )

        instance_profile = iam.CfnInstanceProfile(
            self, "ElasticBeanstalkInstanceProfile",
            roles=[instance_role.role_name]
        )

        # Create Elastic Beanstalk application
        app = eb.CfnApplication(
            self, "GaraApp",
            application_name="gara-app",
            description="Gara docker application deployed via CDK"
        )

        # Create application version with Docker source bundle
        app_version_props = eb.CfnApplicationVersionProps(
            application_name=app.application_name,
            description="Initial version",
            source_bundle=eb.CfnApplicationVersion.SourceBundleProperty(
                s3_bucket=self.create_source_bundle().bucket_name,
                s3_key=self.create_source_bundle().s3_object_key
            )
        )

        app_version = eb.CfnApplicationVersion(
            self, "GaraAppVersion",
            **app_version_props.__dict__
        )
        app_version.add_dependency(app)

        # Create environment
        environment  = eb.CfnEnvironment(
            self, "GaraDockerEnvironment",
            applciation_name=app.application_name,
            environment_name="gara-env",
            solution_stack_name="64bit Amazon Linux 2 v4.3.0 running Docker",
            option_settings=[
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:autoscaling:launchconfiguration",
                    option_name="IamInstanceProfile",
                    value=instance_profile.attr_arn
                ),
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:elasticbeanstalk:environment",
                    option_name="ServiceRole",
                    value=service_role.role_arn
                ),
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:elasticbeanstalk:healthreporting:system",
                    option_name="SystemType",
                    value="enhanced"
                ),
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:autoscaling:asg",
                    option_name="MinSize",
                    value="1"
                ),
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:autoscaling:asg",
                    option_name="MaxSize",
                    value="2"
                ),
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:autoscaling:launchconfiguration",
                    option_name="InstanceType",
                    value="t3.micro"
                )
            ],
            version_label=app_version.ref
        )
        environment.add_dependency(app_version)

        # Output the environment URL
        CfnOutput(
            self, "EnvironmentURL",
            value=f"http://{environment.attr_endpoint_url}",
            description="Gara Elastic Beanstalk Environment URL"
        )

    def create_source_bundle(self):
        app_path = os.path.join(os.path.dirname(__file__), "..", "..", "gara")

        return assets.Asset(
            self, "SourceAsset",
            path=app_path
        )
