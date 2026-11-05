# Configure Kubernetes HA

Configure high availability (HA) for the service Kubernetes control plane
using kube-vip. This page covers the HA architecture, configuration
reference, and troubleshooting.

For the step-by-step deployment procedure including HA configuration, see
[Set Up Service Kubernetes](deploy_kubernetes.md).

## Overview

Omnia deploys **kube-vip** as a static pod on each control-plane node to
provide a floating virtual IP (VIP) for the Kubernetes API server. If the
active control-plane node fails, kube-vip automatically migrates the VIP
to a healthy node, ensuring uninterrupted API access.

!!! important
    Configure HA settings in the deployed `service_k8s_cluster` entry in
    `omnia_config.yml`. Set `enable_k8s_ha: true` and provide a
    `virtual_ip_address` on the entry with `deployment: true`.

## Prerequisites

- For an HA topology, define at least three control-plane nodes in the PXE
  mapping. Use the catalog-qualified functional-group name, such as
  `service_kube_control_plane_rhel_10_0_x86_64` or
  `service_kube_control_plane_rhel_10_2_x86_64`. The RHEL minor version must
  match the selected catalog and must be the same for every Kubernetes node.
- `omnia_config.yml` and the PXE mapping file are staged for the project.
- A virtual IP address is available on the admin network subnet, not assigned to any other device.

## Procedure

Edit `omnia_config.yml` in the active project's Orchestrator input
directory and add HA settings to the deployed `service_k8s_cluster` entry:

```yaml title="File: omnia_config.yml"
service_k8s_cluster:
  - cluster_name: service_cluster
    deployment: true
    enable_k8s_ha: true
    virtual_ip_address: "172.16.107.1"
    # ... other service_k8s_cluster parameters ...
```

|| Parameter | Description |
||---|---|
|| `enable_k8s_ha` | Set to `true` to enable HA for the Kubernetes service node. Required when Kubernetes nodes are mapped. |
|| `virtual_ip_address` | IPv4 address consumed by the generated kube-vip and Kubernetes API configuration. Reserve a free address on the admin subnet that does not overlap any `ADMIN_IP`, the MetalLB `pod_external_ip_range`, or the OIM admin IP. |

The input validator checks the HA cluster-name relationship, IPv4 syntax, VIP
placement in the control-plane admin subnet, and conflicts with OIM, mapped
node, DHCP, and MetalLB addresses. It also requires every mapped control-plane
node to use the same admin subnet and the complete `pod_external_ip_range` to
belong to that subnet. The minimum three-control-plane-node HA topology remains
an operational planning requirement and is not enforced by input validation.

For the full parameter reference, see
[Omnia Config Reference](../../Reference/Configuration/omnia_config.md).

## Verification

After the cluster is provisioned, verify that HA is operational:

1. **Verify the VIP is reachable**:

    ```bash title="Run on: OIM"
    ping -c 3 <virtual_ip_address>
    ```

2. **Check the Kubernetes API via the VIP**:

    ```bash title="Run on: OIM (example)"
    ssh kcp1 'kubectl get nodes'
    ```

    All control-plane and worker nodes should show `Ready`.

3. **Verify kube-vip is running on control-plane nodes**:

    ```bash title="Run on: OIM (example)"
    ssh kcp1 'crictl ps | grep kube-vip'
    ```

## Next steps

- [Set Up Service Kubernetes](deploy_kubernetes.md) -- Deploy the service
  K8s cluster with HA enabled.

## Troubleshooting

### VIP is not reachable after provisioning

Verify that kube-vip is running on the control-plane nodes and the
static pod manifest is present:

```bash title="Run on: OIM (example)"
ssh kcp1 'crictl ps | grep kube-vip'
ssh kcp1 'cat /etc/kubernetes/manifests/kube-vip.yaml'
```

### VIP conflicts with another address or is unreachable

Run the Orchestrator `validate` phase and resolve the reported HA conflict. The
validator requires `virtual_ip_address` to belong to the control-plane admin
subnet and rejects collisions with OIM admin or BMC addresses, mapped node
admin, BMC, or InfiniBand addresses, DHCP ranges, and
`pod_external_ip_range`. If validation succeeds but kube-vip still cannot
claim the address, check for an external device using the VIP; that live
network condition cannot be detected from the input files.

### Common error messages

|| Symptom | Cause | Resolution |
||---|---|---|
|| Input validation rejects `virtual_ip_address` | The value is missing, empty, invalid, outside the shared control-plane subnet, or conflicts with a reserved address | Set a valid, free IPv4 address in the `service_k8s_cluster` entry in `omnia_config.yml`, then rerun the `validate` phase. |
|| VIP is unreachable or kube-vip repeatedly restarts | VIP is outside the admin subnet, already in use, or the control-plane interface cannot claim it | Correct the VIP or network configuration, then reprovision the affected Kubernetes nodes. |
