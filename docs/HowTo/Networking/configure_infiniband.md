
# Configure InfiniBand


Set up InfiniBand (IB) high-speed interconnect on compute nodes with
DOCA-OFED drivers, OpenSM subnet manager, and static IB IP assignment for
low-latency MPI communication.

## Overview


InfiniBand provides the lowest latency and highest bandwidth interconnect
for HPC workloads. Omnia automates the deployment of:

- **DOCA-OFED driver** -- NVIDIA's unified driver package for ConnectX
  InfiniBand HCAs.
- **OpenSM** -- Subnet manager that initializes the IB fabric and manages
  routing.
- **Static IB IPs** -- Assign persistent IPoIB (IP-over-InfiniBand) addresses
  for application-level communication.


## Prerequisites


- Compute nodes have NVIDIA ConnectX InfiniBand HCAs installed.
- An InfiniBand switch connects all compute nodes.
- Physical cabling (QSFP/QSFP56/OSFP) is in place between nodes and the IB
  switch.
- `software_config.json` includes the IB/OFED software package.
- Local repositories are synced with OFED packages (see
  [Create Local Repos](../Setup/create_local_repos.md)).


## Procedure


1. **Enter the omnia_core container**:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```


2. **Configure InfiniBand settings** in the network specification:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/network_spec.yml
   ```


   Add the IB network configuration:

   ```yaml title="File: /opt/omnia/input/project_default/network_spec.yml"
   ---
   ib_network:
     ib_nic_name: "ib0"
     static_range: "10.230.0.101-10.230.0.200"
     subnet: "10.230.0.0"
     netmask: "255.255.255.0"
   ```


3. **Ensure OFED is listed in software_config.json**:

   ```bash title="Run on: omnia_core container"
   cat /opt/omnia/input/project_default/software_config.json | python3 -m json.tool
   ```


   Verify the `softwares` list includes:

   ```json title="File: /opt/omnia/input/project_default/software_config.json"
   {
       "softwares": [
           {"name": "doca_ofed"}
       ]
   }
   ```


4. **Run the omnia.yml playbook** to deploy InfiniBand:

   ```bash title="Run on: omnia_core container"
   cd /omnia
   ansible-playbook omnia.yml --ask-vault-pass
   ```


   The playbook will:

   - Install DOCA-OFED packages on all compute nodes.
   - Load the `mlx5_core` and `mlx5_ib` kernel modules.
   - Configure IPoIB interfaces with static IP addresses.
   - Deploy and start OpenSM on a designated subnet manager node.

5. **(If needed) Manually configure IPoIB on a node**:

   ```bash title="Run on: compute node"
   # Load InfiniBand modules
   modprobe mlx5_core
   modprobe mlx5_ib
   modprobe ib_ipoib

   # Configure the IPoIB interface
   cat <<'EOF' > /etc/sysconfig/network-scripts/ifcfg-ib0
   DEVICE=ib0
   TYPE=InfiniBand
   BOOTPROTO=static
   IPADDR=10.230.0.101
   NETMASK=255.255.255.0
   ONBOOT=yes
   CONNECTED_MODE=yes
   EOF

   ifup ib0
   ```


6. **Configure OpenSM** on the designated subnet manager node:

   ```bash title="Run on: OpenSM node (typically the Slurm control node)"
   dnf install -y opensm
   systemctl enable --now opensm
   ```


   !!! note

       Only one node in the IB fabric should run OpenSM as the primary subnet
       manager. A second node can run OpenSM as a standby for HA.

## Verification


1. **Verify the IB interface is up** on each compute node:

   ```bash title="Run on: compute node"
   ip addr show ib0
   ```


   Expected: the interface shows the assigned IP address and `state UP`.

2. **Check IB port state**:

   ```bash title="Run on: compute node"
   ibstat
   ```


   Expected output:

   ```text title="Expected output on: compute node"
   CA 'mlx5_0'
      Port 1:
         State: Active
         Physical state: LinkUp
         Rate: 200 (HDR)
   ```


3. **Verify OpenSM is running**:

   ```bash title="Run on: OpenSM node"
   systemctl status opensm
   ```


4. **Test IB connectivity** between two compute nodes:

   ```bash title="Run on: compute node 1"
   ping -c 5 10.230.0.102
   ```


5. **Test RDMA bandwidth**:

   On the server node:

   ```bash title="Run on: compute node 1"
   ib_write_bw
   ```


   On the client node:

   ```bash title="Run on: compute node 2"
   ib_write_bw 10.230.0.101
   ```


6. **Test RDMA latency**:

   On the server node:

   ```bash title="Run on: compute node 1"
   ib_write_lat
   ```


   On the client node:

   ```bash title="Run on: compute node 2"
   ib_write_lat 10.230.0.101
   ```


   Expected InfiniBand latency: < 2 microseconds.


## Next Steps


- [Run Hpc Benchmarks](../Slurm/run_hpc_benchmarks.md) -- Run MPI benchmarks over the IB
  fabric.
- [Configure Roce](configure_roce.md) -- Configure RoCE as an alternative to InfiniBand.


## Troubleshooting


**ib0 interface does not appear**
   Verify InfiniBand modules are loaded:

   ```bash title="Run on: compute node"
   lsmod | grep mlx5
   lsmod | grep ib_ipoib
   ```


   Load missing modules:

   ```bash title="Run on: compute node"
   modprobe mlx5_core
   modprobe mlx5_ib
   modprobe ib_ipoib
   ```


**ibstat shows "Down" or "Initializing"**
   - Check physical cable connections.
   - Verify OpenSM is running somewhere in the fabric.
   - Check for firmware issues:

     ```bash title="Run on: compute node"
     ibv_devinfo
     ```


**OpenSM fails to start**
   Check for port GUID conflicts:

   ```bash title="Run on: OpenSM node"
   journalctl -u opensm --no-pager -n 30
   ```


**Poor RDMA performance**
   - Verify link rate (should be 100/200 Gbps for HDR):

     ```bash title="Run on: compute node"
     ibstat | grep Rate
     ```


   - Check for errors on the IB port:

     ```bash title="Run on: compute node"
     perfquery
     ```


   - Ensure `CONNECTED_MODE=yes` in the IPoIB interface configuration.

**IP address conflicts on IB network**
   Check for duplicate IPs:

   ```bash title="Run on: omnia_core container"
   ansible slurm_node -m shell -a "ip addr show ib0 | grep inet"
   ```
