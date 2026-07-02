# BuildStreaM Issues

Issues related to the BuildStreaM catalog-driven CI/CD deployment workflow,
including GitLab pipeline stage failures, container registry operations,
catalog parsing, and OAuth credentials.

## Health Check stage failing

???+ note "Symptom"

    The Health Check stage in the BuildStreaM pipeline fails.

??? note "Cause"

    - The GitLab target IP and the host IP of the BuildStreaM API server are not reachable from each other.
    - BuildStreaM containers are not running properly.

??? note "Resolution"

    1. Ensure the GitLab target IP and BuildStreaM API server are in the same subnet.

    2. Verify that the `omnia_build_stream`, `omnia_postgres`, and `playbook_watcher` services are running on the OIM node:

        ```bash title="Run on: OIM host"
        systemctl status omnia_build_stream.service
        systemctl status omnia_postgres.service
        systemctl status playbook_watcher.service
        ```

    3. If any service has failed, capture and verify the logs:

        ```bash title="Run on: OIM host"
        journalctl -u omnia_build_stream --no-pager
        journalctl -u omnia_postgres --no-pager
        ```

## API Registration stage failing

???+ note "Symptom"

    The API-Registration stage in the BuildStreaM pipeline fails.

??? note "Cause"

    - Maximum client limit reached for BuildStreaM API server registration. Currently, only one client can be registered.
    - Other API registration errors.

??? note "Resolution"

    1. If you encounter the `max_clients_limit_reached` error:
        - Either run the pipeline from the already registered client.
        - Or perform the `gitlab_cleanup` and reconfigure GitLab using the playbook.

    2. For other non-successful API responses, check the authentication logs at `/<nfs-dir>/omnia/log/build_stream/auth.log` on the OIM.

## Token Generation stage failing

???+ note "Symptom"

    The Token-Generation stage in the BuildStreaM pipeline fails.

??? note "Cause"

    - Token generation failed due to authentication issues.
    - Token generation failed due to network issues.

??? note "Resolution"

    1. On the OIM, check the authentication logs at `/<nfs-dir>/omnia/log/build_stream/auth.log` for detailed error information.

## Parse Catalog stage failing

???+ note "Symptom"

    The Parse-Catalog stage in the BuildStreaM pipeline fails with errors such as invalid JSON schema format or catalog structure mismatch.

??? note "Cause"

    - Invalid JSON schema format.
    - The `catalog_rhel.json` structure does not match the expected catalog schema.

??? note "Resolution"

    1. Ensure the JSON is aligned with the schema as shown in reference examples at:
        `https://github.com/dell/omnia/tree/pub/build_stream/examples/catalog`

    2. If the issue persists, check the job-specific logs on the OIM at `/<nfs-dir>/omnia/log/build_stream/<job-id>/<jobid>.log`.

## Create Local Repo stage failing

???+ note "Symptom"

    The Create-Local-Repo stage in the BuildStreaM pipeline fails.

??? note "Cause"

    - Playbook execution failed.
    - Configuration issues in `local_repo_config.yml`.

??? note "Resolution"

    1. Check the log path from the API response for detailed error information. Example API response:

        ```json title="Example API response"
        {
            "stage_name": "create-local-repository",
            "stage_state": "FAILED",
            "started_at": "2026-03-11T10:07:58.906785+00:00Z",
            "ended_at": "2026-03-11T10:49:20.639894+00:00Z",
            "error_code": "PLAYBOOK_EXECUTION_FAILED",
            "error_summary": "Playbook exited with code 2",
            "log_file_path": "/nfs/omnia/log/build_stream/<job-id>/local_repo.yml_20260311_171630.log"
        }
        ```

    2. Verify the configuration settings in `local_repo_config.yml`.

    3. After fixing the configuration issues, re-run the pipeline.

## Build Images stage failing

???+ note "Symptom"

    The Build Images stage in the BuildStreaM pipeline fails.

??? note "Cause"

    - Playbook execution failed.
    - The catalog does not have predefined functional groups.

??? note "Resolution"

    1. Ensure the catalog has the predefined functional groups.

    2. If changes are required in the catalog, make the necessary modifications.

    3. After fixing catalog issues, re-run the pipeline.

## Deploy Images stage failing

???+ note "Symptom"

    The Deploy Images stage in the BuildStreaM pipeline fails.

??? note "Cause"

    - Playbook execution failed.
    - The functional groups listed in the PXE mapping file do not match the functional groups in `catalog_rhel.json`.

??? note "Resolution"

    1. Check the log path from the API response for detailed error information.

    2. Ensure the functional groups listed in the PXE mapping file match those defined in `catalog_rhel.json`.

    3. After making necessary modifications to the PXE mapping, re-run the pipeline manually.

## GitLab pipeline failures (general)

