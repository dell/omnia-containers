# Configure InfiniBand

Set up InfiniBand (IB) high-speed interconnect on cluster nodes with
DOCA-OFED drivers and static IPoIB address assignment for low-latency MPI
communication. Three addressing modes are supported: **IPv4-only** (legacy
default), **dual-stack** (IPv4 + IPv6), and **IPv6-only**.


## Overview

InfiniBand provides the lowest latency and highest bandwidth interconnect
for HPC workloads. Omnia automates the following during node provisioning
via cloud-init:

- **DOCA-OFED driver** -- Installs NVIDIA's unified driver package
  (`doca-ofed` RPM) for ConnectX InfiniBand HCAs, including kernel module
  setup and firewall port configuration.
- **IB network configuration** -- Reads per-node IB address assignments
  from `pxe_mapping_file.csv` (`IB_NIC_NAME`, `IB_IPV4`, `IB_IPV6`),
  discovers the actual kernel interface name on each node, validates
  allocations, and assigns static IPoIB addresses using NetworkManager.
- **DOCA MPI environment** -- Configures the DOCA OpenMPI stack for
  application use.

!!! note
    Omnia does **not** deploy or manage OpenSM (the InfiniBand subnet
    manager). You must ensure an OpenSM instance is running on at least one
    node in the IB fabric before provisioning. See
    [Configure OpenSM](#configure-opensm-manual) for manual setup.


## Prerequisites

- Compute nodes have Mellanox ConnectX-6 (HDR) or ConnectX-7 (NDR)
  InfiniBand HCAs installed with IPoIB support. ConnectX-6 Dx
  (Ethernet-only / RoCE) is not supported for IPoIB.
- An InfiniBand switch connects all cluster nodes.
- Physical cabling (QSFP/QSFP56/OSFP) is in place between nodes and the IB
  switch.
- OpenSM is running on at least one node in the fabric (see
  [Configure OpenSM](#configure-opensm-manual)).
- The `doca` repository is present in the staged Repository Manager
  configuration for both x86_64 and aarch64 architectures.
- The OIM has been prepared (see [Prepare OIM](../main/setup_oim.md)).


## How it works

The IPoIB configuration pipeline runs in three phases during provisioning:

1. **Validate** -- The orchestrator reads `pxe_mapping_file.csv` and
   validates every IB row: address formats, CIDR prefix lengths, uniqueness,
   prohibited address classes, and approved-prefix containment. Validation
   fails atomically — a single invalid row blocks the entire pipeline.

2. **Render and publish** -- NetworkManager configuration scripts are
   generated and published to the Boot Service (BSS) via the Metadata
   Service (SMD). BSS publication is gated on SMD success — if SMD fails,
   BSS is skipped and the node enters `RECOVERY_REQUIRED` state.

3. **Verify** -- Post-configuration verification checks address assignment,
   IPv6 Duplicate Address Detection (DAD) completion, and reachability.

### Publication failure state

When SMD or BSS publication fails, the node is marked `RECOVERY_REQUIRED`
with `failure_stage`, `retryable`, and `recommended_action` details. The
pipeline is idempotent — rerunning provisioning for the affected nodes
completes the remaining publications without duplicating already-applied
configuration.


## Procedure

### Step 1: Configure the IB network in network_spec.yml

Edit `network_spec.yml` in the active project's Orchestrator input directory
and configure the `ib_network` section under `Networks`.

#### IPv4-only (legacy default)

No change required for existing deployments. When `ib_addr_mode` is absent
or set to `ipv4-only`, the IPv6 pipeline is skipped entirely.

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

#### Dual-stack (IPv4 + IPv6)

```yaml title="File: network_spec.yml"
Networks:
  - admin_network:
      # ... admin network fields ...

  - ib_network:
      ipv4_subnet: "192.168.0.0"
      ipv4_netmask_bits: "24"
      ipv6_subnet: "fd00:1b::"
      ipv6_netmask_bits: "64"
      ib_addr_mode: "dual-stack"
      slurm_preferred_addr_family: "ipv6"
      dns: []
```

#### IPv6-only

```yaml title="File: network_spec.yml"
  - ib_network:
      ipv6_subnet: "fd00:1b::"
      ipv6_netmask_bits: "64"
      ib_addr_mode: "ipv6-only"
      dns: []
```

#### `ib_network` parameter reference

| Parameter | Type | Required | Description |
|---|---|---|---|
| `ipv4_subnet` | string | Yes, when IB IPv4 configured | InfiniBand IPv4 network address (e.g., `192.168.0.0`) |
| `ipv4_netmask_bits` | string | Yes, when IB IPv4 configured | IPv4 CIDR prefix length 1–32 (e.g., `"24"`) |
| `ipv6_subnet` | string | Required for dual-stack or ipv6-only | InfiniBand IPv6 network address (e.g., `fd00:1b::`) |
| `ipv6_netmask_bits` | string | Required when `ipv6_subnet` is set | IPv6 CIDR prefix length 1–128 (e.g., `"64"`) |
| `ib_addr_mode` | string | Yes | `dual-stack`, `ipv6-only`, or `ipv4-only`. Default: `dual-stack` |
| `slurm_preferred_addr_family` | string | Required for `dual-stack` | `ipv4` or `ipv6`. Selects which address Slurm uses for NodeAddr. Ignored for `ipv4-only` and `ipv6-only`. Default: `ipv6`. |
| `dns` | list | No | DNS server addresses for the IB interface |

!!! note
    When `ib_addr_mode` is set to `dual-stack` (the default), `slurm_preferred_addr_family` is applicable and must be set to either `ipv4` or `ipv6`. When `ib_addr_mode` is set to `ipv4-only` or `ipv6-only`, `slurm_preferred_addr_family` is ignored.

!!! caution
    The IB subnet must not overlap an admin network range. Keep each
    `IB_IPV4` address inside the configured `ipv4_subnet`. Keep each
    `IB_IPV6` address inside the configured `ipv6_subnet`.

### Step 2: Add IB columns to the PXE mapping file

Edit `pxe_mapping_file.csv` in the same project input directory. The
canonical format uses 12 columns with `IB_NIC_NAME`, `IB_IPV4`, and
`IB_IPV6`.

#### Dual-stack example

```csv
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IPV4,IB_IPV6
slurm_node_rhel_10_0_aarch64,grp1,ABCD34,,node001,02:00:00:00:01:02,172.16.107.43,02:00:00:00:02:02,172.17.107.43,InfiniBand.Slot.7-1,192.168.0.101,fd00:1b::101
slurm_node_rhel_10_0_aarch64,grp1,ABCD35,,node002,02:00:00:00:01:03,172.16.107.44,02:00:00:00:02:03,172.17.107.44,InfiniBand.Slot.7-1,192.168.0.102,fd00:1b::102
```

#### IPv4-only example

Leave `IB_IPV6` empty. The column must still be present:

```csv
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IPV4,IB_IPV6
slurm_node_rhel_10_0_aarch64,grp1,ABCD34,,node001,02:00:00:00:01:02,172.16.107.43,02:00:00:00:02:02,172.17.107.43,InfiniBand.Slot.7-1,192.168.0.101,
```

#### IPv6-only example

Leave `IB_IPV4` empty:

```csv
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IPV4,IB_IPV6
slurm_node_rhel_10_0_aarch64,grp1,ABCD34,,node001,02:00:00:00:01:02,172.16.107.43,02:00:00:00:02:02,172.17.107.43,InfiniBand.Slot.7-1,,fd00:1b::101
```

#### Nodes without InfiniBand

Leave `IB_NIC_NAME`, `IB_IPV4`, and `IB_IPV6` all empty:

```csv
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IPV4,IB_IPV6
service_kube_node_rhel_10_0_x86_64,grp5,ABFL82,,k8s-node1,02:00:00:00:01:04,172.16.107.56,02:00:00:00:02:04,172.17.107.56,,,
```

#### Legacy 11-column format

```csv
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_node_rhel_10_0_aarch64,grp1,ABCD34,,node001,02:00:00:00:01:02,172.16.107.43,02:00:00:00:02:02,172.17.107.43,InfiniBand.Slot.7-1,192.168.0.101
```

**`IB_NIC_NAME`** identifies the InfiniBand HCA slot and port on the server.
Supported formats:

| Format | Example | Description |
|---|---|---|
| `InfiniBand.PCIe.Slot.X-Y` | `InfiniBand.PCIe.Slot.22-1` | PCIe slot X, port Y |
| `InfiniBand.Slot.X-Y` | `InfiniBand.Slot.7-1` | Slot X, port Y |
| `NIC.InfiniBand.X-Y` | `NIC.InfiniBand.1-3` | Slot X, port Y (alternate format) |
| `InfiniBand.Single-Y` | `InfiniBand.Single-1` | Single-port device |

!!! tip
    Slot numbers support decimal and hexadecimal values (e.g.,
    `InfiniBand.Slot.b5-1`). To find the correct `IB_NIC_NAME` for a
    server, check the iDRAC inventory under **Network Devices** or use OME
    discovery, which auto-populates the `IB_NIC_NAME` column.

!!! important
    - `IB_NIC_NAME` requires at least one address (`IB_IPV4` or `IB_IPV6`).
    - `IB_IPV4` values must be unique across all rows.
    - `IB_IPV6` values must be unique across all rows.
    - Leave all three IB columns empty for nodes that do not need IB.

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

1. **Discover the IB interface name** on each compute node. IB interfaces
   use predictable names based on PCI topology (e.g., `ibp161s0`,
   `ibp181s0`), not generic names like `ib0`:

    ```bash title="Run on: compute node"
    IB_IFACE=$(ls /sys/class/net/ | grep '^ib' | head -1)
    echo "IB interface: $IB_IFACE"
    ```

2. **Check IB port state**:

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

3. **Verify the IB interface has an IPv4 address** (dual-stack or IPv4-only):

    ```bash title="Run on: compute node"
    ip -4 addr show "$IB_IFACE"
    ```

    Expected: the interface shows the assigned `IB_IPV4` address and
    `state UP`.

4. **Verify the IB interface has an IPv6 address** (dual-stack or IPv6-only):

    ```bash title="Run on: compute node"
    ip -6 addr show "$IB_IFACE"
    ```

    Expected output for dual-stack:
    ```text
    inet6 fd00:1b::101/64 scope global
    ```

5. **Verify the IB device-to-interface mapping**:

    ```bash title="Run on: compute node"
    ibdev2netdev
    ```

6. **Test IPv4 IB connectivity** between two compute nodes:

    ```bash title="Run on: compute node"
    ping -c 5 <other_node_IB_IPV4>
    ```

7. **Test IPv6 IB connectivity** between two compute nodes (dual-stack or
   IPv6-only):

    ```bash title="Run on: compute node"
    ping6 -c 5 <other_node_IB_IPV6>
    ```

8. **Test RDMA bandwidth**:

    On the server node:

    ```bash title="Run on: compute node 1"
    ib_write_bw
    ```

    On the client node:

    ```bash title="Run on: compute node 2"
    ib_write_bw <server_IB_IPV4>
    ```

9. **Test RDMA latency**:

    On the server node:

    ```bash title="Run on: compute node 1"
    ib_write_lat
    ```

    On the client node:

    ```bash title="Run on: compute node 2"
    ib_write_lat <server_IB_IPV4>
    ```

    Expected InfiniBand latency: < 2 microseconds.


## Next steps

- [IPv6 Upgrade Guide](configure_infiniband_ipv6_upgrade.md) -- Migrate an
  existing IPv4-only cluster to dual-stack IPoIB.
- [Run HPC Benchmarks](run_hpc_benchmarks.md) -- Run MPI benchmarks over
  the IB fabric.


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

Only devices with `Link layer: InfiniBand` are used by Omnia. ConnectX-6 Dx
adapters are Ethernet-only and cannot be used for IPoIB.

### IPv6 address not configured (DEGRADED_IPV6)

After provisioning, the IB interface has an IPv4 address but no IPv6
address despite `IB_IPV6` being set in the PXE mapping file.

**Possible causes:**

- `ipv6_subnet` and `ipv6_netmask_bits` are not set in `network_spec.yml`
- `ib_addr_mode` is `ipv4-only` or unset (IPv6 pipeline is skipped)
- The cloud-init IB configuration script exited before reaching IPv6 setup

**Resolution:**

```bash title="Run on: compute node"
# Discover IB interface name
IB_IFACE=$(ls /sys/class/net/ | grep '^ib' | head -1)

# Check if IPv6 is configured
ip -6 addr show "$IB_IFACE"

# Check cloud-init logs for IB configuration errors
journalctl -u cloud-init --no-pager | grep -i "ipv6\|IB_IPV6\|DEGRADED"

# Verify network_spec.yml on the OIM
grep -A5 ib_network "$OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/network_spec.yml"
```

Correct the configuration and re-provision the affected nodes:

```bash title="Run on: OIM"
cd src/orchestrator/playbooks
ansible-playbook orchestrator.yml --tags provision
```

### IPv6 Duplicate Address Detection (DAD) failure

A node's IPv6 address shows `dadfailed` state, indicating another device on
the IB fabric has the same address.

```bash title="Run on: compute node"
IB_IFACE=$(ls /sys/class/net/ | grep '^ib' | head -1)
ip -6 addr show dev "$IB_IFACE" | grep dadfailed
```

**Resolution:**

1. Search the PXE mapping file for the conflicting `IB_IPV6` value.
2. If the CSV passed validation, the conflict is from a device outside Omnia
   management.
3. Clear the failed address and reassign:

    ```bash title="Run on: compute node"
    IB_IFACE=$(ls /sys/class/net/ | grep '^ib' | head -1)
    ip -6 addr del <address>/<prefix> dev "$IB_IFACE"
    ip -6 addr add <address>/<prefix> dev "$IB_IFACE"
    ```

### RECOVERY_REQUIRED publication state

SMD or BSS publication failed for one or more nodes. The pipeline is
idempotent — rerunning provisioning completes the remaining publications:

```bash title="Run on: OIM"
cd src/orchestrator/playbooks
ansible-playbook orchestrator.yml --tags provision
```

Check `orchestrator_status.yml` for the `failure_stage` and
`recommended_action` for each affected node:

```bash title="Run on: OIM"
cat "$OMNIA_DATA_PATH/orchestrator/output/$OMNIA_PROJECT_NAME/orchestrator_status.yml"
```

### Legacy IB_IP header not recognized

The 11-column format with `IB_IP` is accepted and normalized automatically.
If you see a header mismatch error, check for extra whitespace or hidden
characters in the CSV header:

```bash title="Run on: OIM"
head -1 "$OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/pxe_mapping_file.csv" | cat -A
```

### Poor RDMA performance

- Verify link rate (should be 100/200 Gbps for HDR/NDR):

    ```bash title="Run on: compute node"
    ibstat | grep Rate
    ```

- Check for errors on the IB port:

    ```bash title="Run on: compute node"
    perfquery
    ```
