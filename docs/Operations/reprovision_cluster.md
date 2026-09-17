# Re-provision Cluster Nodes

Re-provisioning restarts existing diskless nodes so that they boot the current
network image published through OpenCHAMI. It does not install an operating
system on a local disk. When a mapping, catalog, image, or Orchestrator input
changes, regenerate the applicable provisioning artifacts before restarting
the nodes.

!!! warning

    Re-provisioning restarts the selected nodes. Stop or drain workloads, back
    up required data, and confirm the target mapping before continuing. The
    PXE workflow does not drain workloads, preserve control-plane quorum, or
    sequence nodes into availability-safe batches.

!!! caution

    Re-provisioning a Slurm control node or Kubernetes control-plane node can
    require the entire corresponding cluster to be re-provisioned.

## Prerequisites

- The OIM and the required OpenCHAMI services are healthy.
- The Omnia environment and required domains are initialized.
- The active Repository Manager `repo_status.yml` reports success and its
  referenced Pulp certificate exists. A PXE-only run still validates this
  contract.
- The nodes were provisioned previously, and Boot Service and Metadata Service
  contain their current boot and cloud-init configuration.
- Configured NFS, VAST Data, or PowerScale storage required by provisioning is
  accessible from the OIM and the applicable cluster nodes.
- The active Orchestrator project inputs pass validation.
- The canonical Orchestrator project mapping is complete and contains the
  correct host, admin-network, and BMC information for every managed node.
- Dell iDRAC credentials are available for physical-server PXE boot.
- The OIM can reach every selected iDRAC and admin IP, and the server firmware
  permits the configured PXE or UEFI HTTP boot target.
- `enable_pxe_boot: true` is set in `orchestrator_config.yml`. For an automatic
  restart, `set_pxe_boot_config.yml` must also use `restart_host: true`, a
  non-`disabled` boot override, and a network boot target.
- When `enable_node_registration: true`, the provisioned image includes
  `cloud-init`, `/proc/uptime` is available, and passwordless root SSH from the
  OIM to each selected admin IP works after boot.
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
active_mapping="$orchestrator_input/pxe_mapping_file.csv"
```

If `pxe_mapping_file_path` is set in `orchestrator_config.yml`, set
`active_mapping` to that absolute path before using the commands in this
procedure.

## Re-provision without modifications

If the mapping, catalog, built images, and Orchestrator inputs have not
changed, rerun only the Orchestrator PXE workflow:

```bash title="Run on: OIM"
cd <OMNIA_SOURCE_PATH>/src/main
./omnia.sh --run orchestrator --tags pxeboot
```

By default, this command restarts every physical node listed in the canonical
mapping. It does not use the legacy Utils PXE playbook or a separate Ansible
inventory. The source defaults use a forced restart and a continuous PXE
override; review `set_pxe_boot_config.yml` and use `once` when the override
must apply only to the next boot. A PXE-only run does not rebuild or validate
the current image-build output; it assumes the published Boot Service and
Metadata Service content is still usable. Use the modified workflow below if
an image or its inputs changed.

To restart only a reviewed subset, copy the full header and exact selected rows
from the canonical mapping into a separate CSV, and pass that file only to the
PXE workflow:

```bash title="Run on: OIM"
./omnia.sh --run orchestrator --tags pxeboot \
  -e pxeboot_inventory=/path/to/reprovision_mapping.csv
```

The subset must contain, at minimum, the named columns `BMC_IP`, `ADMIN_IP`,
`HOSTNAME`, and `SERVICE_TAG`, with unique, valid BMC and admin IP addresses.
Keep the canonical mapping complete and valid. Do not replace it with a subset
to select reboot targets: `provision` treats the canonical mapping as desired
state and can retire previously managed nodes that are omitted from it. A
custom `pxeboot_inventory` limits only the PXE and restart phase.

## Re-provision with modifications

Use the following procedure when the mapping, catalog, image configuration, or
Orchestrator inputs have changed.

1. Update the catalog and the appropriate domain project inputs. Keep the
   canonical mapping complete. Update it directly when using a maintained
   mapping. When OME supplies the mapping, rerun Discovery:

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run discovery --tags execute
    ```

    Review
    `$discovery_output/bmc_pxe_mapping_file.csv`, and copy the approved content
    to `$active_mapping`. Discovery intentionally does not overwrite the
    Orchestrator input. Compare the files before replacing the active mapping:

    ```bash title="Run on: OIM"
    diff -u "$active_mapping" \
      "$discovery_output/bmc_pxe_mapping_file.csv"
    ```

    After review, back up the current Orchestrator mapping and copy the approved
    Discovery CSV using the site's file-change procedure.

