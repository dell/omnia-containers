# Configure Kubernetes HA

Configure high availability (HA) for the service Kubernetes control plane
by setting a virtual IP (VIP) in `high_availability_config.yml`.

## Overview

Omnia deploys **kube-vip** as a static pod on each control-plane node to
provide a floating virtual IP address for the Kubernetes API server. If the
active control-plane node fails, kube-vip automatically migrates the VIP to
a healthy node, ensuring uninterrupted API access.

The HA configuration is defined in `high_availability_config.yml` and must
be completed **before** running `provision.yml`.

!!! important

    Service Kubernetes cluster deployment is supported **only in HA mode**.
    The `enable_k8s_ha` parameter must be set to `true`.

## Prerequisites

- The [Prepare the OIM](../Setup/prepare_oim.md) procedure is complete.
- The [Configure Inputs](../Setup/configure_inputs.md) procedure is complete,
  including `omnia_config.yml` with the `service_k8s_cluster` section. See
  [omnia_config.yml Reference](../../Reference/Configuration/omnia_config.md)
  for the full parameter list.
- At least **3 nodes** assigned to the `service_kube_control_plane` functional
  group in the PXE mapping file.
- At least **1 node** assigned to the `service_kube_node` functional group.
- A free IPv4 address on the admin network subnet for the VIP. The VIP must
  not overlap with any `ADMIN_IP` in the PXE mapping file, the MetalLB
  `pod_external_ip_range` in `omnia_config.yml`, or the OIM admin IP.

## Procedure

1. **Enter the omnia_core container**:

    ```bash title="Run on: OIM host"
    ssh omnia_core
    ```

2. **Open the HA configuration file**:

    ```bash title="Run on: omnia_core container"
    vi /opt/omnia/input/project_default/high_availability_config.yml
    ```

3. **Set the HA parameters**:

    ```yaml title="File: /opt/omnia/input/project_default/high_availability_config.yml"
    service_k8s_cluster_ha:
      - cluster_name: service_cluster
        enable_k8s_ha: true
        virtual_ip_address: "172.16.107.1"
    ```

    | Parameter | Description |
    |-----------|-------------|
    | `cluster_name` | Must match a cluster name in `omnia_config.yml` where `deployment` is `true` |
    | `enable_k8s_ha` | Must be `true` -- service K8s is supported only in HA mode |
    | `virtual_ip_address` | Free IPv4 address on the admin network subnet for the kube-vip VIP |

4. **Save and close the file**.

!!! tip

    For the full list of `high_availability_config.yml` parameters, see
    [HA Config Reference](../../Reference/Configuration/high_availability_config.md).

## Verification

After the cluster is provisioned, verify that HA is operational.

1. **Verify the VIP is reachable**:

    ```bash title="Run on: OIM host"
    ping -c 3 <virtual_ip_address>
    ```

2. **Check the Kubernetes API via the VIP**:

    ```bash title="Run on: control-plane node"
    kubectl get nodes
    ```

    All control-plane and worker nodes should show `Ready`.

3. **Verify kube-vip is running on control-plane nodes**:

    ```bash title="Run on: control-plane node"
    crictl ps | grep kube-vip
    ```

## Next Steps

- [Configure Inputs](../Setup/configure_inputs.md) -- Configure remaining
  input files before provisioning.
- [Create Mapping File](../Setup/create_mapping_file.md) -- Assign nodes to
  functional groups if not already done.

## Troubleshooting

### VIP is not reachable after provisioning

Verify that kube-vip is running on the control-plane nodes and the static
pod manifest is present:

```bash title="Run on: control-plane node"
crictl ps | grep kube-vip
cat /etc/kubernetes/manifests/kube-vip.yaml
```

### VIP conflict error during input validation

The `virtual_ip_address` must not match any `ADMIN_IP` in the PXE mapping
file, the OIM admin IP, or an IP within the MetalLB `pod_external_ip_range`.
Choose a different free IP on the admin subnet.

### Common error messages

| Error | Cause | Resolution |
|-------|-------|------------|
| `kube_vip is not set` | `virtual_ip_address` is empty | Set a valid IPv4 address in `high_availability_config.yml` |
| `virtual_ip_address conflicts with ADMIN_IP` | VIP matches a node IP in the PXE mapping file | Choose a different VIP on the admin subnet |
| `Kube VIP is not reachable via SSH` | kube-vip failed to start or network issue | Check kube-vip pod logs and network connectivity |
