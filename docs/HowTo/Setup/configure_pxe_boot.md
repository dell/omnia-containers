
# Configure PXE Boot

Set the PXE boot order on provisioned nodes so they automatically retrieve and boot into the diskless image provided by the OIM. The `set_pxe_boot.yml` playbook configures boot source override via iDRAC Redfish API.

!!! warning

    This playbook restarts target servers and powers them on if they are off. Any unsaved data will be lost.

## Prerequisites

- Dell iDRAC BMCs must be reachable from the OIM.
- PXE boot order is set/enabled in the BIOS/UEFI settings of the target nodes.
- PXE support is enabled in the NIC firmware.
- iDRAC firmware supports the Boot Source Override API (iDRAC9 and later).
- The OIM server providing the PXE boot image is reachable by the target nodes.

## Inventory setup

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
ssh omnia_core
cd /omnia/utils
ansible-playbook set_pxe_boot.yml -i inventory
```

**Mode 2: Without inventory file** — Configure PXE boot for all nodes in the PXE mapping file:

```bash title="Run on: omnia_core container"
ssh omnia_core
cd /omnia/utils
ansible-playbook set_pxe_boot.yml
```

!!! info

    - [PXE Boot Nodes](pxe_boot_nodes.md) -- Initial PXE boot and provisioning procedure.
    - [PXE Mapping File](../../Reference/SampleFiles/pxe_mapping_file.md) -- Mapping file format and functional group reference.
    - [Discover Nodes](discover_nodes.md) -- Node discovery procedure.
