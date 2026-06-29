# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Build Stream Test Messages (v2.1)."""

# =============================================================================
# TEST NAMES
# =============================================================================

TEST_NAMES = {
    "build_stream_enabled": "Build Stream Enabled Check",
    "build_stream_health": "Build Stream API Health Check",
    "postgres_tables": "PostgreSQL Database Tables Check",
    "gitlab_server": "GitLab Server Running Check",
    "gitlab_runner": "GitLab Runner Running Check",
    "catalog_upload": "Catalog Upload and Pipeline Trigger",
    "pipeline_triggered": "Pipeline Auto-Triggered Check",
    "stage_monitor": "Stage '{stage}' Monitor",
    "stage_db_verify": "Stage '{stage}' Database Verification",
    "catalog_roles": "Catalog Roles and Architectures Check",
    "registry_images": "Registry Images Verification",
    "s3_boot_images": "S3 Boot Images Verification",
    "build_pipeline_result": "Build Pipeline Final Result",
    "pxe_boot_connectivity": "PXE Boot Node Connectivity Check",
    "pxe_boot_cloudinit": "PXE Boot Cloud-Init Verification",
}

# =============================================================================
# LOG MESSAGES
# =============================================================================

TEST_LOG_MSGS = {
    "build_stream_enabled_ok": "Build stream is enabled",
    "build_stream_enabled_fail": "Build stream is not enabled",
    "health_ok": "Build Stream API is healthy",
    "health_fail": "Build Stream API health check failed: {error}",
    "postgres_ok": "All expected tables exist in build_stream_db",
    "postgres_fail": "Missing tables in build_stream_db: {missing}",
    "gitlab_server_ok": "GitLab server is running and accessible",
    "gitlab_server_fail": "GitLab server is not accessible: {error}",
    "gitlab_runner_ok": "GitLab runner is running",
    "gitlab_runner_fail": "GitLab runner is not running: {error}",
    "catalog_upload_ok": "Catalog uploaded successfully",
    "catalog_upload_fail": "Failed to upload catalog: {error}",
    "pipeline_triggered_ok": "Pipeline {pipeline_id} triggered successfully",
    "pipeline_triggered_fail": "Pipeline not triggered: {error}",
    "stage_running": "Stage '{stage}' is running...",
    "stage_completed": "Stage '{stage}' completed successfully ({elapsed}s)",
    "stage_failed": "Stage '{stage}' failed: {error}",
    "stage_db_ok": "Stage '{stage}' verified in database (state: {state})",
    "stage_db_fail": "Stage '{stage}' database verification failed: {error}",
    "catalog_roles_ok": "Catalog roles retrieved: {roles} (architectures: {archs})",
    "catalog_roles_fail": "Failed to get catalog roles: {error}",
    "registry_ok": "All {count} role images found in registry",
    "registry_fail": "Missing {count} role image(s) in registry: {missing}",
    "s3_ok": "All {count} role boot images found in S3",
    "s3_fail": "Missing {count} role boot image(s) in S3: {missing}",
    "pipeline_result_ok": "Build pipeline completed -- all stages passed",
    "pipeline_result_fail": "Build pipeline completed with failures",
    "pxe_connectivity_ok": "All {count} nodes reachable (ping + SSH)",
    "pxe_connectivity_fail": "{unreachable} of {total} nodes unreachable",
    "pxe_cloudinit_ok": "Cloud-init completed on all {count} reachable nodes",
    "pxe_cloudinit_fail": "Cloud-init failed on {failed} of {total} nodes",
    "pxe_no_nodes": "No nodes found in PXE mapping file",
}

# =============================================================================
# ASSERT MESSAGES
# =============================================================================

TEST_ASSERT_MSGS = {
    "build_stream_not_enabled": "Build stream is not enabled in build_stream_config.yml",
    "health_failed": "Build Stream API health check failed: {error}",
    "postgres_failed": "PostgreSQL tables check failed: {error}",
    "gitlab_server_failed": "GitLab server check failed: {error}",
    "gitlab_runner_failed": "GitLab runner check failed: {error}",
    "catalog_upload_failed": "Catalog upload failed: {error}",
    "pipeline_not_triggered": "Pipeline was not triggered after catalog upload",
    "stage_failed": "Stage '{stage}' failed: {error}",
    "stage_db_failed": "Stage '{stage}' database verification failed: {error}",
    "catalog_roles_failed": "Failed to retrieve catalog roles: {error}",
    "registry_images_failed": "Registry image verification failed: {error}",
    "s3_images_failed": "S3 boot image verification failed: {error}",
    "pxe_connectivity_failed": "Node connectivity check failed: {error}",
    "pxe_cloudinit_failed": "Cloud-init verification failed: {error}",
}

# =============================================================================
# SKIP MESSAGES
# =============================================================================

SKIP_MSGS = {
    "build_stream_disabled": "Test skipped - build_stream is not enabled",
    "no_job_id": "Test skipped - no job_id available",
    "previous_stage_failed": "Test skipped - previous stage '{stage}' failed",
    "build_failed": "Test skipped - build pipeline failed",
    "pipeline_not_triggered": "Test skipped - pipeline not triggered",
    "no_nodes_in_pxe_mapping": "Test skipped - no nodes found in PXE mapping file",
}

# =============================================================================
# PIPELINE MESSAGES (for real-time logging)
# =============================================================================

PIPELINE_MSGS = {
    "checking_pipelines": "Checking for existing pipelines...",
    "pipeline_running": "WARNING: Pipeline #{id} is already {status}",
    "no_running_pipelines": "No running/pending pipelines. Latest pipeline ID: {id}",
    "uploading_catalog": "Uploading catalog file to GitLab...",
    "catalog_uploaded": "Catalog uploaded successfully",
    "waiting_pipeline": "Waiting for pipeline to be triggered...",
    "pipeline_triggered": "Pipeline #{id} triggered (status: {status})",
    "waiting_job_db": "Waiting for job to be created in database...",
    "job_created": "Job created: {job_id} (state: {state})",
    "job_not_found": "Warning: Job not found in DB within timeout",
    "pipeline_already_running": "Pipeline #{id} is already {status}. Please cancel it first.",
}

# =============================================================================
# STAGE POLLING MESSAGES (for real-time logging)
# =============================================================================

STAGE_POLL_MSGS = {
    "polling_start": "Polling stage '{stage}' (interval: {interval}s, timeout: {timeout} min)",
    "stage_not_created": "[{time}] Stage '{stage}' not yet created, waiting...",
    "stage_state_change": "[{time}] Stage '{stage}' -> {state}",
    "stage_completed": "[{time}] Stage '{stage}' COMPLETED",
    "stage_failed": "[{time}] Stage '{stage}' FAILED",
    "stage_error": "  Error: {error}",
    "pipeline_status": "[{time}] Pipeline #{id} status: {status}",
    "pipeline_failed": "  Pipeline failed! Check GitLab CI/CD for error details.",
    "pipeline_canceled": "  Pipeline was canceled!",
    "stage_still_running": "[{time}] Stage '{stage}' still {state}...",
    "stage_timeout": "[{time}] TIMEOUT - Stage '{stage}' did not complete",
}
