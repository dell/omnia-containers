# Automate Build and Deployment with Cadence

## Overview

Use the optional BuildStreaM cadence workflow to periodically reconcile the
RPM repositories referenced by a designated catalog and, after successful
reconciliation, build and deploy the resulting images in one GitLab pipeline.

When enabled, the playbook watcher waits for the configured interval, verifies
that no other pipeline is running, and runs catalog-scoped RPM reconciliation.
Repository resynchronization must complete successfully, irrespective of
whether package additions or removals are detected. After a successful
reconciliation, BuildStreaM increments
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
- Wait for operations that use the same catalog, repository, image, or target
  nodes to finish before enabling cadence.

## Procedure

1. On the OIM, open the staged BuildStreaM configuration:

    ```text
    $OMNIA_DATA_PATH/build_stream/input/$OMNIA_PROJECT_NAME/build_stream_config.yml
    ```

    The default project is `project_default`.

2. Configure the `cadence` mapping:

    ```yaml
    cadence:
      # Enable or disable cadence polling for periodic package synchronization
      # Accepted values: true | false
      # Default: false
      enabled: true

      # Polling interval for cadence syncs in days
      # Accepted values: integer >= 1 (1 day minimum)
      # Default: 7 (7 days)
      interval_days: 7

      # Timeout for repo sync playbook execution in seconds
      # Default: 3600 (1 hour)
      sync_timeout_seconds: 3600

      # Poll interval while waiting for sync result in seconds
      # Default: 10
      sync_poll_interval_seconds: 10
    ```

    Use the following constraints:

    | Parameter | Constraint | Default |
    |---|---|---|
    | `enabled` | Boolean | `false` |
    | `interval_days` | Integer greater than or equal to `1` | `7` |
    | `sync_timeout_seconds` | Integer greater than or equal to `60` | `3600` |
    | `sync_poll_interval_seconds` | Integer from `1` through `300` | `10` |

