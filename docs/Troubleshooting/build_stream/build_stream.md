# BuildStreaM Issues

Issues related to BuildStreaM pipeline execution, GitLab integration, catalog validation, and image deployment.

## Health Check Stage Failing

???+ note "Symptom"

    Health Check stage is failing in the BuildStreaM pipeline.

??? note "Cause"

    - GitLab target IP and host IP of the BuildStreaM API server are not reachable from each other
    - BuildStreaM containers are not running properly

??? note "Resolution"

    1. Ensure the GitLab target IP and BuildStreaM API server are in the same subnet.

    2. Verify that the `omnia_build_stream` container and the `omnia_postgres` and `playbook_watcher` services are running on the OIM node:

        ```bash title="Run on: OIM host"
        systemctl status omnia_build_stream.service
        systemctl status omnia_postgres.service
        systemctl status playbook_watcher.service
        ```

    3. If there are failures in any of the containers, capture and verify the logs from journalctl:

        ```bash title="Run on: OIM host"
        journalctl -u omnia_build_stream --no-pager
        journalctl -u omnia_postgres --no-pager
        ```

## API Registration Stage Failing

???+ note "Symptom"

    API-Registration stage is failing in the BuildStreaM pipeline.

??? note "Cause"

    - Maximum client limit reached for BuildStreaM API server registration
    - Other API registration errors

!!! note

    Currently, only one client can be registered with the BuildStreaM API server.

??? note "Resolution"

    1. If you encounter the `max_clients_limit_reached` error:
        - Either run the pipeline from the already registered client
        - Or perform the `cleanup_gitlab` and reconfigure GitLab using the playbook

    2. For other non-successful API responses, check the authentication log
       on the OIM at
       `<OMNIA_DATA_PATH>/log/build_stream/events.log`.

       `OMNIA_DATA_PATH` is configurable and defaults to `/opt/omnia`. With
       the default value, the log is located at
       `/opt/omnia/log/build_stream/events.log`.

## Token Generation Stage Failing

???+ note "Symptom"

    Token-Generation stage is failing in the BuildStreaM pipeline.

??? note "Cause"

    - Token generation failed due to authentication issues
    - Token generation failed due to network issues

??? note "Resolution"

    On the OIM, check the authentication log at
    `<OMNIA_DATA_PATH>/log/build_stream/events.log`.

## Parse Catalog Stage Failing

???+ note "Symptom"

    Parse-Catalog stage is failing in the BuildStreaM pipeline.

??? note "Cause"

    - Invalid JSON schema format
    - The `catalog_rhel.json` structure does not match the expected catalog schema