2. If the catalog or Repository Manager inputs changed, synchronize Repository
   Manager and regenerate its status. If Pulp was cleaned or is unavailable,
   restore it first:

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run repo_manager --tags prepare
    ```

    Then run the synchronization sequence:

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run repo_manager --tags precheck
    ./omnia.sh --run repo_manager --tags download
    ./omnia.sh --run repo_manager --tags status
    ```

    To force existing RPM repositories to check upstream, add
    `-e "resync_repos=all"` to the `download` command, or supply a
    comma-separated list of exact repository names.

3. If the catalog, packages, functional groups, or image settings changed,
   rebuild the configured images. If MinIO or the registry was cleaned or is
   unavailable, run Image Build Manager `prepare` first:

    ```bash title="Run on: OIM"
    ./omnia.sh --run image_build_manager --tags prepare
    ./omnia.sh --run image_build_manager --tags build
    ```

    Omit `prepare` when the existing Image Build Manager infrastructure remains
    healthy. Image Build Manager builds the architectures and functional groups
    selected through its configured catalog or `package_groups.yml`. Ensure
    Repository Manager, Image Build Manager, and Orchestrator resolve the same
    reviewed catalog. Set `force_rebuild: true` in `image_build_config.yml` when
    an intentional rebuild must bypass the package-hash cache.

4. Validate the revised Orchestrator inputs and run the Orchestrator
   prechecks:

    ```bash title="Run on: OIM"
    ./omnia.sh --run orchestrator --tags validate
    ./omnia.sh --run orchestrator --tags precheck
    ```

5. If OpenCHAMI or OpenLDAP was cleaned, or its deployment inputs changed,
   run `prepare`. This phase collects required credentials, deploys the enabled
   services, and validates their readiness:

    ```bash title="Run on: OIM"
    ./omnia.sh --run orchestrator --tags prepare
    ```

    Skip this step only when the already-deployed services remain healthy and
    their deployment configuration is unchanged.

6. Regenerate provisioning, boot-service, metadata-service, and inventory
   content:

    ```bash title="Run on: OIM"
    ./omnia.sh --run orchestrator --tags provision
    ```

7. PXE boot every node in the canonical mapping:

    ```bash title="Run on: OIM"
    ./omnia.sh --run orchestrator --tags pxeboot
    ```

    To restart only reviewed nodes, use a separate subset copied from the
    canonical mapping:

    ```bash title="Run on: OIM"
    ./omnia.sh --run orchestrator --tags pxeboot \
      -e pxeboot_inventory=/path/to/reprovision_mapping.csv
    ```

    Use availability-safe subsets for control-plane nodes. Omnia does not drain
    workloads or sequence control-plane restarts.

For a combined Orchestrator operation, `--tags execute` runs provisioning and
then runs PXE boot when `enable_pxe_boot: true` is configured. The staged
commands above are recommended for maintenance because each phase can be
verified separately.

## Shared Storage Cleanup

Do not clear shared storage for an ordinary or partial re-provisioning. When an
intentional fresh Slurm or Kubernetes cluster will reuse an existing NFS or
VAST path, clear only the directories owned by that cluster. PowerScale data
must be handled through the applicable storage-administration procedure.

Orchestrator component cleanup is a separate, destructive, whole-component
reset; it is not required for a normal or per-node re-provisioning. Preview
and review that workflow before using it. See
[Clean Up Orchestrator](../HowTo/orchestrator/cleanup_orchestrator.md).

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
   Set `mount_on_oim: true` for storage selected by the cluster so that
   Orchestrator can populate the required configuration and artifacts.
2. Reference the required storage name from the applicable cluster definition
   in [omnia_config.yml](../Reference/Configuration/omnia_config.md).
3. Run the Orchestrator `validate`, `precheck`, `provision`, and `pxeboot`
   workflows. Run `prepare` first if OpenCHAMI or OpenLDAP must be restored.

## Verification

Review the Orchestrator outputs:

```bash title="Run on: OIM"
cat "$orchestrator_output/pxeboot_status.yml"
cat "$orchestrator_output/failed_nodes.json"
cat "$orchestrator_output/orchestrator_status.yml"
```

Review `provisioning_report.yml` only when `provision` ran for the same
inventory. Confirm the report timestamps and `inventory_source`; an earlier
report can remain on disk, and a custom PXE subset does not match the canonical
provisioning inventory. In `failed_nodes.json`, distinguish an iDRAC/PXE
failure from a `node_registration` failure. When node registration is
disabled, a successful PXE phase means that restart was initiated but the
operating-system boot and cloud-init completion were not verified.

Verify the applicable cluster:

```bash title="Run on: Slurm control node"
sinfo
```

```bash title="Run on: Kubernetes control-plane node"
export KUBECONFIG=/etc/kubernetes/admin.conf
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
