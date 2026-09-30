# Deploy Telemetry Sinks

## Overview

Use the `deploy_sinks` operation to deploy Kafka, VictoriaMetrics, or
VictoriaLogs without deploying Telemetry sources. Only the specified sinks are
deployed; other sinks remain unchanged. If no sinks are specified, all three
sinks are deployed by default.

For each selected sink, Telemetry creates the required Helm releases,
persistent volume claims, and Kubernetes services. Sink persistent volumes are
preserved by default during cleanup. See
[Clean Up Telemetry](cleanup_telemetry.md) for instructions to delete sink
volumes when they are no longer required.

## Prerequisites

- Complete the requirements on the [Telemetry landing page](index.md).
- Initialize and configure the Telemetry runtime files as described in
  [Deploy the Telemetry Stack](deploy_telemetry.md).
- Ensure that the OIM can reach the Kubernetes control-plane VIP over SSH as
  `root` and that `kubectl` on the VIP can access the cluster.
- Ensure that the required sink charts and images are available for the
  configured online or offline installation mode.
- Run `omnia.sh` commands from `<OMNIA_SOURCE_PATH>/src/main`.

## Procedure

Run the applicable command.

Deploy Kafka only:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run telemetry --tags deploy_sinks -e sinks=kafka
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
    ansible-playbook telemetry.yml --tags deploy_sinks -e sinks=kafka
    ```

Deploy Kafka and VictoriaMetrics:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run telemetry --tags deploy_sinks -e sinks=kafka,victoria_metrics
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
    ansible-playbook telemetry.yml --tags deploy_sinks -e sinks=kafka,victoria_metrics
    ```

Deploy Kafka, VictoriaMetrics, and VictoriaLogs:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run telemetry --tags deploy_sinks
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
    ansible-playbook telemetry.yml --tags deploy_sinks
    ```

Valid sink names are `kafka`, `victoria_metrics`, and `victoria_logs`.
Specify multiple sinks as a comma-separated list without spaces.

## Verification

1. On the Kubernetes control-plane VIP, verify the selected sink resources:

    ```bash title="Run on: Kubernetes control-plane VIP"
    kubectl get pods,services,persistentvolumeclaims -n telemetry
    ```

2. Verify the Helm releases:

    ```bash title="Run on: Kubernetes control-plane VIP"
    helm list -n telemetry
    ```

3. Confirm that resources for each requested sink are running and ready.
   Sinks that were not requested must remain unchanged.

## Next steps

- Configure and deploy the required Telemetry sources from the
  [Telemetry landing page](index.md).
- Export connection details when an external producer or consumer must connect
  to [Kafka](configure_external_kafka.md) or
  [VictoriaMetrics and VictoriaLogs](configure_external_victoria.md).
- To remove sink infrastructure, run the `cleanup_sinks` operation. For
  example:

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

  See [Clean Up Telemetry](cleanup_telemetry.md#clean-up-sinks) for dependency
  checks and instructions to delete sink persistent volumes.

## Troubleshooting

- **A sink name is rejected:** Use `kafka`, `victoria_metrics`, or
  `victoria_logs`. Separate multiple values with commas and do not include
  spaces.
- **A Helm release cannot be created:** Confirm that the required chart and
  image are available for the configured installation mode.
