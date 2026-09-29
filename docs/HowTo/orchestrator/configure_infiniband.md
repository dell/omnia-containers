# Configure InfiniBand

Set up InfiniBand (IB) high-speed interconnect on cluster nodes with
DOCA-OFED drivers and static IPv4 IPoIB assignment for low-latency MPI
communication.

!!! warning "Current address-family support"
    The current Omnia implementation configures one static **IPv4** address on
    one InfiniBand interface per mapped node. IPv6-only, dual-stack IPoIB, and
    multiple IPoIB interfaces per node are not implemented in the current
    staging source. Do not enter IPv6 addresses in `network_spec.yml` or
    `pxe_mapping_file.csv`.

    The [IPv6 InfiniBand engineering draft](#ipv6-infiniband-engineering-draft)
    records the proposed contract for Engineering review. It is not a
    deployment procedure or a support statement.


## Overview

InfiniBand provides the lowest latency and highest bandwidth interconnect
for HPC workloads. Omnia automates the following during node provisioning
via cloud-init:

- **DOCA-OFED driver** -- Installs NVIDIA's unified driver package
  (`doca-ofed` RPM) for ConnectX InfiniBand HCAs, including kernel module
  setup and firewall port configuration.
- **IB network configuration** -- Detects the correct InfiniBand device
  using PCI slot mapping from the `IB_NIC_NAME` in `pxe_mapping_file.csv`,
  then assigns a static IPv4 IPoIB address using `IB_IP` in
  `pxe_mapping_file.csv` and NetworkManager.
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


## IPv6 InfiniBand engineering draft

!!! danger "Review draft — not implemented"
    This section describes the intended Part 1a behavior from BR-34869 v4 and
    ER-ORCH-005. The behavior is not available in the current Omnia staging
    source and is not part of the Omnia 2.3.0.0-rc1 support statement.

    Field names, file formats, supported hardware, and operational commands
    remain subject to Engineering and SME review. Continue to use the IPv4
    procedure earlier on this page until implementation and validation are
    complete.

This draft covers static IP-layer configuration on InfiniBand interfaces after
the node has booted through its administration network. It does not make the
PXE or DHCP boot path IPv6-capable.

### Intended scope

The proposed capability must:

- Configure IPv4-only, dual-stack, or IPv6-only IPoIB per covered interface.
- Apply centrally approved, static addresses to one or more IPoIB interfaces
  on each host through a single normalized processing path.
- Preserve the approved cluster, rack, node, fabric, rail, and logical-interface
  identity for every allocation.
- Support flat, on-link IPoIB communication without installing an IPoIB
  gateway, accepting Router Advertisements for route discovery, or changing
  the administration-network default route.
- Leave OpenSM responsible for InfiniBand link-layer fabric management.
- Reapply an unchanged approved allocation snapshot without creating duplicate
  profiles, addresses, inventory records, host entries, firewall rules, or
  telemetry identities.

The following work remains outside Part 1a:

- IPv6 PXE or DHCPv6 network boot, which belongs to the Part 2 provisioning
  scope.
- Routed IPoIB, IPoIB gateways, static IPoIB routes, and an IB-owned default
  route.
- SLAAC, modified EUI-64, HCA GUID, MAC-address, or privacy-address generation
  for routable production addresses.
- Address reassignment, rotation, retirement, and cross-system reconciliation
  beyond initial assignment and idempotent reapplication of the unchanged
  approved snapshot.
- Certification of HCA, firmware, driver, switch, operating-system,
  NetworkManager, and processor-architecture combinations that are not in an
  approved release matrix.

### Current implementation delta

| Area | Current staging behavior | Required Part 1a behavior |
| --- | --- | --- |
| Network specification | Accepts one IPv4 `ib_network.subnet` and a prefix from 1 through 32 | Accept and validate the approved IPv6 prefix and selected address-family mode without weakening the existing IPv4 path |
| Node mapping | Accepts one `IB_NIC_NAME` and one IPv4 `IB_IP` per host | Consume a normalized collection containing one or more interface allocations per host |
| Interface configuration | Recreates one NetworkManager profile and configures `ipv4.method manual` | Update the intended profile safely and configure each selected address family without flushing unrelated addresses or routes |
| Allocation lifecycle | Checks limited IPv4 uniqueness and NIC/address pairing | Validate authority, snapshot identity, lifecycle state, prefix membership, uniqueness, interface ownership, and all-or-none application |
| OpenCHAMI data | Registers administration addresses; no IPoIB allocation is published to SMD | Publish the accepted IPoIB state using the deployed SMD, Boot Service, and Metadata Service contracts selected by Engineering |
| Hostname data | Uses administration-address mappings | Generate the approved IPoIB hostname records from the complete active snapshot and remove stale managed records safely |
| Runtime verification | Does not perform IPv6 Duplicate Address Detection or a source-bound IPv6 peer test | Complete DAD, route, address, and peer checks before reporting success |
| Test coverage | Exercises the IPv4 network contract; no IPv6 IPoIB integration test exists | Cover every deployment mode, multiple interfaces, failure recovery, OpenSM non-regression, and performance targets |

### Proposed allocation contract

The central IP address management authority must provide one versioned,
complete allocation snapshot. Local configuration files, SMD, Boot Service,
Metadata Service, NetworkManager profiles, and managed host records are
consumers of that snapshot; they must not independently create production
addresses.

The final schema and transport remain an Engineering decision. At minimum,
each allocation record needs the following information:

| Information | Purpose |
| --- | --- |
| Source authority, schema version, snapshot identifier, and integrity metadata | Establish provenance, freshness, and the exact allocation set being applied |
| Cluster, rack, node, fabric, rail, and logical-interface identity | Bind an address to its intended topology and prevent cross-interface application |
| Physical-interface locator | Resolve the logical interface to the intended HCA and port without treating hardware identifiers as an address source |
| Deployment mode | Select IPv4-only, dual-stack, or IPv6-only behavior for the interface |
| Address and prefix | Apply the centrally approved static address and validate prefix membership |
| Lifecycle state | Prevent inactive, stale, retired, or conflicting records from being applied |

The existing `pxe_mapping_file.csv` cannot represent several IPoIB interfaces
or the required snapshot and lifecycle metadata. Engineering must therefore
select one of these approaches before the documentation can provide a final
file format:

1. Introduce a separate canonical interface-allocation artifact and make any
   legacy mapping conversion an explicit compatibility adapter.
2. Replace the current single-interface CSV contract with a versioned format
   and provide a documented migration path.

### Intended address-family behavior

| Mode | Intended result | Failure behavior |
| --- | --- | --- |
| IPv4-only | Preserve the supported static IPv4 IPoIB path without introducing an IPv6 dependency | Report an IPv4 configuration failure through the existing provisioning status path |
| Dual-stack | Apply the approved static IPv4 and IPv6 addresses to the same covered IPoIB interface | If IPv6 configuration fails, report visible degraded IPv4 operation; do not report full success |
| IPv6-only | Apply only the approved static IPv6 address and ensure the interface does not depend on a routable IPv4 address | Stop the affected IPoIB workflow and report an actionable failure; never add a silent IPv4 fallback |

For every mode, implementation must preserve unrelated NetworkManager
profiles, addresses, routes, DNS settings, and the administration-network
default route. The current fallback operation that flushes all addresses from
the device is not suitable for dual-stack operation.

### Proposed provisioning sequence

1. Authenticate and validate the complete allocation snapshot before changing
   any node or service state.
2. Reject missing, duplicate, stale, disallowed-address-class, wrong-prefix,
   wrong-interface, or conflicting records as one protected update.
3. Resolve every logical interface to its approved physical HCA and port.
4. Stage the node configuration and the corresponding OpenCHAMI and managed
   host records without exposing a partially accepted snapshot.
5. Apply the selected static address-family configuration through
   NetworkManager without deriving production addresses from hardware
   identifiers or Router Advertisements.
6. Wait for IPv6 Duplicate Address Detection to complete and fail on duplicate
   or tentative addresses that exceed the approved timeout.
7. Confirm that no IPoIB default route or unexpected IPoIB route was installed,
   then run an IPv6 peer check bound to the configured source interface.
8. Publish the accepted state and a persistent per-node, per-interface result.
9. On failure, retain or restore the last accepted snapshot and report the
   failed node, interface, stage, and recovery action.

The deployed source uses separate SMD, Boot Service, and Metadata Service
operations rather than a standalone BSS service. Engineering must define
transaction, convergence, retry, and compensating rollback behavior across
those services before the all-or-none publication requirement can be marked
implemented.

### Verification contract

Implementation is not ready for documentation sign-off until automated tests
and physical-lab evidence demonstrate all of the following:

| Verification area | Required evidence |
| --- | --- |
| Address modes | IPv4-only, dual-stack, and IPv6-only results match the selected mode on every covered interface |
| Multiple interfaces | One interface and multiple fabric or rail interfaces use the same processing path |
| Static allocation | No routable production address is generated by SLAAC, modified EUI-64, MAC address, HCA GUID, or privacy addressing |
| Idempotency | Reapplying an unchanged snapshot produces no duplicate profiles, addresses, records, firewall rules, or telemetry identities |
| Atomic failure | An invalid record does not leave partially updated protected artifacts or nodes |
| Routing boundary | IPoIB has no gateway, Router Advertisement route, static route, or default route, and the administration default route remains unchanged |
| IPv6 health | DAD completes and a source-bound on-link IPv6 peer check succeeds |
| OpenSM independence | OpenSM process state, configuration, partitions, LIDs, and GIDs do not change solely because IPoIB IPv6 is applied or reapplied |
| Performance | Provisioning-artifact generation and allocation validation meet the approved BR/ER targets at the specified scale |
| Platform matrix | The approved physical HCA, firmware, driver, switch, OS, NetworkManager, and architecture combinations pass release testing |

### Diagnostics and security review

The implementation should emit structured events that identify the snapshot,
node, logical interface, processing stage, result, and actionable error without
placing credentials or unnecessary complete production addresses in normal
logs. Diagnostics must distinguish validation, physical-interface resolution,
NetworkManager application, DAD, route validation, peer validation, service
publication, and rollback failures.

RBAC for allocation ingestion and configuration changes, allocation-export
authentication and integrity, NERSC security requirements, log-retention
policy, and authorized access to address-level diagnostics require explicit
Engineering and security approval before release.

### Decisions required before implementation sign-off

- Canonical allocation schema, transport, authentication, integrity, freshness,
  and full-snapshot semantics.
- Compatibility or migration policy for `pxe_mapping_file.csv`.
- Mapping between logical interface identity and physical HCA/port locators.
- Functional groups that receive the configuration and their consistent
  failure behavior.
- SMD representation for several IPoIB interfaces and the Boot Service and
  Metadata Service publication contract.
- DAD timeout, peer-selection rules, persistent status location, retry policy,
  and rollback boundaries.
- Approved IPv6 address classes and whether `/64` is mandatory for each IPoIB
  fabric.
- Physical support matrix and measurable release-performance thresholds.
- Availability, telemetry, documentation, support, EKT, RBAC, and compliance
  acceptance evidence.

!!! info "Living draft"
    Revalidate this section against the active BR, ER, staging source, schemas,
    runtime consumers, and tests whenever any of them changes. Promote the
    content into the supported procedure only after Engineering supplies
    implementation and validation evidence and the product owner approves the
    release classification.







