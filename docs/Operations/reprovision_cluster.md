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
- The Orchestrator project mapping contains the correct target nodes and BMC
  addresses.
- Dell iDRAC credentials are available for physical-server PXE boot.
- Cluster workloads are stopped or drained before nodes are restarted.

Resolve the active component paths once in the maintenance shell:

```bash title="Run on: OIM"
source /etc/profile.d/omnia-env.sh
source "$OMNIA_DATA_PATH/activate-omnia.sh"
orchestrator_path="${ORCHESTRATOR_DATA_PATH:-${OMNIA_DATA_PATH}/orchestrator}"
discovery_path="${OMNIA_DATA_PATH}/discovery"
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
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
    ansible-playbook orchestrator.yml --tags pxeboot
    ```

By default, the workflow reads `$orchestrator_input/pxe_mapping_file.csv`.
When `pxe_mapping_file_path` is set in `orchestrator_config.yml`, it reads that
absolute path instead. It does not use the legacy Utils PXE playbook or a
separate Ansible inventory.

To re-provision only a reviewed subset of physical nodes, provide a CSV with
the same mapping columns:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags pxeboot \
      -e pxeboot_inventory=/path/to/reprovision_mapping.csv
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
    ansible-playbook orchestrator.yml --tags pxeboot \
      -e pxeboot_inventory=/path/to/reprovision_mapping.csv
    ```

## Re-provision with modifications

Use the following procedure when the mapping, catalog, image configuration, or
Orchestrator inputs have changed.

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
        source /opt/omnia/activate-omnia.sh
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
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/image_build_manager/playbooks
        ansible-playbook image_build_manager.yml --tags build
        ```

   Image Build Manager builds the architectures and functional groups selected
   by the current catalog through its domain entry point.

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
        source /opt/omnia/activate-omnia.sh
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
        source /opt/omnia/activate-omnia.sh
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
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags provision
        ```

7. PXE boot the reviewed nodes:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags pxeboot
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags pxeboot
        ```

For a combined Orchestrator operation, `--tags execute` runs provisioning and
then runs PXE boot when `enable_pxe_boot: true` is configured. The staged
commands above are recommended for maintenance because each phase can be
verified separately.

## NFS Share Cleanup

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

Review the Orchestrator outputs:

```bash title="Run on: OIM"
cat "$orchestrator_output/orchestrator_status.yml"
cat "$orchestrator_output/provisioning_report.yml"
cat "$orchestrator_output/failed_nodes.json"
```

When a custom PXE subset was supplied, also review `pxeboot_status.yml` in the
same output directory.

Verify the applicable cluster:

```bash title="Run on: Slurm control node"
sinfo
```

```bash title="Run on: Kubernetes control-plane node"
kubectl get nodes
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
