# Re-provision Cluster Nodes

Re-provisioning replaces the diskless image on existing cluster nodes. Nodes
load the operating system from images provided through OpenCHAMI and boot from
the provisioning network. PXE boot is owned by the Orchestrator domain.

!!! warning

    Re-provisioning restarts the selected nodes. Stop workloads, back up
    required data, and confirm the target mapping before continuing.

!!! caution

    Re-provisioning a Slurm control node or Kubernetes control-plane node can
    require the entire corresponding cluster to be re-provisioned.

## Prerequisites

- The OIM and the required OpenCHAMI services are healthy.
- The Omnia environment and required domains are initialized.
- NFS or PowerScale shared storage is accessible from the OIM and the cluster
  nodes.
- The canonical Orchestrator project mapping contains the complete desired
  cluster inventory and the correct node and BMC addresses.
- `enable_pxe_boot: true` is set in `orchestrator_config.yml` for physical
  servers that use iDRAC-based PXE boot.
- Every target `BMC_IP` is reachable, and the BMC credentials stored by
  Orchestrator work for every target server.
- When `enable_node_registration: true`, passwordless root SSH from the OIM to
  every target `ADMIN_IP` is configured.
- The published kernel, initrd, and root filesystem artifacts for every target
  functional group are available. When repository or image outputs are reused,
  confirm that `repo_status.yml` and `build_status.yml` report
  `overall_status: success`.
- OpenCHAMI Boot Service, Metadata Service, SMD, DHCP, and the provisioning
  network are operational.
- Cluster workloads are stopped or drained before nodes are restarted.

Resolve the active component paths once in the maintenance shell:

```bash title="Run on: OIM"
source /etc/profile.d/omnia-env.sh
source "$OMNIA_DATA_PATH/activate-omnia.sh"
orchestrator_path="${ORCHESTRATOR_DATA_PATH:-${OMNIA_DATA_PATH}/orchestrator}"
discovery_path="${DISCOVERY_DATA_PATH:-${OMNIA_DATA_PATH}/discovery}"
orchestrator_input="$orchestrator_path/input/$OMNIA_PROJECT_NAME"
orchestrator_output="$orchestrator_path/output/$OMNIA_PROJECT_NAME"
discovery_output="$discovery_path/output/$OMNIA_PROJECT_NAME"
```

## Re-provision without modifications

If the mapping, catalog, built images, and Orchestrator inputs have not
changed, rerun only the Orchestrator PXE workflow:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags pxeboot
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source "${OMNIA_DATA_PATH}/activate-omnia.sh"
    cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
    ansible-playbook orchestrator.yml --tags pxeboot
    ```

By default, the workflow reads `$orchestrator_input/pxe_mapping_file.csv`.
When `pxe_mapping_file_path` is set in `orchestrator_config.yml`, it reads that
absolute path instead. It does not use the legacy Utils PXE playbook or a
separate Ansible inventory.

!!! warning

    Without `pxeboot_inventory`, the PXE phase targets every node in the active
    primary mapping. By default, `restart_host` and `force_restart` are both
    `true`, so every selected physical server is restarted.

To re-provision only a reviewed subset of physical nodes, create a separate
CSV with the following exact, case-sensitive columns. Column order is not
significant.

```text title="File: reprovision_mapping.csv"
BMC_IP,ADMIN_IP,HOSTNAME,SERVICE_TAG
172.17.107.51,172.16.107.51,nid001,ABC1234
```

`BMC_IP` and `ADMIN_IP` must contain valid, nonempty IPv4 addresses and must be
unique within the file. A complete CSV containing the 11-column primary
mapping header is also accepted.

!!! warning

    Do not replace the canonical `pxe_mapping_file.csv` with a temporary
    subset. Provisioning treats the canonical mapping as the complete desired
    state. Omitting existing nodes can change generated inventories, Slurm
    configuration, XNAME assignments, and other provisioning output.

    Orchestrator does not compare `pxeboot_inventory` with the canonical
    mapping. Every row in the custom CSV is targeted for PXE boot and restart.
    Include only the nodes that must be re-provisioned.

Supply the reviewed subset only to the PXE phase:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags pxeboot \
      -e pxeboot_inventory=/path/to/reprovision_mapping.csv
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source "${OMNIA_DATA_PATH}/activate-omnia.sh"
    cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
    ansible-playbook orchestrator.yml --tags pxeboot \
      -e pxeboot_inventory=/path/to/reprovision_mapping.csv
    ```

## Re-provision with modifications

