# Clean Up Telemetry

## Overview

Telemetry supports full cleanup, selective sink cleanup, and independent
source cleanup. Choose the narrowest operation that matches the intended
scope. Source cleanup permanently deletes source-owned persistent volumes;
sink persistent volumes are preserved by default.

## Prerequisites

- Run cleanup while the service Kubernetes cluster is available.
- Ensure that the OIM can reach the Kubernetes control-plane VIP over SSH as
  `root`.
- Back up Telemetry data, credentials, and logs that must be retained.
- Run `omnia.sh` commands from `<OMNIA_SOURCE_PATH>/src/main`.

## Procedure

### Run full cleanup

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

!!! warning

    When `Delete_sinks_volume=true`, Telemetry always deletes credentials,
    inputs, outputs and logs, regardless of the `cleanup_credentials` or
    `cleanup_logs` values.

### Clean up sinks

The `cleanup_sinks` operation removes selected sink infrastructure. Before
cleanup, Telemetry checks whether running sources depend on each requested
sink. A requested sink is not removed while a running source depends on it.

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

### Clean up sources

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

## Verification

1. Inspect the remaining Telemetry resources:

    ```bash title="Run on: Kubernetes control-plane VIP"
    kubectl get pods,services,configmaps,persistentvolumeclaims -n telemetry
    ```

2. Confirm that:

    - Selective sink cleanup changed only the requested sinks. Review the
      command output for any sink blocked by a running source dependency.
    - Source cleanup removed only the requested source and its source-owned
      volumes.
    - Full cleanup removed all source and sink workloads.
    - Sink PVCs remain unless `Delete_sinks_volume=true` was specified.

3. Review the cleanup result:

    ```bash title="Run on: OIM"
    cat "${OMNIA_DATA_PATH:-/opt/omnia}/telemetry/output/${OMNIA_PROJECT_NAME:-project_default}/telemetry_status.yml"
    ```

## Troubleshooting

- **Selective sink cleanup is blocked:** Disable or clean up the running source
  identified for the affected sink, and then rerun the command.
- **A sink PVC remains after cleanup:** This is the default behavior. Rerun the
  applicable cleanup with `Delete_sinks_volume=true` only when permanent data
  deletion is intended.
- **A source must be disabled temporarily:** Set its `metrics_enabled` or
  `logs_enabled` value to `false` in `telemetry_config.yml`, and rerun the
  `deploy` operation instead of cleanup.
- **Cleanup fails:** Review `/var/log/omnia/telemetry/` and the current
  `telemetry_status.yml` before retrying.
