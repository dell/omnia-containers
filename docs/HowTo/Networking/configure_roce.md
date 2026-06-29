
# Configure RoCE


Set up RDMA over Converged Ethernet (RoCE) on compute nodes for
high-performance, low-latency networking without an InfiniBand switch.

## Overview


RoCE (RDMA over Converged Ethernet) enables RDMA communication over standard
Ethernet infrastructure. This eliminates the need for a dedicated InfiniBand
switch while providing near-InfiniBand performance for many workloads.

Omnia supports:

- **RoCEv2** -- RDMA over UDP/IP (routable, recommended for most deployments).
- **NVIDIA ConnectX** adapters in Ethernet mode.
- **Priority Flow Control (PFC)** for lossless Ethernet.
- **ECN (Explicit Congestion Notification)** for congestion management.


## Prerequisites


- Compute nodes have NVIDIA ConnectX adapters capable of RoCE (ConnectX-4 or
  later).
- Adapters are configured in Ethernet mode (not InfiniBand mode).
- Ethernet switches support Priority Flow Control (PFC) and ECN.
- `software_config.json` includes the OFED/DOCA driver package.
- A dedicated VLAN or subnet is available for RoCE traffic.


## Procedure


1. **Enter the omnia_core container**:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```


2. **Configure the RoCE network** in the network specification:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/network_spec.yml
   ```


   ```yaml title="File: /opt/omnia/input/project_default/network_spec.yml"
   ---
   roce_network:
     nic_name: "ens10f0"
     static_range: "10.231.0.101-10.231.0.200"
     subnet: "10.231.0.0"
     netmask: "255.255.255.0"
     mtu: 9000
   ```


3. **Run the omnia.yml playbook**:

   ```bash title="Run on: omnia_core container"
   cd /omnia
   ansible-playbook omnia.yml --ask-vault-pass
   ```


4. **(If needed) Manually configure RoCE on a compute node**:

   a. **Install OFED packages**:

      ```bash title="Run on: compute node"
      dnf install -y rdma-core libibverbs-utils infiniband-diags
      ```


   b. **Configure the network interface** with jumbo frames:

      ```bash title="Run on: compute node"
      cat <<'EOF' > /etc/sysconfig/network-scripts/ifcfg-ens10f0
      DEVICE=ens10f0
      TYPE=Ethernet
      BOOTPROTO=static
      IPADDR=10.231.0.101
      NETMASK=255.255.255.0
      ONBOOT=yes
      MTU=9000
      EOF

      ifup ens10f0
      ```


   c. **Enable RoCEv2 mode** on the adapter:

      ```bash title="Run on: compute node"
      cma_roce_mode -d mlx5_0 -p 1 -m 2
      ```


      Mode `2` selects RoCEv2 (UDP/IP based).

   d. **Configure Priority Flow Control (PFC)**:

      ```bash title="Run on: compute node"
      mlnx_qos -i ens10f0 --pfc 0,0,0,1,0,0,0,0
      ```


      This enables PFC on traffic class 3, which is typically used for RoCE.

   e. **Configure ECN (Explicit Congestion Notification)**:

      ```bash title="Run on: compute node"
      sysctl -w net.ipv4.tcp_ecn=1
      echo "net.ipv4.tcp_ecn=1" >> /etc/sysctl.d/roce.conf
      ```


5. **Configure the Ethernet switch** for lossless RoCE traffic:

   !!! note

       Switch configuration is vendor-specific. Consult your switch
       documentation. The following is an example for Dell OS10 switches:

   ```text title="Run on: Ethernet switch (Dell OS10 example)"
   configure terminal
   interface ethernet 1/1/1-1/1/48
     priority-flow-control mode on
     priority-flow-control priority 3 no-drop
     mtu 9216
   exit
   ```



## Verification


1. **Verify the network interface is up** with jumbo frames:

   ```bash title="Run on: compute node"
   ip addr show ens10f0
   ip link show ens10f0 | grep mtu
   ```


   MTU should show `9000`.

2. **Verify RDMA devices are available**:

   ```bash title="Run on: compute node"
   ibv_devices
   ```


   Expected output:

   ```text title="Expected output on: compute node"
   device          node GUID
   ------          ----------------
   mlx5_0          0002c9030005abcd
   ```


3. **Verify RoCE mode**:

   ```bash title="Run on: compute node"
   cma_roce_mode -d mlx5_0 -p 1
   ```


   Expected: `RoCE v2`

4. **Test RDMA bandwidth** over RoCE:

   On the server node:

   ```bash title="Run on: compute node 1"
   ib_write_bw -d mlx5_0
   ```


   On the client node:

   ```bash title="Run on: compute node 2"
   ib_write_bw -d mlx5_0 10.231.0.101
   ```


5. **Test RDMA latency** over RoCE:

   On the server node:

   ```bash title="Run on: compute node 1"
   ib_write_lat -d mlx5_0
   ```


   On the client node:

   ```bash title="Run on: compute node 2"
   ib_write_lat -d mlx5_0 10.231.0.101
   ```


   Expected RoCE latency: 3-10 microseconds (higher than IB but lower than
   TCP/IP).

6. **Verify PFC counters** (should show no drops):

   ```bash title="Run on: compute node"
   ethtool -S ens10f0 | grep -i pfc
   ```



## Next Steps


- [Configure Infiniband](configure_infiniband.md) -- Compare with InfiniBand for higher
  performance.
- [Run Hpc Benchmarks](../Slurm/run_hpc_benchmarks.md) -- Benchmark MPI performance over
  RoCE.


## Troubleshooting


**ibv_devices shows no devices**
   Verify RDMA modules are loaded:

   ```bash title="Run on: compute node"
   modprobe mlx5_core
   modprobe rdma_ucm
   ```


**RDMA tests fail with "Connection refused"**
   - Verify both nodes can ping each other on the RoCE network.
   - Check firewall rules:

     ```bash title="Run on: compute node"
     firewall-cmd --add-port=18515/tcp --permanent
     firewall-cmd --reload
     ```


**Performance is poor (< 10 Gbps)**
   - Verify MTU is 9000 on both nodes and the switch:

     ```bash title="Run on: compute node"
     ip link show ens10f0
     ```


   - Verify PFC is enabled to prevent packet drops:

     ```bash title="Run on: compute node"
     mlnx_qos -i ens10f0
     ```


**Packet drops on the switch**
   Ensure PFC is configured correctly on all switch ports in the RoCE VLAN.
   Check switch counters for PFC pause frames.

**Adapter is in InfiniBand mode instead of Ethernet**
   Change the port mode using `mstconfig`:

   ```bash title="Run on: compute node"
   mstconfig -d mlx5_0 set LINK_TYPE_P1=ETH
   ```


   Reboot the node for the change to take effect.