???+ note "Symptom"

    A BuildStreaM pipeline in GitLab fails with a red status indicator. The
    pipeline log shows errors in one or more stages (build, deploy, test).

??? note "Cause"

    - The GitLab Runner is not registered or is offline.
    - Pipeline variables (credentials, URLs) are missing or incorrect.
    - The runner does not have network access to the OIM or cluster nodes.
    - A previous pipeline left stale state that conflicts with the current run.

??? note "Resolution"

    1. Check the pipeline log in GitLab:
        - Navigate to **CI/CD > Pipelines** in the BuildStreaM project.
        - Click the failed pipeline, then click the failed job to see its log.

    2. Verify the GitLab Runner is registered and online:

        ```bash title="Run on: GitLab node"
        gitlab-runner list
        gitlab-runner verify
        ```

    3. Check pipeline variables:
        - Navigate to **Settings > CI/CD > Variables** in the GitLab project.
        - Verify all required variables are set (OIM IP, credentials, registry URL).

    4. Test network connectivity from the runner to the OIM:

        ```bash title="Run on: GitLab node"
        ping <oim_ip>
        ssh root@<oim_ip> hostname
        ```

    5. If stale state is the issue, clean up and retry:

        ```bash title="Run on: GitLab node"
        gitlab-runner clear-cache
        ```

## Retry button not displayed

???+ note "Symptom"

    The Retry button is not displayed for failed pipeline stages, including
    deploy, restart, and validate operations.

??? note "Cause"

    The Retry button may not appear in certain failed pipeline stages due to GitLab issues.

??? note "Resolution"

    1. Initiate a restart from the parent pipeline to resolve this issue.

    2. This action restarts the entire pipeline from the beginning, allowing all stages to execute again.

## Registry push failures

???+ note "Symptom"

    The BuildStreaM pipeline fails during the image push stage with errors such
    as:

    ```text title="Example error"
    Error: failed to push image: authentication required
    Error: failed to push image: denied: requested access to the resource is denied
    ```

??? note "Cause"

    - Container registry credentials are incorrect or expired.
    - The registry URL in the pipeline configuration is wrong.
    - The registry's TLS certificate is not trusted by the runner.
    - The registry storage is full.

??? note "Resolution"

    1. Verify registry credentials:

        ```bash title="Run on: OIM host"
        podman login <registry_url>
        ```

    2. Check that the registry URL matches the pipeline configuration:

        ```bash title="Run on: OIM host"
        grep -i registry .gitlab-ci.yml
        ```

    3. If TLS is the issue, add the registry's CA certificate:

        ```bash title="Run on: OIM host"
        cp <registry_ca.crt> /etc/pki/ca-trust/source/anchors/
        update-ca-trust
        ```

    4. Check registry storage:

        ```bash title="Run on: OIM host"
        df -h <registry_data_dir>
        ```

## OAuth credential issues

???+ note "Symptom"

    BuildStreaM operations fail with OAuth authentication errors when
    communicating with GitLab or external services:

    ```text title="Example error"
    Error: OAuth token expired or revoked
    Error: 401 Unauthorized: invalid_token
    ```

??? note "Cause"

    - The OAuth token has expired.
    - The OAuth application was deleted or its secret was rotated in GitLab.
    - The token scope does not include the required permissions (`api`, `read_registry`, `write_registry`).

??? note "Resolution"

    1. Check the current token status:

        ```bash title="Run on: OIM host"
        curl -H "Authorization: Bearer <token>" \
          https://<gitlab_url>/api/v4/user
        ```

        A `401` response confirms the token is invalid.

    2. Generate a new personal access token in GitLab:
        - Navigate to **User Settings > Access Tokens**.
        - Create a new token with scopes: `api`, `read_registry`, `write_registry`.

    3. Update the token in pipeline variables:
        - Navigate to **Settings > CI/CD > Variables**.
        - Update the `GITLAB_TOKEN` (or equivalent) variable with the new token.

    4. If using an OAuth application (rather than personal token):
        - Navigate to **Admin Area > Applications** (or **User Settings > Applications**).
        - Verify the application exists and note the Application ID and Secret.
        - Update the pipeline variables with the new credentials.

    5. Re-run the failed pipeline from the GitLab UI.

!!! info "Related resources"

    - [Deploy GitLab](../HowTo/BuildStreaM/deploy_gitlab.md) -- GitLab deployment guide.
    - [Update Catalog & Pipelines](../HowTo/BuildStreaM/update_catalog_pipeline.md) -- Catalog and pipeline configuration.
    - [BuildStreaM Deployment](../GetStarted/buildstream_deployment.md) -- End-to-end deployment tutorial.
    - [Cleanup Operations](../HowTo/BuildStreaM/cleanup_operations.md) -- Remove old Image Groups.
    - [Retry Pipelines](../HowTo/BuildStreaM/retry_pipelines.md) -- Retry failed pipeline operations.
