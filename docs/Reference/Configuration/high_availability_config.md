# high_availability_config.yml

This file configures Kubernetes control plane high availability (HA) using a
virtual IP address and load-balanced API servers.

Configure exactly one entry in `service_k8s_cluster_ha`. Its `cluster_name`
must match the single `service_k8s_cluster` entry selected with
`deployment: true` in `omnia_config.yml`. The provisioning path uses
`virtual_ip_address` to generate kube-vip and Kubernetes API configuration
regardless of the `enable_k8s_ha` value, so set `enable_k8s_ha: true` for the
supported configuration.

## Parameter Reference

--8<-- "html/high_availability_config.html"

## Prerequisites

- Add the matching service Kubernetes cluster to `omnia_config.yml`.
- The `virtual_ip_address` must be a free IP on the admin network subnet --
  it must not be assigned to any physical server or DHCP range.
- Define at least three control-plane nodes for the supported HA topology. The
  validator checks the cluster-name relationship, VIP subnet, shared
  control-plane subnet, complete `pod_external_ip_range` placement, and
  configured-address conflicts; it does not enforce the control-plane node
  count or detect addresses used by external devices.

## Usage example

```yaml title="File: $OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/high_availability_config.yml"
---
service_k8s_cluster_ha:
  - cluster_name: service_cluster
    enable_k8s_ha: true
    virtual_ip_address: "172.16.107.1"
```

!!! info

    - [Omnia Config](omnia_config.md) -- Kubernetes deployment settings.
    - [Minimum Nodes](../ClusterRequirements/minimum_nodes.md) -- Minimum node counts for HA deployments.
    - [Ports](../../SecurityConfigurationGuide/network_security.md#kubernetes-port-requirements) -- Kubernetes ports including
      the API server.












