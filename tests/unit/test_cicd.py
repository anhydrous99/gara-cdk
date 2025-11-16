"""Tests for CI/CD pipeline (CodeBuild and CodePipeline)"""
import pytest
import aws_cdk.assertions as assertions
from tests.test_constants import ResourceType, InfraConfig
from tests.test_helpers import assert_resource_count, assert_has_property


class TestCodeBuild:
    """Test CodeBuild configuration (Dual Pipelines)"""

    def test_codebuild_projects_created(self, template):
        """Test that 2 CodeBuild projects are created (backend + frontend)"""
        assert_resource_count(template, ResourceType.CODEBUILD_PROJECT, 2)

    def test_backend_codebuild_project_name(self, template):
        """Test that backend CodeBuild project has correct name"""
        assert_has_property(template, ResourceType.CODEBUILD_PROJECT, {
            "Name": InfraConfig.BACKEND_BUILD_PROJECT_NAME
        })

    def test_frontend_codebuild_project_name(self, template):
        """Test that frontend CodeBuild project has correct name"""
        assert_has_property(template, ResourceType.CODEBUILD_PROJECT, {
            "Name": InfraConfig.FRONTEND_BUILD_PROJECT_NAME
        })

    def test_codebuild_build_environment(self, template):
        """Test that CodeBuild uses correct build image and privileged mode"""
        assert_has_property(template, ResourceType.CODEBUILD_PROJECT, {
            "Environment": assertions.Match.object_like({
                "Image": InfraConfig.BUILD_IMAGE,
                "PrivilegedMode": True
            })
        })

    def test_codebuild_has_ecr_uri_environment_variable(self, template):
        """Test that CodeBuild has ECR_REPOSITORY_URI environment variable"""
        assert_has_property(template, ResourceType.CODEBUILD_PROJECT, {
            "Environment": assertions.Match.object_like({
                "EnvironmentVariables": assertions.Match.array_with([
                    assertions.Match.object_like({"Name": "AWS_ACCOUNT_ID"}),
                    assertions.Match.object_like({"Name": "AWS_DEFAULT_REGION"}),
                    assertions.Match.object_like({"Name": "ECR_REPOSITORY_URI"}),
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
    """Test CodePipeline configuration (Dual Pipelines)"""

    def test_codepipelines_created(self, template):
        """Test that 2 CodePipelines are created (backend + frontend)"""
        assert_resource_count(template, ResourceType.CODEPIPELINE, 2)

    def test_backend_codepipeline_name(self, template):
        """Test that backend CodePipeline has correct name"""
        assert_has_property(template, ResourceType.CODEPIPELINE, {
            "Name": InfraConfig.BACKEND_PIPELINE_NAME
        })

    def test_frontend_codepipeline_name(self, template):
        """Test that frontend CodePipeline has correct name"""
        assert_has_property(template, ResourceType.CODEPIPELINE, {
            "Name": InfraConfig.FRONTEND_PIPELINE_NAME
        })

    def test_codepipeline_has_three_stages(self, template):
        """Test that each pipeline has 3 stages: Source, Build, Deploy"""
        pipelines = template.find_resources(ResourceType.CODEPIPELINE)
        for pipeline_id, pipeline in pipelines.items():
            stages = pipeline["Properties"]["Stages"]
            assert len(stages) == 3
            stage_names = [stage["Name"] for stage in stages]
            assert stage_names == ["Source", "Build", "Deploy"]

    def test_backend_codepipeline_source_stage_github(self, template):
        """Test that backend pipeline source stage uses GitHub with correct repo"""
        assert_has_property(template, ResourceType.CODEPIPELINE, {
            "Name": InfraConfig.BACKEND_PIPELINE_NAME,
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
                                "Repo": InfraConfig.BACKEND_GITHUB_REPO,
                                "Branch": InfraConfig.GITHUB_BRANCH
                            })
                        })
                    ])
                })
            ])
        })

    def test_frontend_codepipeline_source_stage_github(self, template):
        """Test that frontend pipeline source stage uses GitHub with correct repo"""
        assert_has_property(template, ResourceType.CODEPIPELINE, {
            "Name": InfraConfig.FRONTEND_PIPELINE_NAME,
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
                                "Repo": InfraConfig.FRONTEND_GITHUB_REPO,
                                "Branch": InfraConfig.GITHUB_BRANCH
                            })
                        })
                    ])
                })
            ])
        })

    def test_codepipeline_deploy_stage_to_ecs(self, template):
        """Test that deploy stages deploy to ECS"""
        assert_has_property(template, ResourceType.CODEPIPELINE, {
            "Stages": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Name": "Deploy",
                    "Actions": assertions.Match.array_with([
                        assertions.Match.object_like({
                            "ActionTypeId": assertions.Match.object_like({
                                "Category": "Deploy",
                                "Provider": "ECS"
                            })
                        })
                    ])
                })
            ])
        })
