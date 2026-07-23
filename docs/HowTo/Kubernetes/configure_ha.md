# Configure Kubernetes HA

Configure high availability (HA) for the service Kubernetes control plane
using kube-vip. This page covers the HA architecture, configuration
reference, and troubleshooting.

For the step-by-step deployment procedure including HA configuration, see
[Set Up Service Kubernetes](setup_service_k8s.md).

## Overview

Omnia deploys **kube-vip** as a static pod on each control-plane node to
provide a floating virtual IP (VIP) for the Kubernetes API server. If the
active control-plane node fails, kube-vip automatically migrates the VIP
to a healthy node, ensuring uninterrupted API access.

!!! important
    Service Kubernetes cluster deployment is supported **only in HA mode**.
    The `enable_k8s_ha` parameter must be set to `true`.

## Prerequisites

- A minimum of 3 `service_kube_control_plane_x86_64` nodes are defined in the PXE mapping file.
- The [Configure Inputs](../Setup/configure_inputs.md) procedure is complete.
- A virtual IP address is available on the admin network subnet, not assigned to any other device.

## Procedure

Edit `high_availability_config.yml` in
`/opt/omnia/input/project_default/` **before** running provisioning:

```yaml title="File: /opt/omnia/input/project_default/high_availability_config.yml"
service_k8s_cluster_ha:
  - cluster_name: service_cluster
    enable_k8s_ha: true
    virtual_ip_address: "172.16.107.1"
```

| Parameter | Description |
|---|---|
| `cluster_name` | Must match `cluster_name` in [omnia_config.yml](../../Reference/Configuration/omnia_config.md) where `deployment` is `true` |
| `enable_k8s_ha` | Must be `true` -- service K8s is supported only in HA mode |
| `virtual_ip_address` | Free IPv4 address on the admin subnet. Must not overlap with any `ADMIN_IP` in the [PXE mapping file](../../Reference/SampleFiles/pxe_mapping_file.md), the MetalLB `pod_external_ip_range`, or the OIM admin IP |

For the full parameter reference, see
[HA Config Reference](../../Reference/Configuration/high_availability_config.md).

## Verification

After the cluster is provisioned, verify that HA is operational:

1. **Verify the VIP is reachable**:

    ```bash title="Run on: omnia_core container"
    ping -c 3 <virtual_ip_address>
    ```

2. **Check the Kubernetes API via the VIP**:

    ```bash title="Run on: omnia_core container (example)"
    ssh kcp1 'kubectl get nodes'
    ```

    All control-plane and worker nodes should show `Ready`.

3. **Verify kube-vip is running on control-plane nodes**:

    ```bash title="Run on: omnia_core container (example)"
    ssh kcp1 'crictl ps | grep kube-vip'
    ```

## Next Steps

- [Set Up Service Kubernetes](setup_service_k8s.md) -- Deploy the service
  K8s cluster with HA enabled.

## Troubleshooting

### VIP is not reachable after provisioning

Verify that kube-vip is running on the control-plane nodes and the
static pod manifest is present:

```bash title="Run on: omnia_core container (example)"
ssh kcp1 'crictl ps | grep kube-vip'
ssh kcp1 'cat /etc/kubernetes/manifests/kube-vip.yaml'
```

### VIP conflict error during input validation

The `virtual_ip_address` must not match any `ADMIN_IP` in the
[PXE mapping file](../../Reference/SampleFiles/pxe_mapping_file.md), the
OIM admin IP, or an IP within the MetalLB `pod_external_ip_range`. Choose
a different free IP on the admin subnet.

### Common error messages

| Error | Cause | Resolution |
|---|---|---|
| `kube_vip is not set` | `virtual_ip_address` is empty | Set a valid IPv4 address in [high_availability_config.yml](../../Reference/Configuration/high_availability_config.md) |
| `virtual_ip_address conflicts with ADMIN_IP` | VIP matches a node IP in the [PXE mapping file](../../Reference/SampleFiles/pxe_mapping_file.md) | Choose a different VIP on the admin subnet |
