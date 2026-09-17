# Deploy the Telemetry Stack

## Overview

Use this page to initialize and configure the shared Telemetry runtime input
files. Complete these steps before following the applicable source-specific
guide. Each source guide contains its own precheck, validation, deployment, and
verification instructions.

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

Continue with the applicable source-specific guide on the
[Telemetry landing page](index.md). Those guides provide the required
precheck, validation, deployment, and verification steps.

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
- For full or component-specific cleanup instructions, see
  [Clean up Telemetry](../../Operations/oim_cleanup.md#2-clean-up-telemetry).

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
