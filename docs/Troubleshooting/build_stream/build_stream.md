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

    A catalog-authoring operation cannot resolve a package version, source,
    tag, supported OS, or architecture.

??? note "Cause"

    - Approved online package-repository access is unavailable.
    - The package is absent from the delivered master reference file.
    - The request does not identify enough package or target-catalog information.
    - The master reference file does not match the selected Omnia revision.

??? note "Resolution"

    1. Do not accept fabricated or model-inferred metadata.
    2. Verify online-source access and then check the delivered master reference
       file.
    3. If neither source contains the package, keep it flagged for manual
       review and do not synchronize or build from the partial catalog.
    4. Supply the missing OS, architecture, package source, version, or tag,
       then repeat the operation and review its evidence.

## Catalog Impact Analysis Is Incomplete

???+ note "Symptom"

    An impact or compatibility report lists direct catalog references but
    cannot determine transitive package or driver dependencies.

??? note "Cause"

    Online package-repository, upstream-documentation, or Red Hat compatibility
    access is unavailable. The fallback master reference file describes direct
    functional-layer relationships and recorded constraints but does not
    establish every transitive package dependency or upstream compatibility
    result.

??? note "Resolution"

    1. Review the evidence sources identified in the report.
    2. Confirm that the result identifies offline mode and discloses that
       transitive dependencies or the Red Hat Compatibility Matrix were not
       evaluated.
    3. Treat relationships not present in the master reference file as
       unresolved, not as compatible or unaffected.
    4. Restore access through the site-approved endpoint allowlist and repeat
       the analysis when an online result is required.

## Catalog Impact Analysis Has Repository Metadata for the Wrong Architecture

???+ note "Symptom"

    The catalog targets one architecture, but the analysis environment has
    local repository metadata only for another architecture.

??? note "Cause"

    The required architecture-specific repositories are not configured in the
    analysis environment, and an approved online source is unavailable.

??? note "Resolution"

    1. Do not silently substitute metadata from the available architecture.
    2. Configure local repositories for the target architecture, restore access
       to an approved online source, or explicitly approve the available
       architecture as a disclosed stand-in.
    3. If no option is acceptable, keep the affected finding unresolved and do
       not use it as evidence that the proposed change is safe.

## AI-Generated Catalog Fails Validation

???+ note "Symptom"

    A generated or edited catalog fails JSON, schema, package-resolution,
    architecture, or identifier checks.

??? note "Cause"

    - The generated content does not match the catalog format used by the
      selected Omnia revision.
    - A functional layer references a missing group or does not contain
      exactly one `base_os` group.
    - A group references a missing package, or a package source lacks fields
      required for its package type.
    - A `base_os` group does not declare `os` and `os_version`.
    - A new build reuses an existing `<identifier>-v<version>` value.
    - The reference data belongs to a different Omnia or catalog revision.

??? note "Resolution"

    1. Do not write, merge, synchronize, or build from the invalid catalog.
    2. Compare it with the samples under `src/main/samples/` and the
       [Catalog JSON reference](../../Reference/SampleFiles/catalog_json.md).
    3. Correct missing references, base-OS metadata, package sources, and other
       reported validation errors.
    4. Increment `version` for another revision of the same catalog family,
       or use a new `identifier` for a different catalog family.
    5. Repeat validation and submit the change through the normal Merge Request
       review process.

## Catalog Selection Is Refused

???+ note "Symptom"

    The skill refuses an OS, architecture, stack, node-role, GPU, storage, or
    network selection.

??? note "Cause"

    The master reference file does not mark the selection as `supported`, or
    a recorded constraint makes it incompatible with an earlier selection.

??? note "Resolution"

    1. Review the reported `support_status`, constraint, and supported
       alternatives.
    2. Explicitly select a supported alternative or correct an earlier
       selection.
    3. Do not ask the skill to infer or silently substitute a similar option.

## Operator-Supplied Repository URL Is Missing

???+ note "Symptom"

    A generated catalog reports that a repository URL is required before
    synchronization.

??? note "Cause"

    The package source uses a repository whose URL is intentionally supplied
    by the operator rather than recorded as a default.

??? note "Resolution"

    1. Obtain the approved repository URL from the site administrator.
    2. Do not use an AI-inferred URL.
    3. Configure the URL and confirm that the catalog's repository name is
       mapped for the selected OS version and architecture in
       `repo_manager_config.yml` before synchronization. When subscription
       access is disabled, every referenced RPM repository requires an
       explicit URL.

## Catalog Edit Is Not Applied

???+ note "Symptom"

    The skill presents findings but does not modify the catalog.

??? note "Cause"

    - Explicit operator approval was not provided.
    - The operator declined the proposed edit.
    - The proposed output failed schema validation.
    - The requested destination is outside the source catalog tree under
      `src/main/samples/catalogs/`.

??? note "Resolution"

    1. Review the impact and compatibility findings and any fallback
       disclosure.
    2. Correct unresolved data or schema violations.
    3. Confirm that the destination is under `src/main/samples/catalogs/`.
    4. Explicitly approve the revised proposal if the change should proceed.

## Bulk Catalog Edit Is Partially Applied

???+ note "Symptom"

    Some matching catalogs are updated while others are listed as skipped.

??? note "Cause"

    Each catalog is validated independently. A matching catalog that would
    fail schema validation remains unchanged while other valid catalogs can be
    updated.

??? note "Resolution"

    1. Review the changed, skipped, and unaffected catalog lists.
    2. Confirm that every skipped catalog is unchanged.
    3. Correct each reported schema violation and request the edit again only
       for the affected catalog.

## Browser-Based Assistant Cannot Access Catalog Files