3. Validate the configuration:

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run build_stream --tags validate
    ```

4. Allow the watcher to run automatically. The first reconciliation begins
   after `interval_days`.

5. To run the unified pipeline manually without waiting for reconciliation:

    1. In the managed GitLab project, navigate to **Build** > **Pipelines**.
    2. Click **New pipeline**.
    3. Add the variable `PIPELINE_TYPE` with the value `cadence`.
    4. Click **Run pipeline**.

    ![Cadence Pipeline](../../assets/images/cadence_pipeline.png)

    A manual cadence pipeline uses the current `cadence_catalog_rhel.json` and
    starts the unified lifecycle directly. Starting the pipeline manually
    bypasses periodic repository reconciliation.

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
    `stale_packages_remaining`, and nonnegative integer package counters. The
    resynchronization must succeed whether or not the counters report package
    additions or removals.

3. For a successful reconciliation, confirm that:

    - `cadence_catalog_rhel.json` has a new `catalog.version` and a cadence Git
      commit on the configured branch.
    - GitLab displays all eight cadence stages.
    - The pipeline summary reports the `JOB_ID` and composite
      `IMAGE_GROUP_ID` used for the execution.
    - The target nodes restart with the newly built image and the validation
      stage succeeds.

### Monitoring Cadence Health

Cadence runs automatically at configured intervals to synchronize repositories and trigger builds. Because cadence operates without manual intervention, you must actively monitor its health to detect failures that may occur due to network issues, unreachable repositories, catalog errors, or other problems.

#### Log Locations

Cadence-related logs are stored in the following locations:

| Log Type | Location | Purpose |
|---|---|---|
| Service journal | `journalctl -u playbook-watcher.service` | Systemd journal for the playbook-watcher service, including cadence timer events and reconciliation results |
| Cadence execution logs | `$OMNIA_DATA_PATH/build_stream/log/cadence-*/` | Detailed logs for each cadence execution cycle |
| Repository sync status | `$OMNIA_DATA_PATH/repo_manager/output/$OMNIA_PROJECT_NAME/repo_resync_status.yml` | Repository reconciliation status and results |
| BuildStreaM events | `$OMNIA_DATA_PATH/log/build_stream/events.log` | BuildStreaM API events and authentication logs |

`OMNIA_DATA_PATH` defaults to `/opt/omnia` if not customized.

#### Monitoring Commands

**Check Cadence Timer Status**

Verify that the cadence timer is active and running:

```bash title="Run on: OIM host"
systemctl status playbook-watcher.service
```

The service should show as `active (running)`.

**View Recent Cadence Events**

Review the playbook-watcher journal for cadence-related events:

```bash title="Run on: OIM host"
journalctl -u playbook-watcher.service --no-pager
```

To filter for cadence-specific messages:

```bash title="Run on: OIM host"
journalctl -u playbook-watcher.service --no-pager | grep -i cadence
```

To view events from a specific time range (for example, the last 24 hours):

```bash title="Run on: OIM host"
journalctl -u playbook-watcher.service --since "24 hours ago" --no-pager
```

**Check Repository Reconciliation Status**

After a cadence cycle runs, inspect the repository synchronization status:

```bash title="Run on: OIM host"
cat $OMNIA_DATA_PATH/repo_manager/output/$OMNIA_PROJECT_NAME/repo_resync_status.yml
```

Confirm that:
- `overall_status` is `success`
- `orphan_cleanup` is `success`
- All repositories report successful synchronization
- `stale_packages_remaining` is `0`
- Package counters are nonnegative integers

**View Cadence Execution Logs**

Cadence execution logs are organized by timestamp in directories named `cadence-<timestamp>`:

```bash title="Run on: OIM host"
ls -la $OMNIA_DATA_PATH/build_stream/log/cadence-*/
```

To view the most recent cadence execution log:

```bash title="Run on: OIM host"
ls -t $OMNIA_DATA_PATH/build_stream/log/cadence-*/ | head -1 | xargs -I {} cat $OMNIA_DATA_PATH/build_stream/log/{}/cadence.log
```

#### Failure Indicators

Monitor for these common failure indicators:

| Indicator | Location | Description |
|---|---|---|
| Cadence timer not started | `journalctl -u playbook-watcher.service` | Journal does not report a started cadence timer |
| Reconciliation failed | `repo_resync_status.yml` | `overall_status` is not `success` |
| Repository unreachable | `journalctl -u playbook-watcher.service` | Error messages about unreachable repository URLs |
| Catalog commit failed | `journalctl -u playbook-watcher.service` | Git push errors for `cadence_catalog_rhel.json` |
| Pipeline not triggered | GitLab Pipelines page | No pipeline appears after successful reconciliation |
| Stale packages detected | `repo_resync_status.yml` | `stale_packages_remaining` is greater than `0` |

#### Recommended Monitoring Practices

1. **Daily Log Review**: Check `journalctl -u playbook-watcher.service` daily for any error messages or failed cadence cycles.

2. **Automated Monitoring**: Set up a monitoring system to alert on:
   - `playbook-watcher.service` status changes
   - Journal entries containing "ERROR" or "FAILED" related to cadence
   - Missing cadence cycles beyond the expected interval

3. **Post-Cadence Verification**: After each expected cadence cycle:
   - Verify that `cadence_catalog_rhel.json` has a new `catalog.version`
   - Confirm that a new GitLab pipeline was triggered
   - Check that the pipeline completed successfully

4. **Repository Health**: Periodically verify that all repositories referenced in the cadence catalog are reachable from the OIM.

#### Common Failure Scenarios

**Repository Unreachable**

**Symptom**: Cadence fails with error about missing repository URLs or unreachable repositories.

**Resolution**:
1. Check network connectivity to the repository from the OIM
2. Verify repository URLs in the catalog are correct
3. Ensure authentication credentials (if required) are valid
4. Check repository availability and status

**Service Restart**

**Symptom**: Cadence timer resets after `playbook-watcher.service` restart.

**Resolution**: This is expected behavior. The timer restarts with the configured interval after service restart. Allow the complete interval to elapse for the next cycle.

**Concurrent Pipeline**

**Symptom**: Cadence cycle is suppressed with no pipeline triggered.

**Resolution**: An existing pipeline was running when cadence attempted to start. Allow the running pipeline to complete and wait for the next interval.

## Next steps

- Review the [Catalog JSON reference](../../Reference/SampleFiles/catalog_json.md).
- Use [Cleanup Operations](cleanup_operations.md)
  to remove image groups that are no longer required.

## Troubleshooting

- **The timer does not start:** Confirm that `cadence.enabled` is `true`, the
  staged configuration is valid, and `playbook-watcher.service` is active.
- **The first cycle has not run:** The watcher waits for the complete
  `interval_days` value before its first cycle.
- **Cadence Pipeline is not triggered periodically:** If RPM reconciliation via repo_resync.yml fails, there will be no cadence pipeline invoked.
- **The cycle is suppressed:** An active pipeline causes cadence to skip that
  cycle. Allow the pipeline to finish and wait for the next interval.
- **The reconciliation result is rejected:** Correct any failed aggregate or
  repository status, failed orphan cleanup, nonzero stale-package count, or
  invalid package counter in the Repository Manager workflow.
- **A pipeline stage reports a missing identifier:** Review the
  `initialization` and `parse-catalog` jobs. Dependent stages do not run
  without their `JOB_ID` and `IMAGE_GROUP_ID` artifacts.
- **The unified pipeline fails:** Open the failed GitLab job and correct the
  reported build, deployment, restart, or validation problem. Catalog-mode
  cadence builds do not create a `*_prev` S3 rollback copy.
- **Cadence fails without notification:** Cadence failures are logged but do not trigger automatic alerts. Monitor the playbook-watcher journal, repository sync status, and cadence execution logs. See [Monitoring Cadence Health](#monitoring-cadence-health) for detailed procedures.
- For additional issues, see
  [BuildStreaM Issues](../../Troubleshooting/build_stream/build_stream.md).
