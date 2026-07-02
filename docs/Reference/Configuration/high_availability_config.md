# high_availability_config.yml Reference

File path: `/opt/omnia/input/project_default/high_availability_config.yml`

This file configures Kubernetes control plane high availability (HA) using a
virtual IP address and load-balanced API servers.

## HA configuration parameters

--8<-- "html/high_availability_config.html"

## Prerequisites

- Minimum **3 control plane nodes** for a quorum-based HA deployment.
- The `ha_virtual_ip` must be a free IP on the admin network subnet --
  it must not be assigned to any physical server or DHCP range.
- All control plane nodes must have L2 connectivity on the admin network for
  ARP-based virtual IP failover.

## Usage example

```yaml title="File: /opt/omnia/input/project_default/high_availability_config.yml"
---
service_k8s_cluster_ha:
  - cluster_name: service_cluster
    enable_k8s_ha: true
    virtual_ip_address: "172.16.107.1"
```
!!! info

    - [Omnia Config](omnia_config.md) -- Kubernetes deployment settings.
    - [Minimum Nodes](../ClusterRequirements/minimum_nodes.md) -- Minimum node counts for HA deployments.
    - [Ports](../ClusterRequirements/ports.md) -- Kubernetes ports including
      the API server.