??? note "Resolution"

    - Ensure the JSON is aligned with the schema as shown in the reference examples available at:
        - [https://github.com/dell/omnia/tree/pub/build_stream/examples/catalog](https://github.com/dell/omnia/tree/pub/build_stream/examples/catalog)
    - If the issue persists, check the job-specific log on the OIM at
      `<OMNIA_DATA_PATH>/log/build_stream/<job-id>/<job-id>.log`.

## Create Local Repo Stage Failing

???+ note "Symptom"

    Create-Local-Repo stage is failing in the BuildStreaM pipeline.

??? note "Cause"

    - Playbook execution failed
    - Catalog, `repo_manager_config.yml`, or
      `repo_manager_endpoint_config.yml` configuration issues

??? note "Resolution"

    1. If there are issues with playbook execution, the log path is available from the API response. Check the logs at the path specified in the `log_file_path` field.

        **Example API response format**:

        ```json title="Example API response format"
        {
            "stage_name": "create-local-repository",
            "stage_state": "FAILED",
            "started_at": "2026-03-11T10:07:58.906785+00:00Z",
            "ended_at": "2026-03-11T10:49:20.639894+00:00Z",
            "error_code": "PLAYBOOK_EXECUTION_FAILED",
            "error_summary": "Playbook exited with code 2",
            "log_file_path": "/var/log/omnia/repo_manager/<job-id>/repo_manager.yml_20260311_171630.log"
        }
        ```

    2. Verify the selected catalog and the project-scoped
       `repo_manager_config.yml` and `repo_manager_endpoint_config.yml`
       settings.

    3. After fixing the configuration issues, re-run the pipeline.

## Build Images Stage Failing

???+ note "Symptom"

    Build Images stage is failing in the BuildStreaM pipeline.

??? note "Cause"

    - Playbook execution failed
    - Catalog does not have predefined functional groups

??? note "Resolution"

    1. Ensure the catalog has the predefined functional groups. For the supported functional groups, see the [BuildStreaM deployment guide](../../GetStarted/buildstream_deployment.md).

    2. If changes are required in the catalog, make the necessary modifications to the catalog.

    3. After fixing catalog issues, re-run the pipeline.

## Deploy Images Stage Failing

???+ note "Symptom"

    Deploy Images stage is failing in the BuildStreaM pipeline.

??? note "Cause"

    - Playbook execution failed
    - The functional groups listed in the PXE mapping file do not adhere to functional groups in the `catalog_rhel.json`

??? note "Resolution"

    1. Check the log path from the API response for detailed error information.

    2. Ensure the functional groups listed in the PXE mapping file matches the functional groups defined in the `catalog_rhel.json`.

    3. After making necessary modifications to the PXE mapping, re-run the pipeline manually.

## Retry Button Not Displayed

???+ note "Symptom"

    The Retry button is not displayed for failed pipeline stages, including deploy, restart, and validate operations.

??? note "Cause"

    The Retry button may not appear in certain failed pipeline stages due to GitLab issues.

??? note "Resolution"

    1. Initiate a restart from the parent pipeline to resolve this issue.

    2. This action restarts the entire pipeline from the beginning, allowing all stages to execute again.

## Parse Catalog Reports an Unsupported Schema Version

???+ note "Symptom"

    The **Parse Catalog** stage fails with an unsupported catalog schema
    version.

??? note "Cause"

    The value of `schema_version` is not supported by the installed
    BuildStreaM release.

??? note "Resolution"

    1. Compare the catalog with a sample under `src/main/samples/` from the
       same Omnia release.
    2. For a new Omnia 2.3 catalog, set `schema_version` to `2`.
    3. Validate the complete catalog and commit a new revision.

## Parse Catalog Reports a Duplicate Image Group

???+ note "Symptom"

    The **Parse Catalog** stage fails with a duplicate image-group error.

??? note "Cause"

    The composite catalog revision
    `<identifier>-v<version>` has already been used by another image group.

??? note "Resolution"

    1. Keep `identifier` and increment `version` when creating another
       revision of the same catalog family.
    2. Use a different `identifier` only when creating a different catalog
       family.
    3. Commit the catalog after confirming that the resulting composite value
       is unique.

## Catalog-Authoring Skill Cannot Resolve Package Metadata

???+ note "Symptom"

    A catalog-authoring skill cannot complete the requested operation because
    required package or catalog information is unavailable.

??? note "Cause"

    The request does not provide all required inputs, or the assistant cannot
    access the selected skill, its companion files, or the target catalog.

??? note "Resolution"

    1. Identify the skill operation and target catalog.
    2. Provide the package or component name, version, operating system,
       architecture, source, consuming role, and installation method when
       applicable.
    3. Confirm that the selected `SKILL.md`, its required companion files, and
       the catalog are from the same Omnia checkout.
    4. Retry the request. If required information remains unavailable, keep it
       unresolved instead of supplying an assumed value.

## Cadence Timer Does Not Start

???+ note "Symptom"

    `playbook-watcher.service` is active, but its journal reports that cadence
    polling is disabled or does not report a started cadence timer.

??? note "Cause"

    - `cadence.enabled` is `false`.
    - The staged `build_stream_config.yml` was not validated.

??? note "Resolution"

    1. Validate the staged BuildStreaM configuration with the `validate` tag.
    2. Allow the complete configured interval to elapse; the first cycle is
       not immediate.

## Cadence Cycle Does Not Start a Pipeline

???+ note "Symptom"

    The cadence interval elapsed, but no unified pipeline appears in GitLab.

??? note "Cause"

    - Another pipeline was running, so the cycle was suppressed.
    - Repository reconciliation did not complete successfully.
    - `repo_resync_status.yml` was missing, malformed, failed, or reported
      stale packages.
    - The cadence catalog commit could not be pushed.

??? note "Resolution"

    1. Review `journalctl -u playbook-watcher.service` for the suppression,
       reconciliation, or Git error.
    2. Inspect
       `$OMNIA_DATA_PATH/repo_manager/output/$OMNIA_PROJECT_NAME/repo_resync_status.yml`.
    3. Require successful aggregate, orphan-cleanup, synchronization, and
       cleanup states; zero stale packages; and valid package counters.

!!! info

    - [BuildStreaM](../../HowTo/build_stream/index.md) -- BuildStreaM and GitLab deployment procedures
    - [Execute Build Pipeline](../../HowTo/build_stream/execute_build_pipeline.md) -- Build pipeline operations
    - [Execute Deploy Pipeline](../../HowTo/build_stream/execute_deploy_pipeline.md) -- Deploy pipeline operations
    - [Automate Build and Deployment with Cadence](../../HowTo/build_stream/execute_cadence_pipeline.md) -- Cadence configuration and unified pipeline operations
    - [Retry Pipelines](../../Operations/build_stream/retry_pipelines.md) -- Retry failed pipeline operations
    - [Update Catalog](../../Operations/build_stream/update_catalog.md) -- Catalog configuration
    - [AI-Assisted Catalog Authoring](../../HowTo/build_stream/ai_catalog_authoring.md) -- Catalog generation, editing, analysis, and comparison
