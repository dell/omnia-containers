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

## Prerequisites

- Enable iDRAC Telemetry and provide a valid BMC CSV.
- Review `bmc_group_data.csv` and identify every unique subnet represented
  in its `BMC_IP` column.
- Ensure `cluster_inventory` contains
  `service_kube_node_x86_64.hosts` entries with `ansible_host` values.
- Provide common BMC credentials through the Telemetry credential workflow.
- Enable the Redfish API on each BMC.

## Procedure

1. Identify the first service worker in the inventory referenced by
   `telemetry_config.yml`.

2. From the Kubernetes VIP, confirm that the worker accepts the same SSH check
   used by Telemetry:

    ```bash title="Run on: Kubernetes VIP"
    ssh -o ConnectTimeout=10 -o BatchMode=yes -o StrictHostKeyChecking=no \
      <worker-address> echo reachable
    ```

3. Ensure the worker can connect to every BMC address from the configured CSV
   at `https://<BMC_IP>/redfish/v1/`. Telemetry uses HTTP basic authentication,
   a 30-second timeout, and accepts the BMC's self-signed certificate for this
   check.

4. When site VLANs or routes are required, configure them through the site's
   network management process before deploying Telemetry. No VLAN variables or
   VLAN configuration playbook exist in the Telemetry source.

5. Deploy iDRAC Telemetry:

    ```bash title="Run on: OIM"
    cd src/main
    ./omnia.sh --run telemetry --tags deploy
    ```

## Verification

Review `<OMNIA_DATA_PATH>/telemetry/idrac_telemetry_report.yml`. BMCs that pass
reachability, authentication, Redfish, firmware, and license checks are listed
as enabled; failures are separated into invalid, unreachable, Redfish-disabled,
or unsupported results.

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