???+ note "Symptom"

    The assistant cannot read or write a catalog repository.

??? note "Cause"

    The browser-based invocation channel has no direct file-system access.

??? note "Resolution"

    1. For catalog generation or editing, paste the complete catalog content
       required for the operation.
    2. Request the complete resulting catalog, then validate and apply it
       manually within the catalog repository.
    3. Do not use a browser-only assistant to generate an exhaustive reversible
       semantic diff. Run `catalog_manager.py diff` from a channel with shell
       access.

## Semantic Catalog Diff Is Rejected

???+ note "Symptom"

    The comparison produces no diff, or its reverse operation does not restore
    the current catalog.

??? note "Cause"

    - The current or future catalog does not conform to the catalog schema.
    - One input uses the legacy uppercase `Catalog` root instead of the
      lowercase Schema 2 `catalog` root.
    - The deterministic comparison engine could not verify its forward or
      reverse reconstruction invariant.

??? note "Resolution"

    1. Correct every reported schema violation in both input catalogs.
    2. If an input uses the legacy catalog format, convert it with
       `catalog_manager.py transform` and validate the converted file.
    3. Regenerate the machine-readable forward and reverse diffs with
       `catalog_manager.py diff`.
    4. Do not apply the change set unless the command completes its internal
       forward and reverse reconstruction checks successfully.

## Semantic Catalog Diff Reports a Blocking Warning

???+ note "Symptom"

    The changelog contains `[BLOCKING] CON-004` even though the comparison
    command generated its output files.

??? note "Cause"

    Kubernetes component minor-version pins disagree in the proposed future
    catalog. Diff generation and compatibility-warning evaluation are separate,
    so the command can generate the comparison artifacts while reporting a
    blocking catalog condition.

??? note "Resolution"

    1. Do not promote the future catalog or start a build from it.
    2. Align the affected Kubernetes component pins.
    3. Validate the corrected catalog and regenerate both machine-readable
       diffs and the changelog.

## HTML Catalog Changelog Is Not Created

???+ note "Symptom"

    The JSON diffs and Markdown changelog are generated, but the requested HTML
    changelog is absent.

??? note "Cause"

    Jinja2 is not installed in the environment running `catalog_manager.py`.

??? note "Resolution"

    Review the Markdown changelog, which remains available without Jinja2. If
    HTML output is required, install the site-approved Jinja2 package and repeat
    the comparison with `--output-html`.

## Cadence Timer Does Not Start

???+ note "Symptom"

    `playbook-watcher.service` is active, but its journal reports that cadence
    polling is disabled or does not report a started cadence timer.

??? note "Cause"

    - `cadence.enabled` is `false`.
    - The staged `build_stream_config.yml` was not validated.
    - `cadence.gitlab_repo_path` is empty.
    - The watcher was not restarted after the configuration changed.

??? note "Resolution"

    1. Validate the staged BuildStreaM configuration with the `validate` tag.
    2. Confirm that `gitlab_repo_path` identifies a writable local Git clone
       containing `cadence_catalog_rhel.json`.
    3. Restart `playbook-watcher.service` and review its journal.
    4. Allow the complete configured interval to elapse; the first cycle is
       not immediate.

## Cadence Cycle Does Not Start a Pipeline

???+ note "Symptom"

    The cadence interval elapsed, but no unified pipeline appears in GitLab.

??? note "Cause"

    - Another watcher request was active, so the cycle was suppressed.
    - Reconciliation succeeded without package additions or removals.
    - `repo_resync_status.yml` was missing, malformed, failed, or reported
      stale packages.
    - The cadence catalog commit could not be pushed.

??? note "Resolution"

    1. Review `journalctl -u playbook-watcher.service` for the suppression,
       no-update, reconciliation, or Git error.
    2. Inspect
       `$OMNIA_DATA_PATH/repo_manager/output/$OMNIA_PROJECT_NAME/repo_resync_status.yml`.
    3. Require successful aggregate, orphan-cleanup, synchronization, and
       cleanup states; zero stale packages; and valid package counters.
    4. If changes were detected, verify the local clone's branch, remote,
       connectivity, and noninteractive push authentication.

## Unified Cadence Pipeline Stops Between Stages

???+ note "Symptom"

    A cadence job reports that `JOB_ID` or `IMAGE_GROUP_ID` is missing, or a
    later stage does not start.

??? note "Cause"

    The initialization or parse-catalog job did not publish its required
    dotenv artifact, or an earlier stage failed.

??? note "Resolution"

    1. Review the initialization and parse-catalog job logs first.
    2. Correct the reported upload, catalog, or BSM API failure.
    3. Retry the complete downstream pipeline after resolving the cause.
    4. Do not treat catalog-mode cadence artifacts as an automatic `_prev`
       rollback; catalog mode does not create that backup.

!!! info

    - [BuildStreaM](../../HowTo/build_stream/index.md) -- BuildStreaM and GitLab deployment procedures
    - [Execute Build Pipeline](../../HowTo/build_stream/execute_build_pipeline.md) -- Build pipeline operations
    - [Execute Deploy Pipeline](../../HowTo/build_stream/execute_deploy_pipeline.md) -- Deploy pipeline operations
    - [Automate Build and Deployment with Cadence](../../HowTo/build_stream/execute_cadence_pipeline.md) -- Cadence configuration and unified pipeline operations
    - [Retry Pipelines](../../Operations/build_stream/retry_pipelines.md) -- Retry failed pipeline operations
    - [Update Catalog](../../Operations/build_stream/update_catalog.md) -- Catalog configuration
    - [AI-Assisted Catalog Authoring](../../HowTo/build_stream/ai_catalog_authoring.md) -- Catalog generation, editing, analysis, and comparison



