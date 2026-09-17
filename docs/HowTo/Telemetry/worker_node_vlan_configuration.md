# Worker Node VLAN Configuration for iDRAC Telemetry

## Overview

In multi-subnet deployments, Kubernetes control plane nodes and worker nodes
can reside in different admin or PXE subnets. The iDRAC Telemetry service is
deployed on Kubernetes worker nodes and collects metrics from all BMC endpoints
in its configured `bmc_group_data.csv` runtime inventory. Use the `BMC_IP`
column of Orchestrator's `bmc_group_data.csv` to identify the BMC networks
that the workers must reach.

The generated BMC mapping is available at:

```text
$ORCHESTRATOR_DATA_PATH/output/$OMNIA_PROJECT_NAME/bmc_group_data.csv
```

See the [Telemetry domain contract](../../Reference/domain_contracts/telemetry_contract.md#bmc_group_datacsv)
for the file contract.

If one or more BMC networks are not directly reachable from the worker-node
admin or PXE network, configure an additional VLAN-tagged interface and the
required static routes on every Kubernetes worker node that can host Telemetry
pods.

When iDRAC Telemetry synchronizes its BMC inventory, it delegates Redfish
validation and Telemetry enablement to the first reachable service Kubernetes
worker in the configured inventory. If the first worker cannot be reached over
SSH, it tries the second worker when one exists and then falls back to the
Kubernetes VIP. Each BMC must be reachable over HTTPS from the selected host.

The Telemetry source does not create VLAN interfaces or routes. Those settings
must already provide the connectivity required by the iDRAC workflow.

### When is this configuration required?

Prepare the worker-node VLAN only when all the following conditions apply:

- iDRAC Telemetry is enabled.
- Kubernetes control plane nodes and worker nodes reside in different subnets.
- Telemetry pods are deployed on Kubernetes worker nodes.
- One or more BMC networks are not directly reachable from the worker-node
  admin or PXE network.
- VLAN tagging and static routes are required to reach the BMC endpoints.

!!! note

    Validate BMC reachability from every Kubernetes worker node that can host
    Telemetry pods, not only from the control plane nodes.

## Variables

The following placeholders are used when planning and applying the worker-node
VLAN configuration. They are not settings in a Telemetry input file.

| Variable | Description | Source | Example |
|---|---|---|---|
| `PARENT_INTERFACE` | PXE or admin NIC on the worker node. | Run `ip route show default` on the worker node. The output device, such as `dev eno16895np0`, is the parent interface. | `eno16895np0` |
| `VLAN_ID` | VLAN ID trunked on the switch. | Obtain the VLAN ID configured on the Top-of-Rack switch port that carries BMC traffic from the site network team. | `702` |
| `VLAN_INTERFACE` | VLAN-tagged interface derived from `PARENT_INTERFACE.VLAN_ID`. | Combine `PARENT_INTERFACE` and `VLAN_ID`. | `eno16895np0.702` |
| `VLAN_IP` | Free address in the BMC VLAN subnet, unique to each worker node. | Obtain an unused address from the site network team. | `xx.xx.bb.113` |
| `VLAN_NETMASK` | BMC VLAN subnet prefix length. | Obtain the prefix length from the site network team. | `24` |
| `VLAN_GATEWAY` | Gateway that routes to the BMC subnets. | Obtain the BMC VLAN gateway from the site network team. | `xx.xx.bb.1` |
| `BMC_SUBNET` | BMC network that the worker must reach. | Identify each unique network from the `BMC_IP` column in `$ORCHESTRATOR_DATA_PATH/output/$OMNIA_PROJECT_NAME/bmc_group_data.csv`. Use the subnet prefix assigned by the site network team. | `xx.xx.aa.0/24` |
| `ROUTE_METRIC` | Static-route metric. | Choose a value that does not conflict with existing routes; verify with `ip route show` on the worker node. | `50` |
| `TEST_BMC_IP` | BMC address used to test connectivity. | Select an address in an unreachable subnet from the `BMC_IP` column in `$ORCHESTRATOR_DATA_PATH/output/$OMNIA_PROJECT_NAME/bmc_group_data.csv`. | `xx.xx.aa.12` |

## Prerequisites

- Enable iDRAC Telemetry and provide a valid BMC CSV.
- Review `bmc_group_data.csv` and identify every unique subnet represented
  in its `BMC_IP` column.
- Ensure `cluster_inventory` contains
  `service_kube_node_x86_64.hosts` entries with `ansible_host` values.
- Provide common BMC credentials through the Telemetry credential workflow.
- Enable the Redfish API on each BMC.

## Procedure

### Part 1: Identify BMC networks and validate worker reachability

1. Load the installed environment and resolve the Orchestrator-generated BMC
   inventory:

    ```bash title="Run on: OIM host"
    source /etc/profile.d/omnia-env.sh
    orchestrator_path="${ORCHESTRATOR_DATA_PATH:-${OMNIA_DATA_PATH}/orchestrator}"
    bmc_inventory="$orchestrator_path/output/$OMNIA_PROJECT_NAME/bmc_group_data.csv"
    test -r "$bmc_inventory"
    ```

2. List the BMC addresses that the workers must reach:

    ```bash title="Run on: OIM host"
    awk -F, 'NR > 1 {
      gsub(/^[ \t]+|[ \t]+$/, "", $1)
      if ($1 != "") print $1
    }' "$bmc_inventory" | sort -u
    ```

    Map each address to the actual subnet and prefix supplied by the site
    network team. Do not infer a `/24` prefix from the first three octets; the
    required CIDR depends on the site's BMC network design. Use each resulting
    CIDR as a `BMC_SUBNET` value.

3. Identify the first service worker in the inventory referenced by
   `telemetry_config.yml`. Use the configured `cluster_inventory` path:

    ```bash title="Run on: OIM host"
    ansible-inventory -i <cluster_inventory-path> \
      --graph service_kube_node_x86_64
    ```

    Telemetry tries the first worker, retries unreachable BMCs from the second
    worker when present, and falls back to the Kubernetes VIP when worker SSH
    access is unavailable. Validate every listed worker because Telemetry pods
    can be scheduled on any of them.

4. From the Kubernetes VIP, confirm that the worker accepts the same SSH check
   used by Telemetry:

    ```bash title="Run on: Kubernetes VIP"
    ssh -o ConnectTimeout=10 -o BatchMode=yes -o StrictHostKeyChecking=no \
      <worker-address> echo reachable
    ```

5. On every Kubernetes worker that can host Telemetry pods, check the selected
   route and HTTPS reachability for each BMC address:

    ```bash title="Run on: Each Kubernetes worker node"
    ip route get <BMC_IP>
    curl --insecure --connect-timeout 30 --silent --show-error \
      --output /dev/null --write-out '%{http_code}\n' \
      "https://<BMC_IP>/redfish/v1/"
    ```

    Any HTTP response confirms that the Redfish endpoint is reachable. A `401`
    response is expected when this connectivity-only command is run without
    credentials. During deployment, Telemetry uses the configured common BMC
    credentials and accepts the BMC's self-signed certificate.

### Part 2: Configure the VLAN interface and routes

Perform the following operations on every Kubernetes worker node that can host
Telemetry pods. Use a unique `VLAN_IP` on each worker and repeat the route
command for every required `BMC_SUBNET`.

```bash title="Run on: Each Kubernetes worker node"
# Inspect the parent interface before changing it.
ip link show <PARENT_INTERFACE>

# Create and address the VLAN interface.
sudo ip link add link <PARENT_INTERFACE> \
  name <PARENT_INTERFACE>.<VLAN_ID> type vlan id <VLAN_ID>
sudo ip link set <PARENT_INTERFACE>.<VLAN_ID> up
sudo ip addr add <VLAN_IP>/<VLAN_NETMASK> \
  dev <PARENT_INTERFACE>.<VLAN_ID>
ip -4 address show <PARENT_INTERFACE>.<VLAN_ID>

# Add and verify the route to a BMC subnet.
ping -c 1 <VLAN_GATEWAY>
sudo ip route add <BMC_SUBNET> via <VLAN_GATEWAY> \
  dev <PARENT_INTERFACE>.<VLAN_ID> metric <ROUTE_METRIC>
ip route show | grep --fixed-strings '<BMC_SUBNET>'
ping -c 2 <TEST_BMC_IP>
```

The expected route has this form:

```text
<BMC_SUBNET> via <VLAN_GATEWAY> dev <PARENT_INTERFACE>.<VLAN_ID> metric <ROUTE_METRIC>
```

!!! warning

    The `ip` commands above configure the running system and do not persist
    across a reboot. After validating connectivity, use the site's supported
    network-management method to make the VLAN interface and routes persistent.
    Telemetry does not create or maintain VLAN interfaces and routes.

### Part 3: Deploy iDRAC Telemetry

After configuring every applicable worker and confirming that each BMC Redfish
endpoint is reachable, deploy the enabled Telemetry sources and sinks:

```bash title="Run on: OIM host"
cd <OMNIA_SOURCE_PATH>/src/main
./omnia.sh --run telemetry --tags deploy
```

## Verification

Review
`$TELEMETRY_DATA_PATH/output/$OMNIA_PROJECT_NAME/idrac_telemetry_report.yml`.
When `TELEMETRY_DATA_PATH` is unset, use
`$OMNIA_DATA_PATH/telemetry/output/$OMNIA_PROJECT_NAME/idrac_telemetry_report.yml`.
BMCs that pass reachability, authentication, Redfish, firmware, and license
checks are listed as enabled; failures are separated into invalid,
unreachable, Redfish-disabled, or unsupported results.

## Next steps

- Complete [Configure iDRAC Telemetry](configure_idrac.md).

## Troubleshooting

- **The worker SSH check fails:** Restore SSH reachability from the VIP. The
  workflow retries the second service worker, when present, and then falls back
  to the VIP for BMC validation, but worker access is the intended path.
- **A BMC returns `401`:** Correct the common BMC credentials.
- **A BMC returns `404`:** Enable its Redfish API.
- **A BMC times out or has a connection error:** Correct the external network
  path. Telemetry reports the BMC as unreachable and does not configure the
  missing VLAN or route.
