
# Configure PXE Boot

## Overview

The `set_pxe_boot.yml` playbook uses the iDRAC Redfish API to set the boot source override on target nodes, ensuring they boot from PXE on the next restart to retrieve the diskless image from the OIM.

!!! caution

    <b>This playbook restarts the target servers and powers on servers that are currently off.<br>Running workloads may be interrupted, and any unsaved data could be lost.<br>Ensure all critical workloads are gracefully stopped and any important data is saved before executing this playbook.</b>

## Prerequisites

- The [Provision Nodes](../orchestrator/provision_nodes.md) procedure is complete.
- Dell iDRAC BMCs must be reachable from the OIM.
- PXE boot order is set/enabled in the BIOS/UEFI settings of the target nodes.
- PXE support is enabled in the NIC firmware.
- iDRAC firmware supports the Boot Source Override API (iDRAC9 and later).
- The OIM server providing the PXE boot image is reachable by the target nodes.

### Inventory setup

Create an inventory file with a `bmc` group containing the BMC IP addresses of the target nodes:

```ini title="Example: inventory"
[bmc]
172.17.107.43
172.17.107.44
172.17.107.45
```

!!! note

    The inventory must contain a `bmc` group with at least one BMC IP address.

## Procedure

**Mode 1: With inventory file** — Configure PXE boot for specific nodes:

```bash title="Run on: omnia_core container"
cd /omnia/utils
ansible-playbook set_pxe_boot.yml -i inventory
```

**Mode 2: Without inventory file** — Configure PXE boot for all nodes in the PXE mapping file:

```bash title="Run on: omnia_core container"
cd /omnia/utils
ansible-playbook set_pxe_boot.yml
```

## Verification

1. Verify the playbook completed without failures in the Ansible run summary (`failed=0`).

## Next Steps

- [Provision Nodes](../orchestrator/provision_nodes.md) -- Provision the cluster nodes after PXE boot configuration.
- [Verify Cluster](../../Operations/verify_cluster.md) -- Verify the cluster is operational after booting.

## Troubleshooting

- **Setting PXE boot order manually in BIOS**: If the Redfish API call fails or the node does not honor the boot source override, set the PXE boot order manually:

    1. Restart the node and enter BIOS/UEFI setup (typically `F2` during POST on Dell servers).
    2. Navigate to **Boot Settings** > **Boot Sequence**.
    3. Move the NIC/PXE entry to the top of the boot order.
    4. Save changes and exit (`F10` or equivalent) to restart the node.

- **Checking iDRAC license**: The Boot Source Override API requires an iDRAC Enterprise or Datacenter license.

    If the license does not support Redfish Boot Source Override, upgrade the iDRAC license or configure PXE boot order manually in BIOS.

- **Checking iDRAC connectivity**: If the OIM cannot reach the BMC, verify network connectivity before re-running the playbook:

    ```bash title="Run on: OIM host"
    ping -c 4 <idrac_ip>
    curl -k -I https://<idrac_ip>/redfish/v1
    ```

    If the ping or curl request fails, verify the iDRAC IP address, the BMC network cabling/VLAN, and that the iDRAC network interface is enabled.

!!! info

    - [PXE Mapping File](../../Reference/SampleFiles/pxe_mapping_file.md) -- Mapping file format and functional group reference.
    - [Discover Nodes](../discovery/discover_nodes.md) -- Node discovery procedure.



















