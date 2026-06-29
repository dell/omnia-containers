
# Create a Mapping File


Create the `pxe_mapping_file.csv` that tells Omnia how to discover and
provision each bare-metal server. This file maps service tags, MAC addresses,
IP addresses, and functional group assignments for every target node.

## Overview


The PXE mapping file is a CSV file that Omnia's discovery playbook uses to:

- Identify each server by its Dell service tag.
- Assign admin and BMC network addresses.
- Place nodes into functional groups (e.g., `slurm_control_node`,
  `slurm_node`, `kube_control_plane`, `kube_node`, `login_node`).
- Map blade servers to their parent chassis (for PowerEdge MX and C-series).

The file must be created **before** running the discovery playbook.


## Prerequisites


- The [Deploy Omnia Core](deploy_omnia_core.md) procedure is complete and `omnia_core` is
  running.
- You have the service tag, admin MAC address, and BMC MAC address for every
  target server. These are available from:

  - iDRAC web UI (System > Overview)
  - Physical label on the server front panel
  - OpenManage Enterprise (OME) inventory

- Admin and BMC IP ranges are planned and do not conflict with existing
  allocations.


## Procedure


1. **Enter the omnia_core container**:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```


   Or alternatively:

   ```bash title="Run on: OIM host"
   podman exec -it -u root omnia_core bash
   ```


2. **Navigate to the input directory**:

   ```bash title="Run on: omnia_core container"
   cd /opt/omnia/input/project_default
   ```


3. **Create the mapping file** using a text editor:

   ```bash title="Run on: omnia_core container"
   vi pxe_mapping_file.csv
   ```


4. **Add the CSV header and node entries**. The file must contain the following
   columns in this exact order:

   ```text title="File: /opt/omnia/input/project_default/pxe_mapping_file.csv"
   FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP
   slurm_control_node,slurm_cluster,ABCDEF1,,,aa:bb:cc:dd:ee:01,10.5.0.101,aa:bb:cc:dd:ff:01,10.3.0.101
   slurm_node,slurm_cluster,ABCDEF2,,,aa:bb:cc:dd:ee:02,10.5.0.102,aa:bb:cc:dd:ff:02,10.3.0.102
   slurm_node,slurm_cluster,ABCDEF3,,,aa:bb:cc:dd:ee:03,10.5.0.103,aa:bb:cc:dd:ff:03,10.3.0.103
   login_node,slurm_cluster,ABCDEF4,,,aa:bb:cc:dd:ee:04,10.5.0.104,aa:bb:cc:dd:ff:04,10.3.0.104
   kube_control_plane,k8s_cluster,ABCDEF5,,,aa:bb:cc:dd:ee:05,10.5.0.105,aa:bb:cc:dd:ff:05,10.3.0.105
   kube_node,k8s_cluster,ABCDEF6,,,aa:bb:cc:dd:ee:06,10.5.0.106,aa:bb:cc:dd:ff:06,10.3.0.106
   ```


### Column Reference


| Column | Required | Description |
| --- | --- | --- |
| `FUNCTIONAL_GROUP_NAME` | Yes | Node role. Valid values: `slurm_control_node`, `slurm_node`, `login_node`, `kube_control_plane`, `kube_node`, `auth_server` |
| `GROUP_NAME` | Yes | Logical cluster grouping (e.g., `slurm_cluster`, `k8s_cluster`) |
| `SERVICE_TAG` | Yes | Dell service tag of the server (7-character alphanumeric string) |
| `PARENT_SERVICE_TAG` | Yes | Service tag of the parent chassis for blade servers. Leave empty for rack servers. |
| `HOSTNAME` | Yes | Custom hostname. Leave empty to let Omnia auto-generate from the service tag. |
| `ADMIN_MAC` | Yes | MAC address of the PXE-capable NIC on the admin network |
| `ADMIN_IP` | Yes | Static IP address to assign on the admin network |
| `BMC_MAC` | Yes | MAC address of the BMC/iDRAC network interface |
| `BMC_IP` | Yes | Static IP address to assign on the BMC network |

!!! warning

    - Column headers are **case-sensitive**. Use uppercase exactly as shown.
    - All fields are **mandatory**. Use an empty value (two consecutive commas)
      for fields that should be auto-generated (`PARENT_SERVICE_TAG`,
      `HOSTNAME`).
    - `ADMIN_MAC` must be the MAC address of the NIC used for PXE boot.
    - `BMC_MAC` must be the MAC address of the BMC/iDRAC interface.
    - Do **not** add spaces after commas.

5. **Save and exit** the editor (`:wq` in vi).


## Verification


1. **Validate the CSV format** by checking the header row:

   ```bash title="Run on: omnia_core container"
   head -1 /opt/omnia/input/project_default/pxe_mapping_file.csv
   ```


   Expected output:

   ```text title="Expected output on: omnia_core container"
   FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP
   ```


2. **Count the entries** (excluding the header):

   ```bash title="Run on: omnia_core container"
   tail -n +2 /opt/omnia/input/project_default/pxe_mapping_file.csv | wc -l
   ```


   The count should match the number of target servers you intend to provision.

3. **Check for formatting issues** (trailing spaces, empty lines):

   ```bash title="Run on: omnia_core container"
   cat -A /opt/omnia/input/project_default/pxe_mapping_file.csv
   ```


   Ensure there are no trailing spaces (`$` should immediately follow the
   last field value) and no blank lines.


## Next Steps


- [Configure Inputs](configure_inputs.md) -- Configure software and cluster input files.
- [Configure Credentials](configure_credentials.md) -- Set up encrypted provisioning credentials.
- [Discover Nodes](discover_nodes.md) -- Run the discovery playbook using this mapping file.


## Troubleshooting


**Discovery playbook fails with "invalid mapping file" error**
   - Verify column headers are uppercase and match exactly.
   - Ensure no trailing spaces or hidden characters (use `cat -A` to check).
   - Confirm every row has exactly 9 comma-separated fields.

**MAC address not found during discovery**
   - Verify the `ADMIN_MAC` matches the PXE NIC (not an onboard NIC that is
     disabled in BIOS).
   - Check that the BMC MAC corresponds to the iDRAC dedicated NIC, not a
     shared LOM.

**IP address conflict**
   - Ensure no duplicate IPs exist in the `ADMIN_IP` or `BMC_IP` columns.
   - Verify the IP ranges do not overlap with the OIM's own addresses or any
     DHCP scope on the network.

**Blade server not discovered**
   - Populate the `PARENT_SERVICE_TAG` column with the chassis service tag
     for all blade servers in PowerEdge MX or C-series chassis.
