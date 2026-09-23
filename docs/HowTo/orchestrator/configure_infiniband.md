# Configure InfiniBand

Set up InfiniBand (IB) high-speed interconnect on cluster nodes with
DOCA-OFED drivers and static IPoIB IP assignment for low-latency MPI
communication.


## Overview

InfiniBand provides the lowest latency and highest bandwidth interconnect
for HPC workloads. Omnia automates the following during node provisioning
via cloud-init:

- **DOCA-OFED driver** -- Installs NVIDIA's unified driver package
  (`doca-ofed` RPM) for ConnectX InfiniBand HCAs, including kernel module
  setup and firewall port configuration.
- **IB network configuration** -- Detects the correct InfiniBand device
  using PCI slot mapping from the `IB_NIC_NAME` in `pxe_mapping_file.csv`,
  then assigns a static IPoIB IP address using `IB_IP` in `pxe_mapping_file.csv` and NetworkManager.
- **DOCA MPI environment** -- Configures the DOCA OpenMPI stack for
  application use.

!!! note
    Omnia does **not** deploy or manage OpenSM (the InfiniBand subnet
    manager). You must ensure an OpenSM instance is running on at least one
    node in the IB fabric before provisioning. See
    [Configure OpenSM](#configure-opensm-manual) for manual setup.


## Prerequisites

- Compute nodes have NVIDIA ConnectX InfiniBand HCAs installed.
- An InfiniBand switch connects all cluster nodes.
- Physical cabling (QSFP/QSFP56/OSFP) is in place between nodes and the IB
  switch.
- OpenSM is running on at least one node in the fabric (see
  [Configure OpenSM](#configure-opensm-manual)).
- The `doca` repository is present in the staged Repository Manager configuration for
  both x86_64 and aarch64 architectures.
- The OIM has been prepared
  (see [Prepare OIM](../main/setup_oim.md)).


## Procedure

### Step 1: Configure the IB network in network_spec.yml

Edit `network_spec.yml` in the active project's Orchestrator input directory
and configure the `ib_network` section under `Networks`:

```yaml title="File: network_spec.yml"
Networks:
- admin_network:
    oim_nic_name: "eno1"
    subnet: "172.16.107.0"
    netmask_bits: "24"
    primary_oim_admin_ip: "172.16.107.254"
    primary_oim_bmc_ip: ""
    router: "172.16.107.254"
    dynamic_range: "172.16.107.201-172.16.107.250"
    dns: []
    ntp_servers: []
    additional_subnets: []

- ib_network:
    subnet: "192.168.0.0"
    netmask_bits: "24"
    dns: []
```

| Parameter      | Description                                                  |
|----------------|--------------------------------------------------------------|
| `subnet`       | Network address for the IB subnet (e.g., `192.168.0.0`)     |
| `netmask_bits` | CIDR prefix length for the IB network. It can differ from the primary admin-network prefix length. |
| `dns`          | List of DNS server IPs to configure on the IB interface      |

!!! caution
    The IB subnet must not overlap an admin network range. Orchestrator applies
    the IB-specific `netmask_bits` value to node InfiniBand interfaces, so the
    IB and admin networks may use different prefix lengths. Keep each `IB_IP`
    inside the configured IB subnet.

### Step 2: Add IB columns to the PXE mapping file

Edit `pxe_mapping_file.csv` in the same project input directory and add the
`IB_NIC_NAME` and `IB_IP` columns for each node that requires InfiniBand.

```csv title="File: pxe_mapping_file.csv"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_control_node_rhel_10_0_x86_64,grp0,ABCD12,,ctrl-node1,02:00:00:00:01:01,172.16.107.52,02:00:00:00:02:01,172.17.107.52,InfiniBand.Slot.7-1,192.168.0.100
slurm_node_rhel_10_0_aarch64,grp1,ABCD34,,compute-node1,02:00:00:00:01:02,172.16.107.43,02:00:00:00:02:02,172.17.107.43,InfiniBand.Slot.7-2,192.168.0.101
slurm_node_rhel_10_0_aarch64,grp2,ABFG34,,compute-node2,02:00:00:00:01:03,172.16.107.44,02:00:00:00:02:03,172.17.107.44,NIC.InfiniBand.1-3,192.168.0.102
service_kube_node_rhel_10_0_x86_64,grp5,ABFL82,,k8s-node1,02:00:00:00:01:04,172.16.107.56,02:00:00:00:02:04,172.17.107.56,,
```

**`IB_NIC_NAME`** identifies the InfiniBand HCA slot and port on the server.
Supported formats:

| Format                         | Example                        | Description                          |
|--------------------------------|--------------------------------|--------------------------------------|
| `InfiniBand.PCIe.Slot.X-Y`    | `InfiniBand.PCIe.Slot.22-1`   | PCIe slot X, port Y                  |
| `InfiniBand.Slot.X-Y`         | `InfiniBand.Slot.7-1`         | Slot X, port Y                       |
| `NIC.InfiniBand.X-Y`          | `NIC.InfiniBand.1-3`          | Slot X, port Y (alternate format)    |
| `InfiniBand.Single-Y`         | `InfiniBand.Single-1`         | Single-device system, port Y         |

!!! tip
    Slot numbers support decimal and hexadecimal values. To find the correct
    `IB_NIC_NAME` for a server, check the iDRAC inventory under **Network
    Devices** or use OME discovery, which auto-populates the `IB_NIC_NAME`
    column.

!!! important
    - `IB_NIC_NAME` and `IB_IP` must **both** be provided or **both** be
      empty for each row.
    - Each `IB_IP` must be unique across all nodes.
    - Leave both columns empty for nodes that do not need IB (e.g.,
      Kubernetes-only nodes).

### Step 3: Deploy the cluster

After completing the configuration steps above, proceed with the standard
deployment workflow:

1. [Configure and synchronize repositories](../repo_manager/configure_repos.md).
2. [Build the functional-group images](../image_build_manager/build_images.md).
3. [Provision the nodes](provision_nodes.md).

During node boot, cloud-init automatically executes the DOCA-OFED
installation and IB network configuration.

!!! note
    The `doca-ofed` package is provided through the selected Omnia catalog;
    no separate software-selection entry is required.

### Configure OpenSM (Manual)

Omnia does not deploy OpenSM. You must configure it manually on at least
one node in the IB fabric **before** provisioning.

1. Install OpenSM on the designated subnet manager node:

    ```bash title="Run on: subnet manager node"
    dnf install -y opensm
    ```

2. Enable and start the service:

    ```bash title="Run on: subnet manager node"
    systemctl enable --now opensm
    ```

3. Verify OpenSM is running:

    ```bash title="Run on: subnet manager node"
    systemctl status opensm
    ```

!!! note
    Only one node in the IB fabric should run OpenSM as the primary subnet
    manager. A second node can run OpenSM as a standby for high availability.


## Verification

1. **Check IB port state** on each compute node:

    ```bash title="Run on: compute node"
    ibstat
    ```

    ```text title="Expected output"
    CA 'mlx5_0'
       Port 1:
          State: Active
          Physical state: LinkUp
          Rate: 200 (HDR)
    ```

2. **Verify the IB interface has an IP address**:

    ```bash title="Run on: compute node"
    ip addr show | grep ib
    ```

    Expected: the interface shows the assigned `IB_IP` address and
    `state UP`.

3. **Verify the IB device-to-interface mapping**:

    ```bash title="Run on: compute node"
    ibdev2netdev
    ```

    ```text title="Expected output"
    mlx5_0 port 1 ==> ib0 (Up)
    ```

4. **Test IB connectivity** between two compute nodes:

    ```bash title="Run on: compute node"
    ping -c 5 <other_node_IB_IP>
    ```

5. **Test RDMA bandwidth**:

    On the server node:

    ```bash title="Run on: compute node 1"
    ib_write_bw
    ```

    On the client node:

    ```bash title="Run on: compute node 2"
    ib_write_bw <server_IB_IP>
    ```

6. **Test RDMA latency**:

    On the server node:

    ```bash title="Run on: compute node 1"
    ib_write_lat
    ```

    On the client node:

    ```bash title="Run on: compute node 2"
    ib_write_lat <server_IB_IP>
    ```

    Expected InfiniBand latency: < 2 microseconds.

## Next steps

- [Run HPC Benchmarks](run_hpc_benchmarks.md) -- Run MPI
  benchmarks over the IB fabric.

## Troubleshooting

### IB interface does not appear

Verify InfiniBand modules are loaded:

```bash title="Run on: compute node"
lsmod | grep mlx5
lsmod | grep ib_ipoib
```

Load missing modules manually:

```bash title="Run on: compute node"
modprobe mlx5_ib
modprobe ib_ipoib
modprobe ib_umad
modprobe ib_uverbs
```

### ibstat shows "Down" or "Initializing"

- Check physical cable connections between the node and the IB switch.
- Verify OpenSM is running somewhere in the fabric:
  `systemctl status opensm`
- Check firmware and device info:

    ```bash title="Run on: compute node"
    ibv_devinfo
    ```

### IB_NIC_NAME cannot be resolved to a device

If the cloud-init log shows `ERROR: Could not resolve PCI address for slot`,
verify the `IB_NIC_NAME` value matches a physical slot on the server:

```bash title="Run on: compute node"
dmidecode -t slot | grep -E "Designation|Bus Address"
```

Compare the slot number in your `pxe_mapping_file.csv` with the output.

### No InfiniBand-capable devices found

If the log shows `All found mlx5 devices are Ethernet-only`, the NVIDIA
NICs on the node are configured for Ethernet (RoCE) mode, not InfiniBand.
Verify the HCA firmware mode:

```bash title="Run on: compute node"
ibstat
```

Only devices with `Link layer: InfiniBand` are used by Omnia.

### Poor RDMA performance

- Verify link rate (should be 100/200 Gbps for HDR):

    ```bash title="Run on: compute node"
    ibstat | grep Rate
    ```

- Check for errors on the IB port:

    ```bash title="Run on: compute node"
    perfquery
    ```








