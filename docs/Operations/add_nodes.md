# Add Nodes

## Overview

Orchestrator treats the current `pxe_mapping_file.csv` as the desired node
inventory. To add nodes, append valid rows, rerun provisioning, and PXE boot
only the new physical servers by passing a custom inventory CSV to the
source-supported `pxeboot_inventory` extra variable.

The provisioning pass handles every mapped category: Kubernetes, Slurm and
login, OS-only, and custom functional groups. It re-registers category nodes in
SMD, refreshes functional-group boot and metadata configuration, prepares the
configured bolt-ons, and regenerates reports and inventories.

## Prerequisites

- Complete the [Provision Nodes](../HowTo/orchestrator/provision_nodes.md)
  procedure for the existing cluster.
- Discover the new hardware and collect all required mapping values. For
  physical nodes, ensure that every `BMC_IP` is reachable and that the BMC
  credentials stored by Orchestrator work for every new server.
- Ensure that `HOSTNAME`, `ADMIN_MAC`, and `ADMIN_IP` are unique across the
  complete primary mapping. Non-empty `SERVICE_TAG` and `IB_IP` values must
  also be unique.
- Ensure that Image Build Manager's `build_status.yml` reports
  `overall_status: success` and contains matching kernel, initrd, and root
  filesystem artifacts for every new functional group. The artifacts must be
  accessible from the OIM.
- If a new functional group was added to the catalog, rerun Repository Manager and
  Image Build Manager before running Orchestrator.
- Confirm that every new `ADMIN_IP` belongs to the primary admin subnet or one
  of the additional admin subnets configured in `network_spec.yml`.
- Preserve the order of all existing rows in `pxe_mapping_file.csv`. Append new
  rows at the end. Reordering existing rows can change the generated XNAME
  assignments.

## Procedure

1. Resolve the active project paths:

    ```bash title="Run on: OIM"
    source /etc/profile.d/omnia-env.sh
    source "${OMNIA_DATA_PATH}/activate-omnia.sh"

    orchestrator_path="${OMNIA_DATA_PATH}/orchestrator"
    discovery_path="${OMNIA_DATA_PATH}/discovery"

    orchestrator_input="${orchestrator_path}/input/${OMNIA_PROJECT_NAME}"
    orchestrator_output="${orchestrator_path}/output/${OMNIA_PROJECT_NAME}"
    discovery_output="${discovery_path}/output/${OMNIA_PROJECT_NAME}"
    ```

2. Append the new rows to the primary mapping configured by
   `pxe_mapping_file_path` in `orchestrator_config.yml`.

   When `pxe_mapping_file_path` is empty, use:

    ```text
    $orchestrator_input/pxe_mapping_file.csv
    ```

   Preserve the exact case-sensitive header, all existing rows, and their
   current order. Add new rows at the end of the file.

    ```text title="Required primary mapping header"
    FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
    ```

    !!! warning

        Do not reorder or remove existing rows while adding nodes. Orchestrator
        generates XNAME assignments from row positions, so changing the order
        can change the identities assigned to existing nodes.

3. If Discovery produced the new hardware mapping, review
   `$discovery_output/bmc_pxe_mapping_file.csv` and merge the approved new rows
   into the Orchestrator mapping. Discovery does not update the Orchestrator
   input automatically; do not replace retained rows without reviewing the
   difference.

4. Create a separate CSV containing only the new physical nodes that must be
   PXE booted.

   The custom PXE inventory requires the following exact, case-sensitive
   column names. Column order is not significant.

    ```text title="File: new_nodes.csv"
    BMC_IP,ADMIN_IP,HOSTNAME,SERVICE_TAG
    172.17.107.51,172.16.107.51,nid001,ABC1234
    172.17.107.52,172.16.107.52,nid002,DEF5678
    ```

   `BMC_IP` and `ADMIN_IP` must contain valid, non-empty IPv4 addresses and
   must be unique within this CSV. `HOSTNAME` and `SERVICE_TAG` should match
   the corresponding rows in the primary mapping.

   A CSV containing the complete 11-column primary mapping header is also
   accepted when the new rows are copied directly from
   `pxe_mapping_file.csv`.

    !!! warning

        Orchestrator does not compare `pxeboot_inventory` with the primary
        mapping. Every row in the custom CSV is targeted for PXE boot and
        restart. Confirm that the file contains only new nodes that were
        included in the preceding provisioning run.

