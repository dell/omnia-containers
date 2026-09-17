# Deploy the Telemetry Stack

## Overview

The Telemetry entry point validates the three runtime input files, deploys the
required sinks, deploys each enabled source, reconciles the generated
Kustomize manifests, checks pod state, and writes `telemetry_status.yml`.
Running without tags performs validation followed by deployment. Cleanup,
precheck, upgrade, rollback, and connection-export workflows run only when
their tags are selected explicitly.

## Prerequisites

- Meet the platform requirements on the [Telemetry landing page](index.md).
- Export `OMNIA_DATA_PATH` and `OMNIA_PROJECT_NAME`, or accept `/opt/omnia` and
  `project_default`.
- Provide an Orchestrator YAML inventory whose `kube_vip_group` contains the
  service Kubernetes VIP. The inventory must also contain service control-plane
  and worker groups; LDMS additionally uses its Slurm groups.
- Ensure that the OIM can reach the VIP over SSH as `root` and that `kubectl`
  on the VIP can access the cluster.
- Make the shared `k8s_cluster_mount` available on the Kubernetes nodes. LDMS
  also requires the configured `slurm_cluster_mount` on the Slurm nodes.
- Run customer-facing `omnia.sh` commands from `src/main`. The script is not
  located at the root of the source checkout.

## Procedure

1. From the Omnia source root, change to `src/main` and initialize the shared
   virtual environment and Telemetry runtime files:

    ```bash title="Run on: OIM"
    cd src/main
    ./omnia.sh --setup-venv
    ```

    Telemetry templates are staged under
    `<OMNIA_DATA_PATH>/telemetry/input/<project>/`. Running
    `src/telemetry/domain-init.sh --force` overwrites existing project inputs;
    use it only when that is intended.

2. Edit all three project input files without removing their keys:

    - `telemetry_config.yml`: inventory, sources, bridges, sinks, and
      source-specific settings.
    - `telemetry_storage_config.yml`: replica counts and CPU, memory, and PVC
      settings.
    - `telemetry_packages.yml`: online/offline mode, repository URL, shared
      Kubernetes and Slurm mounts, registry, images, charts, repositories, and
      Python modules.

3. Run the opt-in environment precheck:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run telemetry --tags precheck
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/telemetry
        ansible-playbook playbooks/telemetry.yml --tags precheck
        ```

    It validates the VIP and SSH access, control-plane and worker readiness,
    non-Telemetry pod health, and the source-specific PowerScale and LDMS
    prerequisites when those sources are enabled. This operation is opt-in and
    is not included in the untagged default flow.

4. Validate only the input contract when desired:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run telemetry --tags validate
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/telemetry
        ansible-playbook playbooks/telemetry.yml --tags validate
        ```

    Validation includes L1 JSON Schema checks and L2 cross-field checks. L2
    also checks SSH access to the Kubernetes VIP and verifies the configured
    Kubernetes mount remotely, so this is not an offline-only operation. Use
    an absolute `cluster_inventory` path, normally
    `<ORCHESTRATOR_DATA_PATH>/output/<OMNIA_PROJECT_NAME>/orchestrator_inventory.yaml`.
    When `ORCHESTRATOR_DATA_PATH` is unset, resolve it as
    `<OMNIA_DATA_PATH>/orchestrator`. Replace the placeholders with absolute
    values because environment variables are not expanded inside YAML.

5. Deploy the enabled configuration:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run telemetry --tags deploy
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/telemetry
        ansible-playbook playbooks/telemetry.yml --tags deploy
        ```

    The credential role creates an encrypted `telemetry_credentials.yml` and
    prompts only for empty credentials required by the enabled sources.


    Deployment loads the configuration and credentials, deploys sink
    infrastructure, deploys enabled sources and Vector bridges, generates the
    root Kustomization, applies the complete stack, checks component state, and
    writes `telemetry_status.yml`.

    The current source has these operational limitations:

    - The deployment configuration loader reads `project_default`, even when a
      different `OMNIA_PROJECT_NAME` was validated.
    - `TELEMETRY_DATA_PATH` is not consistently applied by initialization and
      deployment.
    - The root deployment invokes the sink playbook with its default selection,
      which deploys Kafka, VictoriaMetrics, and VictoriaLogs.
    - PowerScale, UFM, and VAST are imported by the root deployment only when
      their metrics channel is enabled. A logs-only configuration is not
      supported by this path.

## Verification

1. Read the generated status file:

    ```bash title="Run on: OIM"
    cat /opt/omnia/telemetry/output/project_default/telemetry_status.yml
    ```

    Adjust the path when `OMNIA_DATA_PATH` or `OMNIA_PROJECT_NAME` differs.
    Confirm `overall_status: success` and check that each requested sink,
    source, and bridge is `deployed`. Disabled components are `skipped`.

2. On the Kubernetes VIP, inspect the namespace:

    ```bash title="Run on: Kubernetes VIP"
    kubectl get pods -n telemetry
    ```

    Deployment fails when a pod reaches `CrashLoopBackOff`, `Error`,
    `ImagePullBackOff`, `ErrImagePull`, `InvalidImageName`, or
    `CreateContainerConfigError`.

After completing steps 1 and 2, use the verification section in each enabled
Telemetry source guide:

- [Verify iDRAC Telemetry](configure_idrac.md#verification)
- [Verify LDMS Telemetry](configure_ldms.md#verification)
- [Verify PowerScale Telemetry](configure_powerscale.md#verification)
- [Verify UFM Telemetry](configure_ufm.md#verification)
- [Verify VAST Telemetry](configure_vast.md#verification)
- [Verify OME Telemetry](telemetry_from_ome.md#verification)
- [Verify the Vector-LDMS bridge](configure_ldms.md#view-ldms-metrics-in-the-victoriametrics-ui-vmui)

## Next steps

- Export [Kafka](configure_external_kafka.md) or
  [Victoria](configure_external_victoria.md) connection details when external
  systems must publish or query Telemetry data.
- To remove all Telemetry runtime resources while preserving sink PVCs and
  Kafka identity metadata, choose one execution method:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run telemetry --tags cleanup
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/telemetry
        ansible-playbook playbooks/telemetry.yml --tags cleanup
        ```

  Pass `-e delete_sinks_volume=true` only when the Kafka, VictoriaMetrics, and
  VictoriaLogs sink volumes must also be deleted. Source-specific tags such as
  `cleanup_idrac`, `cleanup_ldms`, and `cleanup_powerscale` remove their
  respective sources and source-owned volumes. Although sink-specific cleanup
  tags are discoverable in the current playbook, sink cleanup is gated by the
  full `cleanup` operation.

  The `cleanup_idrac` workflow deletes the MySQL PVC
  `mysqldb-pvc-idrac-telemetry-0` and permanently removes the iDRAC service
  inventory stored in `idrac_telemetrydb`.

## Troubleshooting

- **Input validation fails:** Correct every file listed in the validation
  output. Validation applies JSON Schema checks and cross-field logic to all
  three input files.
- **`kube_vip` is missing:** Set `cluster_inventory` to a valid inventory with
  `all.children.kube_vip_group.hosts`.
- **The VIP is unreachable:** Restore root SSH connectivity from the OIM to the
  inventory VIP.
- **A pod is in an error state:** Run
  `kubectl logs -n telemetry <pod-name>` on the VIP and correct the reported
  image, configuration, or secret issue.
- **An LDMS node was skipped:** Review `deploy_unreachable_nodes.ldms` in the
  status file. Unreachable LDMS nodes are recorded without failing an otherwise
  successful deployment; failures returned by reachable nodes remain fatal.
