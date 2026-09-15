# Worker Node VLAN Configuration for iDRAC Telemetry

In multi-subnet deployments, Kubernetes control plane nodes and worker nodes can reside in different admin/PXE subnets. The iDRAC telemetry service is deployed on Kubernetes worker nodes and collects metrics from all BMC endpoints defined in the `BMC_IP` column of `pxe_mapping_file.csv`.

If one or more BMC networks are not directly reachable from the worker node admin/PXE network, an additional VLAN-tagged interface and corresponding static routes must be configured on **all** Kubernetes worker nodes hosting telemetry pods.

## When is this configuration required?

Perform this configuration **only if all** of the following conditions are met:

- iDRAC telemetry is enabled.
- Kubernetes control plane nodes and worker nodes reside in different subnets.
- Telemetry pods are deployed on Kubernetes worker nodes.
- One or more BMC networks are not directly reachable from the worker-node admin/PXE network.
- Additional VLAN tagging and routing are required to access BMC endpoints.

!!! note
    Reachability validation should be performed **from Kubernetes worker nodes** hosting telemetry pods, not from control plane nodes.

## Variables

| Variable | Description | Source | Example |
|---|---|---|---|
| `PARENT_INTERFACE` | PXE/admin NIC on worker node | Run `ip route show default` on the worker node. The output device (e.g., `dev eno16895np0`) is the parent interface. | `eno16895np0` |
| `VLAN_ID` | VLAN ID trunked on switch | Obtain from the site network team. This is the VLAN ID configured on the Top-of-Rack (ToR) switch trunk port that carries BMC traffic. | `702` |
| `VLAN_INTERFACE` | Derived: `PARENT_INTERFACE.VLAN_ID` | Automatically derived by combining `PARENT_INTERFACE` and `VLAN_ID`. | `eno16895np0.702` |
| `VLAN_IP` | Free IP in the BMC VLAN subnet (unique per node) | Obtain from the site network team. Must be an unused IP in the BMC VLAN subnet, unique for each worker node. | `xx.xx.bb.113` |
| `VLAN_NETMASK` | Subnet mask prefix length | Obtain from the site network team. Matches the BMC VLAN subnet prefix length. | `24` |
| `VLAN_GATEWAY` | Gateway that routes to BMC subnets | Obtain from the site network team. This is the default gateway IP for the BMC VLAN subnet. | `xx.xx.bb.1` |
| `BMC_SUBNET` | BMC network(s) to reach | Identify from the `BMC_IP` column in `pxe_mapping_file.csv`. Group BMC IPs by their first three octets to determine unique subnets. See [Part 1: Discover BMC networks](#part-1-discover-bmc-networks). | `xx.xx.aa.0/24` |
| `ROUTE_METRIC` | Route metric | User-defined. Use a value (e.g., `50`) that does not conflict with existing routes. Verify with `ip route show` on the worker node. | `50` |
| `TEST_BMC_IP` | A BMC IP to test connectivity | Pick any BMC IP from the `BMC_IP` column in `pxe_mapping_file.csv` that belongs to an unreachable subnet. | `xx.xx.aa.12` |

## Part 1: Discover BMC networks

Identify the BMC subnets that need to be reachable from worker nodes.

1. Open the PXE mapping file on the omnia_core container:

    ```bash title="Run on: omnia_core container"
    cat /opt/omnia/input/project_default/pxe_mapping_file.csv
    ```

2. Look at the `BMC_IP` column in the output. Group the BMC IPs by their subnet (first three octets). Each unique subnet (e.g., `xx.xx.aa.0/24`) is a BMC network that must be reachable from the worker nodes.

    For the `pxe_mapping_file.csv` format and column definitions, see [PXE Mapping File](../../Reference/SampleFiles/pxe_mapping_file.md).

3. Identify the admin interface on each worker node:

    ```bash title="Run on: Each Kubernetes worker node"
    ip route show default
    ```

## Part 2: VLAN interface configuration

A typical configuration is displayed below.

The following operations must be performed on **all Kubernetes worker nodes**.

### Example

Based on the following example deployment:

```text
Control Plane Network : xx.xx.xx.0/24
Worker Network        : xx.xx.yy.0/24
BMC Networks          : xx.xx.aa.0/24, xx.xx.bb.0/24
VLAN ID               : <VLAN_ID>
VLAN Interface        : <PARENT_INTERFACE>.<VLAN_ID>
VLAN Gateway          : xx.xx.bb.1
VLAN Netmask          : 24
Route Metric          : 50
```

**Worker Node:**

```bash
# VLAN interface creation
ip link show <PARENT_INTERFACE>
sudo ip link add link <PARENT_INTERFACE> name <PARENT_INTERFACE>.<VLAN_ID> type vlan id <VLAN_ID>
sudo ip link set <PARENT_INTERFACE>.<VLAN_ID> up
sudo ip addr add <VLAN_IP>/<VLAN_NETMASK> dev <PARENT_INTERFACE>.<VLAN_ID>
ip -4 a show <PARENT_INTERFACE>.<VLAN_ID>

# Route configuration
ping -c 1 <VLAN_GATEWAY>
sudo ip route add <BMC_SUBNET> via <VLAN_GATEWAY> dev <PARENT_INTERFACE>.<VLAN_ID> metric <ROUTE_METRIC>
ip route show | grep <BMC_SUBNET>
ping -c 2 <TEST_BMC_IP>
```

Expected route on worker nodes:

```text
<BMC_SUBNET> via <VLAN_GATEWAY> dev <PARENT_INTERFACE>.<VLAN_ID> metric <ROUTE_METRIC>
```

!!! note
    Repeat the VLAN interface creation and route configuration steps on **each** Kubernetes worker node, using a unique `VLAN_IP` per node.

## Part 3: Deploy iDRAC telemetry

After VLAN and route configuration has been completed on **all** Kubernetes worker nodes and connectivity to **all** BMC endpoints has been validated, deploy telemetry:

```bash title="Run on: omnia_core container"
cd /omnia/telemetry
ansible-playbook telemetry.yml
```
