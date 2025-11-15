"""Tests for CI/CD pipeline (CodeBuild and CodePipeline)"""
import pytest
import aws_cdk.assertions as assertions
from tests.test_constants import ResourceType, InfraConfig
from tests.test_helpers import assert_resource_count, assert_has_property


class TestCodeBuild:
    """Test CodeBuild configuration"""

    def test_codebuild_project_created(self, template):
        """Test that CodeBuild project is created"""
        assert_resource_count(template, ResourceType.CODEBUILD_PROJECT, 1)

    def test_codebuild_project_name(self, template):
        """Test that CodeBuild project has correct name"""
        assert_has_property(template, ResourceType.CODEBUILD_PROJECT, {
            "Name": InfraConfig.BUILD_PROJECT_NAME
        })

    def test_codebuild_build_environment(self, template):
        """Test that CodeBuild uses correct build image and privileged mode"""
        assert_has_property(template, ResourceType.CODEBUILD_PROJECT, {
            "Environment": assertions.Match.object_like({
                "Image": InfraConfig.BUILD_IMAGE,
                "PrivilegedMode": True
            })
        })

    def test_codebuild_environment_variables(self, template):
        """Test that CodeBuild has necessary environment variables"""
        assert_has_property(template, ResourceType.CODEBUILD_PROJECT, {
            "Environment": assertions.Match.object_like({
                "EnvironmentVariables": assertions.Match.array_with([
                    assertions.Match.object_like({"Name": "AWS_ACCOUNT_ID"}),
                    assertions.Match.object_like({"Name": "AWS_DEFAULT_REGION"}),
                    assertions.Match.object_like({"Name": "ECR_REPOSITORY_URI"}),
                    assertions.Match.object_like({"Name": "FRONTEND_ECR_REPOSITORY_URI"}),
                    assertions.Match.object_like({
                        "Name": "GITHUB_TOKEN",
                        "Type": "SECRETS_MANAGER"
                    })
                ])
            })
        })

    def test_codebuild_github_webhook(self, template):
        """Test that CodeBuild has GitHub webhook configured"""
        assert_has_property(template, ResourceType.CODEBUILD_PROJECT, {
            "Source": assertions.Match.object_like({
                "Type": "GITHUB"
            }),
            "Triggers": assertions.Match.object_like({
                "Webhook": True
            })
        })

    def test_codebuild_timeout(self, template):
        """Test that CodeBuild has correct timeout"""
        assert_has_property(template, ResourceType.CODEBUILD_PROJECT, {
            "TimeoutInMinutes": InfraConfig.BUILD_TIMEOUT
        })


class TestCodePipeline:
    """Test CodePipeline configuration"""

    def test_codepipeline_created(self, template):
        """Test that CodePipeline is created"""
        assert_resource_count(template, ResourceType.CODEPIPELINE, 1)

    def test_codepipeline_name(self, template):
        """Test that CodePipeline has correct name"""
        assert_has_property(template, ResourceType.CODEPIPELINE, {
            "Name": InfraConfig.PIPELINE_NAME
        })

    def test_codepipeline_has_three_stages(self, template):
        """Test that pipeline has 3 stages: Source, Build, Deploy"""
        assert_has_property(template, ResourceType.CODEPIPELINE, {
            "Stages": assertions.Match.array_equals([
                assertions.Match.object_like({"Name": "Source"}),
                assertions.Match.object_like({"Name": "Build"}),
                assertions.Match.object_like({"Name": "Deploy"})
            ])
        })

    def test_codepipeline_source_stage_github(self, template):
        """Test that source stage uses GitHub with correct configuration"""
        assert_has_property(template, ResourceType.CODEPIPELINE, {
            "Stages": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Name": "Source",
                    "Actions": assertions.Match.array_with([
                        assertions.Match.object_like({
                            "ActionTypeId": assertions.Match.object_like({
                                "Category": "Source",
                                "Provider": "GitHub"
                            }),
                            "Configuration": assertions.Match.object_like({
                                "Owner": InfraConfig.GITHUB_OWNER,
                                "Repo": InfraConfig.GITHUB_REPO,
                                "Branch": InfraConfig.GITHUB_BRANCH
                            })
                        })
                    ])
                })
            ])
        })

    def test_codepipeline_deploy_stage_dual_deployment(self, template):
        """Test that deploy stage deploys to both backend and frontend"""
        assert_has_property(template, ResourceType.CODEPIPELINE, {
            "Stages": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Name": "Deploy",
                    "Actions": assertions.Match.array_with([
                        assertions.Match.object_like({
                            "Name": "DeployBackend",
                            "ActionTypeId": assertions.Match.object_like({
                                "Provider": "ECS"
                            })
                        }),
                        assertions.Match.object_like({
                            "Name": "DeployFrontend",
                            "ActionTypeId": assertions.Match.object_like({
                                "Provider": "ECS"
                            })
                        })
                    ])
                })
            ])
        })