Use the following procedure when the mapping, catalog, image configuration, or
Orchestrator inputs have changed.

Use the phases that correspond to the changed inputs:

| Change | Required phases |
| --- | --- |
| No mapping, catalog, image, or Orchestrator input changed | Orchestrator `pxeboot` only. |
| Mapping or Orchestrator input changed | Orchestrator `validate`, `precheck`, `provision`, and `pxeboot`. |
| Catalog, package, or repository changed | Repo Manager `precheck`, `download`, and `status`; Image Build Manager `build`; then the Orchestrator phases. |
| Image configuration or functional group changed | Image Build Manager `build`; then Orchestrator `precheck`, `provision`, and `pxeboot`. |
| OpenCHAMI or OpenLDAP was cleaned or reconfigured | Orchestrator `prepare` before `provision`. |
| Only selected nodes must restart | Pass a temporary `pxeboot_inventory` to the PXE phase. |

1. Update the catalog and the appropriate domain project inputs. Update
   `pxe_mapping_file.csv` directly when using a maintained mapping. When OME
   supplies the mapping, rerun Discovery, review
   `$discovery_output/bmc_pxe_mapping_file.csv`, and copy the approved content
   to `$orchestrator_input/pxe_mapping_file.csv` (or to the explicit
   `pxe_mapping_file_path`). Discovery intentionally does not overwrite the
   Orchestrator input. Compare the files before replacing the active mapping:

    ```bash title="Run on: OIM"
    diff -u "$orchestrator_input/pxe_mapping_file.csv" \
      "$discovery_output/bmc_pxe_mapping_file.csv"
    ```

   After review, back up the current Orchestrator mapping and copy the approved
   Discovery CSV using the site's file-change procedure.

2. If catalog packages or repositories changed, synchronize Repository
   Manager and regenerate its status:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run repo_manager --tags precheck
        ./omnia.sh --run repo_manager --tags download
        ./omnia.sh --run repo_manager --tags status
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source "${OMNIA_DATA_PATH}/activate-omnia.sh"
        cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
        ansible-playbook repo_manager.yml --tags precheck
        ansible-playbook repo_manager.yml --tags download
        ansible-playbook repo_manager.yml --tags status
        ```

3. If the catalog, packages, functional groups, or image settings changed,
   rebuild the configured images:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run image_build_manager --tags build
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source "${OMNIA_DATA_PATH}/activate-omnia.sh"
        cd <OMNIA_SOURCE_PATH>/src/image_build_manager/playbooks
        ansible-playbook image_build_manager.yml --tags build
        ```

   Image Build Manager builds the architectures and functional groups selected
   by the current catalog through its domain entry point.

   If Pulp, MinIO, or the image registry was removed or is unhealthy, run the
   applicable Repo Manager or Image Build Manager `prepare` phase before
   downloading packages or building images.

4. Validate the revised Orchestrator inputs and run the Orchestrator
   prechecks:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags validate
        ./omnia.sh --run orchestrator --tags precheck
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source "${OMNIA_DATA_PATH}/activate-omnia.sh"
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags validate
        ansible-playbook orchestrator.yml --tags precheck
        ```

5. If OpenCHAMI or OpenLDAP was cleaned, or its deployment inputs changed,
   run `prepare`. This phase collects required credentials, deploys the enabled
   services, and validates their readiness:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags prepare
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source "${OMNIA_DATA_PATH}/activate-omnia.sh"
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags prepare
        ```

   Skip this step only when the already-deployed services remain healthy and
   their deployment configuration is unchanged.

6. Regenerate provisioning, boot-service, metadata-service, and inventory
   content:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags provision
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source "${OMNIA_DATA_PATH}/activate-omnia.sh"
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags provision
        ```

7. PXE boot the nodes. The following command uses the complete active mapping:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags pxeboot
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source "${OMNIA_DATA_PATH}/activate-omnia.sh"
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags pxeboot
        ```

   To restart only a reviewed subset, add the temporary inventory to either
   command:

    ```bash title="Run on: OIM"
    ./omnia.sh --run orchestrator --tags pxeboot \
      -e pxeboot_inventory=/absolute/path/to/reprovision_mapping.csv
    ```

For a combined Orchestrator operation, `--tags execute` runs provisioning and
then runs PXE boot when `enable_pxe_boot: true` is configured. The staged
commands above are recommended for maintenance because each phase can be
verified separately.

## PXE boot and verification settings