5. Run the Orchestrator precheck and provisioning phases:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"

        # Optional input-only validation for faster feedback
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags validate

        # Includes input validation and checks images and deployed prerequisites
        ./omnia.sh --run orchestrator --tags precheck

        # Refresh provisioning data, reports, and generated inventories
        ./omnia.sh --run orchestrator --tags provision
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks

        # Optional input-only validation for faster feedback
        ansible-playbook orchestrator.yml --tags validate

        # Includes input validation and checks images and deployed prerequisites
        ansible-playbook orchestrator.yml --tags precheck

        # Refresh provisioning data, reports, and generated inventories
        ansible-playbook orchestrator.yml --tags provision
        ```

   The separate `validate` command is optional because `precheck` also performs
   input schema and logic validation.

6. PXE boot only the new physical nodes by supplying the custom inventory:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags pxeboot \
          -e pxeboot_inventory=/absolute/path/to/new_nodes.csv
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags pxeboot \
          -e pxeboot_inventory=/absolute/path/to/new_nodes.csv
        ```

   Orchestrator reads the custom CSV, builds the BMC target group, configures
   the selected boot source through Redfish, and restarts only the listed
   nodes.

   When `enable_node_registration: true`, Orchestrator verifies each node by:

   - Connecting to its `ADMIN_IP` using passwordless root SSH.
   - Confirming that the node booted after the current PXE request.
   - Waiting for `cloud-init` to complete successfully.

   This verification performs more than an admin-IP reachability check.

   For virtual machines or environments without iDRAC, set
   `enable_pxe_boot: false`. Orchestrator skips the complete iDRAC PXE and
   restart flow. Configure network boot and restart only the new virtual
   machines manually after provisioning.

## Verification

Check the full provisioning result and the new-node PXE result separately:

```bash title="Run on: OIM"
cat "${orchestrator_output}/provisioning_report.yml"
cat "${orchestrator_output}/pxeboot_status.yml"
cat "${orchestrator_output}/failed_nodes.json"
```

When a custom PXE inventory is used, `pxeboot_status.yml` reports only the
nodes from that CSV and records the custom inventory path.

A successful `failed_nodes.json` contains:

```json
{
  "failure_count": 0,
  "failed_nodes": []
}
```

The JSON file itself is not empty.

For a Slurm compute-node addition, verify the node from a Slurm controller:

```bash title="Run on: Slurm controller"
scontrol show node <new-compute-hostname>
sinfo
```

Confirm that the node appears in the intended partition and does not remain in
an unexpected `UNKNOWN` or `DOWN` state.

For a Kubernetes node addition, verify the node from the first Kubernetes
control-plane node:

```bash title="Run on: first Kubernetes control-plane node"
kubectl get nodes -o wide
kubectl get pods --all-namespaces -o wide
```

Confirm that the new Kubernetes node reaches the `Ready` state. A successful
PXE report confirms operating-system boot and cloud-init completion, but does
not by itself confirm Kubernetes cluster membership.

## Next steps

- Retain the updated primary `pxe_mapping_file.csv` as the desired inventory
  for future Orchestrator runs.
- Use [Remove Slurm Compute Nodes](remove_slurm_nodes.md) when decommissioning
  Slurm compute nodes.
- Adjust `node_registration_pause_minutes`, `node_registration_retries`, and
  `node_registration_delay` in `set_pxe_boot_config.yml` if the hardware
  consistently requires a longer boot window.
- `boot_source_override_enabled` defaults to `continuous`. With this setting,
  the selected nodes continue choosing PXE during later restarts. Retain
  `continuous` for stateless nodes, or configure the following for a single PXE
  boot:

    ```yaml
    boot_source_override_enabled: once
    ```

- If Telemetry was previously deployed, ensure that
  `telemetry_config.yml.cluster_inventory` references the regenerated
  `orchestrator_inventory.yml`.

  When iDRAC telemetry is enabled, also refresh the file referenced by
  `idrac_telemetry_configurations.bmc_group_data_path` with the regenerated
  `bmc_group_data.csv`.

  Reconcile the enabled Telemetry components after updating these inputs:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run telemetry --tags deploy
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
        ansible-playbook telemetry.yml --tags deploy
        ```

## Troubleshooting

**Provisioning reports a missing image**

The functional-group name must have a matching entry in Image Build Manager's
successful `build_status.yml`. Build the missing image and rerun `precheck` and
`provision`.

**The PXE phase would include existing nodes**

Do not run `--tags pxeboot` against the complete mapping for this operation.
Pass a same-format CSV containing only the new rows with
`-e pxeboot_inventory=/absolute/path/to/new_nodes.csv`.

### A new node fails PXE boot or node registration

Review `failure_stage` and `verification_state` in `pxeboot_status.yml` or
`failed_nodes.json`.

- For `failure_stage: pxe_boot`, check BMC connectivity, BMC credentials,
  Redfish support, the configured boot override, and whether the restart
  request succeeded.
- For `failure_stage: node_registration`, check passwordless root SSH from the
  OIM to the node's `ADMIN_IP`.
- `verification_state: unreachable` means passwordless root SSH did not
  succeed.
- `verification_state: stale_boot` means the node is reachable, but its current
  boot started before the PXE request. Confirm that the server actually
  restarted.
- `verification_state: cloud_init_pending` means cloud-init did not complete
  before the configured retry limit.
- `verification_state: cloud_init_error` means cloud-init completed with an
  error or unsupported state. Check the following on the node:

    ```bash title="Run on: Added node"
    cloud-init status --long
    journalctl -u cloud-init -u cloud-final --no-pager
    ```

If the server requires more time to boot, increase the node-registration timing
values in `set_pxe_boot_config.yml` and retry the PXE phase with the custom
inventory.
