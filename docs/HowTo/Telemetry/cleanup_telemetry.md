# Clean Up Telemetry

## Overview

Telemetry supports selective sink cleanup, independent source cleanup, and
full cleanup. Choose the narrowest operation that matches the intended scope.

!!! warning

    Source cleanup permanently deletes source-owned persistent volumes. Sink
    volumes are preserved by default, but they are permanently deleted when
    `Delete_sinks_volume=true` is specified. Back up any required data before
    cleanup.

## Prerequisites

- Run cleanup while the service Kubernetes cluster is available.
- Ensure that the OIM can reach the Kubernetes control-plane VIP over SSH as
  `root`.
- Back up Telemetry data, credentials, and logs that must be retained.
- Run `omnia.sh` commands from `<OMNIA_SOURCE_PATH>/src/main`.

## Clean up sinks

The `cleanup_sinks` operation removes selected sink infrastructure. Before
cleanup, Telemetry detects running sources that depend on each requested sink.
If any requested sink has a dependency, the entire selective cleanup is
aborted. No requested sink is removed when this dependency check fails.

Sink persistent volumes are preserved by default. The operation removes the
Helm releases, Kubernetes pods, services, and ConfigMaps associated with each
selected sink.

Run the applicable command.

Clean up Kafka only:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run telemetry --tags cleanup_sinks -e sinks=kafka
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
    ansible-playbook telemetry.yml --tags cleanup_sinks -e sinks=kafka
    ```

Clean up Kafka and VictoriaMetrics:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run telemetry --tags cleanup_sinks -e sinks=kafka,victoria_metrics
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
    ansible-playbook telemetry.yml --tags cleanup_sinks -e sinks=kafka,victoria_metrics
    ```

Clean up Kafka, VictoriaMetrics, and VictoriaLogs:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run telemetry --tags cleanup_sinks
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
    ansible-playbook telemetry.yml --tags cleanup_sinks
    ```

Valid sink names are `kafka`, `victoria_metrics`, and `victoria_logs`.
Specify multiple sinks as a comma-separated list without spaces.

To delete a selected sink's persistent volumes as part of cleanup, set
`Delete_sinks_volume=true`:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run telemetry --tags cleanup_sinks \
      -e sinks=kafka \
      -e Delete_sinks_volume=true
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
    ansible-playbook telemetry.yml --tags cleanup_sinks \
      -e sinks=kafka \
      -e Delete_sinks_volume=true
    ```

!!! warning

    When `Delete_sinks_volume=true`, Telemetry always deletes credentials and
    logs, regardless of the `cleanup_credentials` or `cleanup_logs` values.

## Clean up sources

Source cleanup removes one Telemetry source without affecting other sources or
sinks. It removes the source pods, services, ConfigMaps, and source-owned
persistent volumes.

Run the applicable source cleanup command:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run telemetry --tags cleanup_<source>
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
    ansible-playbook telemetry.yml --tags cleanup_<source>
    ```

Replace `<source>` with `idrac`, `ldms`, `powerscale`, `ufm`, `vast`, or `ome`.
Run only the command for the source that must be removed. Use the enable and
disable procedure on the corresponding source page when the source must be
disabled without removing its infrastructure.

## Run full cleanup

Full cleanup removes all Telemetry sources and sinks unconditionally. Sources
are drained first, and then all sinks are cleaned. Source-owned persistent
volumes are always deleted. Sink volumes are preserved by default.

Run full cleanup:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run telemetry --tags cleanup
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
    ansible-playbook telemetry.yml --tags cleanup
    ```

To delete sink volumes too:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run telemetry --tags cleanup -e Delete_sinks_volume=true
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
    ansible-playbook telemetry.yml --tags cleanup -e Delete_sinks_volume=true
    ```

Use `cleanup_credentials=false` to preserve credentials and
`cleanup_logs=false` to preserve logs:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run telemetry --tags cleanup \
      -e cleanup_credentials=false \
      -e cleanup_logs=false
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
    ansible-playbook telemetry.yml --tags cleanup \
      -e cleanup_credentials=false \
      -e cleanup_logs=false
    ```

The preservation settings do not apply when `Delete_sinks_volume=true` is
specified. In that case, credentials and logs are always deleted.

## Verification

1. Inspect the remaining Telemetry resources:

    ```bash title="Run on: Kubernetes control-plane VIP"
    kubectl get pods,services,configmaps,persistentvolumeclaims -n telemetry
    ```

2. Confirm that:

    - Selective sink cleanup removed all requested sinks or removed none when a
      dependency blocked the operation.
    - Source cleanup removed only the requested source and its source-owned
      volumes.
    - Full cleanup removed all source and sink workloads.
    - Sink PVCs remain unless `Delete_sinks_volume=true` was specified.

3. Review the cleanup result:

    ```bash title="Run on: OIM"
    cat "${OMNIA_DATA_PATH:-/opt/omnia}/telemetry/output/${OMNIA_PROJECT_NAME:-project_default}/telemetry_status.yml"
    ```

## Troubleshooting

- **Selective sink cleanup is blocked:** Disable or clean up every running
  source that depends on any requested sink, and then rerun the
  command. Because cleanup is all-or-nothing, no requested sink is removed
  while a dependency remains.
- **A sink PVC remains after cleanup:** This is the default behavior. Rerun the
  applicable cleanup with `Delete_sinks_volume=true` only when permanent data
  deletion is intended.
- **A source must be disabled temporarily:** Set its `metrics_enabled` or
  `logs_enabled` value to `false` in `telemetry_config.yml`, and rerun the
  `deploy` operation instead of cleanup.
- **Cleanup fails:** Review `/var/log/omnia/telemetry/` and the current
  `telemetry_status.yml` before retrying.
