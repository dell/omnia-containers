# Automate Build and Deployment with Cadence

## Overview

Use the optional BuildStreaM cadence workflow to periodically reconcile the
RPM repositories referenced by a designated catalog and, when package content
changes, build and deploy the resulting images in one GitLab pipeline.

Cadence is disabled by default. When enabled, the playbook watcher waits for
the configured interval, verifies that no other watcher request is active,
and runs catalog-scoped RPM reconciliation. A successful reconciliation with
no package additions or removals ends without changing the catalog or starting
a pipeline. When packages changed, BuildStreaM increments
`catalog.version`, commits and pushes `cadence_catalog_rhel.json`, and GitLab
runs these stages:

```text
initialization
-> parse-catalog
-> configure-local-repository
-> build-images
-> deploy
-> restart
-> validate
-> summary
```

The deploy, restart, and validation stages use the image-group identifier
created by the same pipeline execution. The existing build-only and
deploy-only pipelines remain independently available.

!!! note

    Cadence configuration is stored in `build_stream_config.yml`, not in the
    catalog JSON. `cadence_catalog_rhel.json` contains the catalog input whose
    committed changes select the unified cadence pipeline.

## Prerequisites

- Deploy BuildStreaM and its managed GitLab project. See
  [BuildStreaM](index.md).
- Verify that `omnia_postgres.service`, `omnia_build_stream.service`, and
  `playbook-watcher.service` are active on the OIM.
- Verify that `cadence_catalog_rhel.json` exists at the root of the managed
  GitLab project.
- Configure every RPM repository referenced by the cadence catalog and verify
  that its upstream source is reachable from the OIM.
- Complete the Image Build Manager inputs and
  `input/orchestrator/pxe_mapping_file.csv` in the managed GitLab project.
- Provide a build host for every architecture present in the cadence catalog.
  An aarch64 image requires a native aarch64 build host.
- Create a writable local clone of the managed GitLab project on the OIM. The
  clone must track the configured GitLab default branch and be able to push
  without an interactive credential prompt.
- Wait for operations that use the same catalog, repository, image, or target
  nodes to finish before enabling or manually starting cadence.

## Procedure

1. On the OIM, open the staged BuildStreaM configuration:

    ```text
    $OMNIA_DATA_PATH/build_stream/input/$OMNIA_PROJECT_NAME/build_stream_config.yml
    ```

    The default project is `project_default`.

2. Configure the `cadence` mapping. Replace the example repository path with
   the absolute path of the writable local GitLab clone:

    ```yaml
    cadence:
      enabled: true
      interval_seconds: 86400
      catalog_filename: "cadence_catalog_rhel.json"
      gitlab_repo_path: "/path/to/local/omnia-catalog-clone"
      playbook_name: "repo_sync.yml"
      sync_timeout_seconds: 3600
      sync_poll_interval_seconds: 10
    ```

    Use the following constraints:

    | Parameter | Constraint | Default |
    |---|---|---|
    | `enabled` | Boolean | `false` |
    | `interval_seconds` | Integer greater than or equal to `3600` | `86400` |
    | `catalog_filename` | JSON filename without directory components | `cadence_catalog_rhel.json` |
    | `gitlab_repo_path` | Nonempty local Git repository path when cadence is enabled | Empty |
    | `playbook_name` | Retain the allow-listed `repo_sync.yml` value | `repo_sync.yml` |
    | `sync_timeout_seconds` | Integer greater than or equal to `60` | `3600` |
    | `sync_poll_interval_seconds` | Integer from `1` through `300` | `10` |

3. Validate the configuration:

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run build_stream --tags validate
    ```

4. Restart the watcher so it loads the updated cadence configuration:

    ```bash title="Run on: OIM host"
    sudo systemctl restart playbook-watcher.service
    ```

5. Allow the watcher to run automatically. The first reconciliation begins
   after `interval_seconds`; restarting the service does not start an
   immediate reconciliation.

6. To run the unified pipeline manually without waiting for reconciliation:

    1. In the managed GitLab project, navigate to **Build** > **Pipelines**.
    2. Click **New pipeline**.
    3. Add the variable `PIPELINE_TYPE` with the value `cadence`.
    4. Click **Run pipeline**.

    A manual cadence pipeline uses the current `cadence_catalog_rhel.json` and
    starts the unified lifecycle directly. It does not first run the periodic
    repository-reconciliation decision.

## Verification

1. Verify the watcher service and confirm that the cadence timer started:

    ```bash title="Run on: OIM host"
    systemctl status playbook-watcher.service
    journalctl -u playbook-watcher.service --no-pager
    ```

    The journal reports the configured interval when the timer starts.

2. After an automatic reconciliation, inspect:

    ```text
    $OMNIA_DATA_PATH/repo_manager/output/$OMNIA_PROJECT_NAME/repo_resync_status.yml
    ```

    Confirm that `overall_status` and `orphan_cleanup` are `success`. Every
    repository must report successful synchronization and cleanup, zero
    `stale_packages_remaining`, and nonnegative integer package counters.

3. For a reconciliation that finds no package additions or removals, confirm
   that the watcher reports no package updates and that it did not change the
   cadence catalog or start a GitLab pipeline.

4. For a reconciliation that finds changes, confirm that:

    - `cadence_catalog_rhel.json` has a new `catalog.version` and a cadence Git
      commit on the configured branch.
    - GitLab displays all eight cadence stages.
    - The pipeline summary reports the `JOB_ID` and composite
      `IMAGE_GROUP_ID` used for the execution.
    - The target nodes restart with the newly built image and the validation
      stage succeeds.

## Next steps

- [Execute Build Pipeline](execute_build_pipeline.md) to build images without
  deploying them.
- [Execute Deploy Pipeline](execute_deploy_pipeline.md) to deploy an existing
  image group independently.
- Review the [Catalog JSON reference](../../Reference/SampleFiles/catalog_json.md).
- Use [Cleanup Operations](../../Operations/build_stream/cleanup_operations.md)
  to remove image groups that are no longer required.

## Troubleshooting

- **The timer does not start:** Confirm that `cadence.enabled` is `true`, the
  staged configuration is valid, and `playbook-watcher.service` was restarted.
- **The first cycle has not run:** The watcher waits for the complete
  `interval_seconds` value before its first cycle.
- **The local repository is rejected:** Confirm that `gitlab_repo_path` is an
  absolute path to a writable Git repository containing
  `cadence_catalog_rhel.json`.
- **The catalog cannot be pushed:** Verify the clone's remote, branch, network
  connectivity, and noninteractive Git authentication. Review the clone's
  commit state before changing the catalog version again.
- **The cycle is suppressed:** An active JSON request in the watcher processing
  queue causes cadence to skip that cycle. Allow the operation to finish and
  wait for the next interval.
- **No pipeline starts after a successful cycle:** If all `packages_added` and
  `packages_removed` values are zero, no pipeline is expected.
- **The reconciliation result is rejected:** Correct any failed aggregate or
  repository status, failed orphan cleanup, nonzero stale-package count, or
  invalid package counter in the Repository Manager workflow.
- **A pipeline stage reports a missing identifier:** Review the
  `initialization` and `parse-catalog` jobs. Dependent stages do not run
  without their `JOB_ID` and `IMAGE_GROUP_ID` artifacts.
- **The unified pipeline fails:** Open the failed GitLab job and correct the
  reported build, deployment, restart, or validation problem. Catalog-mode
  cadence builds do not create a `*_prev` S3 rollback copy.
- For additional issues, see
  [BuildStreaM Issues](../../Troubleshooting/build_stream/build_stream.md).
