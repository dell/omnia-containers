# BuildStreaM Troubleshooting

Diagnose and resolve common BuildStreaM issues including pipeline stage
failures, container service problems, GitLab errors, and runner
configuration issues.

## Overview

BuildStreaM integrates multiple components: GitLab, GitLab Runner,
the BuildStreaM API server, PostgreSQL database, Playbook Watcher,
and the Omnia playbook engine. Failures can occur at any pipeline stage.
This guide provides systematic troubleshooting for each component.

## Prerequisites

- GitLab is deployed (see [Deploy GitLab](deploy_gitlab.md)).
- A BuildStreaM catalog is configured (see [Update Catalog & Pipelines](update_catalog_pipeline.md)).
- `root` access to the OIM host and the omnia_core container.

## Procedure

### BuildStreaM service failures

1. **Verify BuildStreaM services are running**:

    ```bash title="Run on: OIM host"
    systemctl status omnia_build_stream.service
    systemctl status omnia_postgres.service
    systemctl status playbook_watcher.service
    ```

2. **Check BuildStreaM service logs**:

    ```bash title="Run on: OIM host"
    journalctl -u omnia_build_stream --no-pager
    journalctl -u omnia_postgres --no-pager
    ```

3. **Check authentication logs**:

    ```bash title="Run on: OIM host"
    cat /<nfs-dir>/omnia/log/build_stream/auth.log
    ```

### Pipeline stage failures

4. **View pipeline logs** in GitLab:

    Navigate to **Build** > **Pipelines** > click the failed pipeline >
    click the failed job. Read the job output from bottom to top for the
    error.

5. **Check job-specific logs on the OIM**:

    ```bash title="Run on: OIM host"
    ls /<nfs-dir>/omnia/log/build_stream/<job-id>/
    cat /<nfs-dir>/omnia/log/build_stream/<job-id>/<jobid>.log
    ```

6. **Common parse-catalog failures**:

    - Invalid JSON schema format in `catalog_rhel.json`.
    - Catalog structure does not match expected schema.
    - Verify against reference examples at `https://github.com/dell/omnia/tree/pub/build_stream/examples/catalog`.

7. **Common create-local-repository failures**:

    - Playbook execution failed. Check the `log_file_path` field in the API response.
    - Configuration issues in `local_repo_config.yml`.

8. **Common build-image failures**:

    - The catalog does not have predefined functional groups.
    - Playbook execution errors. Check the API response log path.

9. **Common deploy failures**:

    - Functional groups in PXE mapping file do not match `catalog_rhel.json`.
    - Check the API response log path for detailed error information.

### GitLab and runner issues

10. **GitLab is unresponsive or slow**:

    ```bash title="Run on: GitLab node"
    podman stats gitlab --no-stream
    podman logs gitlab --tail=30
    ```

11. **Runner is offline or not picking up jobs**:

    Navigate to **Settings** > **CI/CD** > **Runners** in GitLab.
    Verify the runner shows a green status indicator.

12. **Runner jobs time out**:

    Increase the job timeout in GitLab:

    - Navigate to **Settings** > **CI/CD** > **General pipelines** > **Timeout**.
    - Set to `2 hours` or longer for provisioning and build jobs.

### Registry issues

13. **Container registry is unreachable**:

    ```bash title="Run on: OIM host"
    systemctl status registry.service
    podman logs registry
    ```

    Restart the registry:

    ```bash title="Run on: OIM host"
    systemctl restart registry.service
    ```

14. **Image push/pull fails**:

    ```bash title="Run on: OIM host"
    curl -s http://localhost:5000/v2/_catalog
    ```

### General debugging

15. **Check system resources** on the OIM:

    ```bash title="Run on: OIM host"
    df -h
    free -h
    podman ps -a
    podman stats --no-stream
    ```

## Verification

After resolving issues, verify the pipeline works end-to-end:

1. Make a trivial change to the catalog or input files.
2. Push the change and verify the pipeline triggers.
3. Confirm all stages complete with green checkmarks.

## Next Steps

- [Update Catalog & Pipelines](update_catalog_pipeline.md) -- Resume catalog-driven deployments.
- [Deploy GitLab](deploy_gitlab.md) -- Reconfigure GitLab if needed.
- [Retry Pipelines](retry_pipelines.md) -- Retry failed pipeline operations.

## Troubleshooting

!!! note

    This page **is** the troubleshooting how-to for BuildStreaM. For
    the Symptom/Cause/Resolution reference, see
    [BuildStreaM Issues](../../Troubleshooting/buildstream.md).

    Additional log locations:

    - BuildStreaM API logs: `journalctl -u omnia_build_stream`
    - PostgreSQL logs: `journalctl -u omnia_postgres`
    - Playbook Watcher logs: `journalctl -u playbook_watcher`
    - Job-specific logs: `/<nfs-dir>/omnia/log/build_stream/<job-id>/`
    - Authentication logs: `/<nfs-dir>/omnia/log/build_stream/auth.log`