Review `$orchestrator_input/set_pxe_boot_config.yml` before restarting the
nodes. The relevant defaults are:

```yaml
enable_node_registration: true
restart_host: true
force_restart: true
boot_source_override_enabled: continuous
boot_source_override_target: pxe
```

- `restart_host: false` configures the boot source without restarting the
  server.
- `force_restart: true` performs an immediate restart. Set it to `false` when
  the operating system must be given an opportunity to shut down gracefully.
- `boot_source_override_enabled: continuous` continues selecting PXE on later
  restarts. Use `once` when only the current provisioning boot must use PXE.
- When `enable_node_registration: true`, Orchestrator connects to every target
  `ADMIN_IP` by passwordless root SSH, confirms that the boot occurred after
  the current PXE request, and waits for cloud-init to complete successfully.
- When node-registration verification is disabled,
  `pxe_initiated_unverified` confirms only that the Redfish boot and restart
  request was initiated. It does not confirm operating-system boot or
  cloud-init completion.

## NFS Share Cleanup

Shared-storage cleanup is not part of normal node re-provisioning. Preserve
the existing shared data unless an intentional fresh-cluster reset has been
reviewed and approved.

When a fresh Slurm or Kubernetes cluster will reuse an existing shared-storage
path, clear only the directories owned by that cluster before re-provisioning.
OIM cleanup does not automatically make an arbitrary NFS share safe to reuse.

!!! danger

    Removing shared-storage content is irreversible. Verify the mounted
    filesystem, configured path, cluster ownership, and backup before deleting
    any content. Do not run a recursive deletion command against an unresolved
    variable or an unverified mount point.

### Reuse the same share paths

1. Stop the workloads and power off the affected cluster nodes when required.
2. Identify the exact share paths from the Orchestrator project
   `storage_config.yml`.
3. Back up required data and clear the cluster-owned content using the
   approved storage-administration procedure.
4. Run the Orchestrator `provision` and `pxeboot` workflows.

### Use new share paths

1. Configure new `mounts` entries in
   [storage_config.yml](../Reference/Configuration/storage_config.md).
2. Reference the required storage name from the applicable cluster definition
   in [omnia_config.yml](../Reference/Configuration/omnia_config.md).
3. Run the Orchestrator `validate`, `precheck`, `provision`, and `pxeboot`
   workflows. Run `prepare` first if OpenCHAMI or OpenLDAP must be restored.

## Verification

Review the current PXE run outputs:

```bash title="Run on: OIM"
cat "$orchestrator_output/pxeboot_status.yml"
cat "$orchestrator_output/failed_nodes.json"
cat "$orchestrator_output/orchestrator_status.yml"
```

Expected results:

- `pxeboot_status.yml` reports `overall_status: success`, the expected
  `inventory_source` and `custom_inventory` value, and a successful result for
  every selected node.
- `failed_nodes.json` reports `failure_count: 0` and contains an empty
  `failed_nodes` array. The file itself is not empty on a successful run.
- `orchestrator_status.yml` reports `last_completed_phase: pxeboot` and a
  successful PXE phase.
- The timestamps and run identifiers belong to the current execution.

If `provision` was run during the current operation, also review:

```bash title="Run on: OIM"
cat "$orchestrator_output/provisioning_report.yml"
```

Do not use an older `provisioning_report.yml` as proof that the current PXE
operation succeeded. Provisioning details are correlated with PXE results only
when the report inventory source matches the active PXE inventory.

When node-registration verification is enabled, a successful PXE result also
confirms passwordless root SSH, a fresh operating-system boot, and successful
cloud-init completion. When it is disabled, independently verify the boot and
cloud-init state on every selected node.

Verify the applicable cluster:

```bash title="Run on: Slurm control node"
scontrol show nodes
sinfo
squeue
srun -N 1 hostname
```

```bash title="Run on: Kubernetes control-plane node"
kubectl get nodes -o wide
kubectl get pods --all-namespaces -o wide
```

!!! info

    - [Add Nodes](add_nodes.md) or
      [Remove Slurm Compute Nodes](remove_slurm_nodes.md) -- Change the
      supported node inventory without re-imaging retained nodes.
    - [Build Cluster Images](../HowTo/image_build_manager/build_images.md) --
      Build the images selected by the catalog.
    - [Configure Storage](../HowTo/orchestrator/configure_storage.md) -- Manage
      storage configuration for cluster nodes.
    - [Configure PXE Boot](../HowTo/orchestrator/configure_pxe_boot.md) --
      Configure and run the Orchestrator PXE workflow.
