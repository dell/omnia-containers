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

## Catalog-Authoring Skill Cannot Resolve Package Metadata

???+ note "Symptom"

    A catalog-authoring operation cannot resolve a package version, source,
    tag, supported OS, or architecture.

??? note "Cause"

    - The package is absent from the supplied master catalogs or reference files.
    - The request does not identify enough package or target-catalog information.
    - The supplied reference data does not match the selected Omnia revision.

??? note "Resolution"

    1. Do not accept fabricated or model-inferred metadata.
    2. Verify the package against an approved catalog, repository, or reference
       file.
    3. Supply the missing OS, architecture, package source, version, or tag.
    4. Repeat the operation and review its evidence before applying the change.

## Catalog Impact Analysis Is Incomplete

???+ note "Symptom"

    An impact or compatibility report lists direct catalog references but
    cannot determine transitive package or driver dependencies.

??? note "Cause"

    Catalogs and adapter policies describe direct catalog relationships but do
    not provide every RPM dependency, kernel-to-driver constraint, or upstream
    compatibility rule. The supplied inputs do not include a package-dependency
    or compatibility data source for those relationships.

??? note "Resolution"

    1. Review the evidence sources identified in the report.
    2. Treat unverified transitive dependencies as unresolved risk.
    3. Supply an approved package-dependency or compatibility data source.
    4. Complete package and platform compatibility review before merging the
       catalog change.

## AI-Generated Catalog Fails Validation

???+ note "Symptom"

    A generated or edited catalog fails JSON, schema, package-resolution,
    architecture, or identifier checks.

??? note "Cause"

    - The generated content does not match the catalog format used by the
      selected Omnia revision.
    - Package metadata or functional-layer placement is incomplete.
    - A new build reuses an existing catalog identifier.
    - The reference data belongs to a different Omnia or catalog revision.

??? note "Resolution"

    1. Do not merge the generated catalog or start a new build from it.
    2. Compare it with the sample catalog and schema delivered with the same
       Omnia source revision.
    3. Review the machine-readable diff and correct unsupported or unresolved
       values.
    4. Assign a unique catalog identifier when the change represents a new
       build.
    5. Repeat validation and submit the change through the normal Merge Request
       review process.

!!! info

    - [BuildStreaM](../../HowTo/build_stream/index.md) -- BuildStreaM and GitLab deployment procedures
    - [Execute Build Pipeline](../../HowTo/build_stream/execute_build_pipeline.md) -- Build pipeline operations
    - [Execute Deploy Pipeline](../../HowTo/build_stream/execute_deploy_pipeline.md) -- Deploy pipeline operations
    - [Retry Pipelines](../../Operations/build_stream/retry_pipelines.md) -- Retry failed pipeline operations
    - [Update Catalog](../../Operations/build_stream/update_catalog.md) -- Catalog configuration
    - [NERSC AI Catalog Authoring](../../HowTo/build_stream/ai_catalog_authoring.md) -- AI-assisted catalog generation, editing, analysis, and review










