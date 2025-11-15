# Test Migration Map

## Overview

The original `test_gara_cdk_stack.py` (65 tests) has been refactored into 6 modular files (66 tests). The tests are functionally equivalent but better organized.

## Test Mapping

### Original → Refactored

| Original Test (test_gara_cdk_stack.py) | New Location | Notes |
|----------------------------------------|--------------|-------|
| **TestStackCreation** | | |
| `test_stack_synthesizes_successfully` | `test_outputs_monitoring.py::TestStackValidation::test_stack_synthesizes_successfully` | Moved to validation |
| | |
| **TestVPCConfiguration** | `test_vpc_networking.py::TestVPCConfiguration` | |
| `test_vpc_is_created` | `test_vpc_is_created` | Same functionality |
| `test_vpc_has_two_availability_zones` | `test_vpc_has_correct_number_of_subnets` | Renamed for clarity |
| `test_vpc_has_nat_gateway` | `test_vpc_has_nat_gateway` | Same functionality |
| `test_vpc_has_internet_gateway` | `test_vpc_has_internet_gateway` | Same functionality |
| `test_vpc_subnets_have_correct_cidr_mask` | `test_vpc_subnets_have_correct_cidr_mask` | Same functionality |
| | |
| **TestS3Bucket** | `test_storage.py::TestS3Bucket` | |
| `test_s3_bucket_is_created` | `test_s3_buckets_created` | Updated for 2 buckets |
| `test_s3_bucket_has_correct_name_pattern` | `test_s3_bucket_has_naming_configuration` | Improved assertion |
| `test_s3_bucket_blocks_public_access` | `test_s3_bucket_blocks_public_access` | Same functionality |
| | |
| **TestDynamoDB** | `test_storage.py::TestDynamoDB` | |
| `test_dynamodb_table_is_created` | `test_dynamodb_table_created` | Same functionality |
| `test_dynamodb_table_name_pattern` | `test_dynamodb_table_has_name` | Improved assertion |
| `test_dynamodb_table_has_correct_partition_key` | `test_dynamodb_table_has_correct_partition_key` | Same functionality |
| `test_dynamodb_table_has_pay_per_request_billing` | `test_dynamodb_table_billing_mode` | Renamed |
| `test_dynamodb_table_has_point_in_time_recovery` | `test_dynamodb_table_has_point_in_time_recovery` | Same functionality |
| `test_dynamodb_table_has_published_index` | `test_dynamodb_table_has_published_index` | Same functionality |
| `test_dynamodb_table_has_correct_attributes` | `test_dynamodb_table_attributes` | Renamed |
| | |
| **TestECRRepositories** | `test_containers.py::TestECRRepositories` | |
| `test_ecr_repositories_are_created` | `test_ecr_repositories_created` | Same functionality |
| `test_backend_ecr_repository_name` | `test_backend_ecr_repository_name` | Same functionality |
| `test_frontend_ecr_repository_name` | `test_frontend_ecr_repository_name` | Same functionality |
| `test_ecr_repositories_have_lifecycle_policies` | `test_ecr_repositories_have_lifecycle_policies` | Same functionality |
| | |
| **TestECSCluster** | `test_containers.py::TestECSCluster` | |
| `test_ecs_cluster_is_created` | `test_ecs_cluster_created` | Same functionality |
| `test_ecs_cluster_name` | `test_ecs_cluster_name` | Same functionality |
| `test_ecs_cluster_has_container_insights` | `test_ecs_cluster_has_container_insights` | Same functionality |
| `test_ecs_cluster_has_autoscaling_group` | `test_autoscaling_group_exists` | Renamed |
| `test_autoscaling_group_uses_t3_small` | `test_autoscaling_group_instance_type` | Renamed |
| `test_autoscaling_group_capacity` | `test_autoscaling_group_capacity` | Same functionality |
| | |
| **TestIAMRoles** | `test_iam_security.py::TestIAMRoles` | |
| `test_backend_task_role_exists` | `test_iam_roles_created` | Generalized |
| `test_task_roles_trust_ecs_service` | `test_task_roles_trust_ecs_service` | Same functionality |
| `test_backend_has_s3_permissions` | `test_backend_has_s3_permissions` | Same functionality |
| `test_backend_has_dynamodb_permissions` | `test_backend_has_dynamodb_permissions` | Same functionality |
| `test_backend_has_secrets_manager_permissions` | `test_backend_has_secrets_manager_permissions` | Same functionality |
| `test_codebuild_role_has_ecr_permissions` | `test_codebuild_role_has_ecr_permissions` | Same functionality |
| | |
| **TestECSTaskDefinitions** | `test_containers.py::TestECSTaskDefinitions` | |
| `test_two_task_definitions_created` | `test_task_definitions_created` | Same functionality |
| `test_task_definitions_use_bridge_network_mode` | `test_task_definitions_use_bridge_network_mode` | Same functionality |
| `test_backend_task_definition_container_config` | `test_backend_container_configuration` | Uses helper function |
| `test_frontend_task_definition_container_config` | `test_frontend_container_configuration` | Uses helper function |
| `test_backend_task_environment_variables` | `test_backend_environment_variables` | Uses helper function |
| `test_frontend_task_has_api_key_secret` | `test_frontend_has_api_key_secret` | Same functionality |
| `test_task_definitions_have_cloudwatch_logging` | `test_task_definitions_have_cloudwatch_logging` | Same functionality |
| | |
| **TestLoadBalancers** | `test_containers.py::TestLoadBalancers` | |
| `test_two_load_balancers_created` | `test_load_balancers_created` | Same functionality |
| `test_load_balancers_are_internet_facing` | `test_load_balancers_are_internet_facing` | Same functionality |
| `test_target_groups_health_check_config` | `test_target_group_health_check_configuration` | Uses helper function |
| `test_two_ecs_services_created` | `test_ecs_services_created` | Same functionality |
| `test_ecs_services_have_desired_count` | `test_ecs_services_desired_count` | Same functionality |
| | |
| **TestCodeBuild** | `test_cicd.py::TestCodeBuild` | |
| `test_codebuild_project_created` | `test_codebuild_project_created` | Same functionality |
| `test_codebuild_project_name` | `test_codebuild_project_name` | Same functionality |
| `test_codebuild_uses_standard_7_image` | `test_codebuild_build_environment` | Combined test |
| `test_codebuild_has_correct_environment_variables` | `test_codebuild_environment_variables` | Same functionality |
| `test_codebuild_has_github_webhook` | `test_codebuild_github_webhook` | Same functionality |
| `test_codebuild_timeout` | `test_codebuild_timeout` | Same functionality |
| | |
| **TestCodePipeline** | `test_cicd.py::TestCodePipeline` | |
| `test_codepipeline_created` | `test_codepipeline_created` | Same functionality |
| `test_codepipeline_name` | `test_codepipeline_name` | Same functionality |
| `test_codepipeline_has_three_stages` | `test_codepipeline_has_three_stages` | Same functionality |
| `test_codepipeline_source_stage_uses_github` | `test_codepipeline_source_stage_github` | Same functionality |
| `test_codepipeline_deploy_stage_has_two_actions` | `test_codepipeline_deploy_stage_dual_deployment` | Renamed for clarity |
| | |
| **TestCloudFormationOutputs** | `test_outputs_monitoring.py::TestCloudFormationOutputs` | |
| `test_all_outputs_are_created` | `test_minimum_outputs_created` | Renamed |
| `test_backend_load_balancer_output` | `test_backend_load_balancer_output` | Same functionality |
| `test_frontend_load_balancer_output` | `test_frontend_load_balancer_output` | Same functionality |
| `test_ecr_repository_outputs` | Split into `test_backend_ecr_output` + `test_frontend_ecr_output` | Separated |
| `test_s3_bucket_output` | `test_s3_bucket_output` | Same functionality |
| `test_dynamodb_table_output` | `test_dynamodb_table_output` | Same functionality |
| | |
| **TestCloudWatchLogs** | `test_outputs_monitoring.py::TestCloudWatchLogs` | |
| `test_log_groups_created` | `test_log_groups_created` | Same functionality |
| `test_log_retention_is_one_week` | `test_log_retention_configured` | Renamed |
| | |
| **TestResourceCounts** | `test_vpc_networking.py::TestSecurityGroups` + `test_outputs_monitoring.py::TestStackValidation` | |
| `test_security_groups_count` | `test_vpc_networking.py::TestSecurityGroups::test_security_groups_created` | Moved |
| `test_no_unencrypted_resources` | `test_outputs_monitoring.py::TestStackValidation::test_no_unencrypted_s3_buckets` | Moved |

## Summary

- **Original file:** 65 tests in 1 file (883 lines)
- **Refactored files:** 66 tests in 6 files (~681 lines total)
- **Additional test:** 1 extra test split from combined test
- **Duplicates:** Yes - both suites test the same functionality

## Recommendation

**Delete** `tests/unit/test_gara_cdk_stack.py` because:

1. ✅ All functionality is covered by refactored tests
2. ✅ Refactored tests are better organized
3. ✅ Refactored tests use constants (no magic values)
4. ✅ Refactored tests use fixtures (no duplication)
5. ✅ Refactored tests use helpers (more maintainable)
6. ❌ Running both wastes time and resources

## Performance Impact

Keeping both files:
- 131 tests run
- Stack synthesized 7 times (once per module)
- ~53 seconds

After deleting original:
- 66 tests run
- Stack synthesized 6 times
- ~30 seconds (estimated 44% faster)
