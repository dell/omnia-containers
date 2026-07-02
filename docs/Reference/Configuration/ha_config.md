
# high_availability_config.yml Reference


File path: `/opt/omnia/input/project_default/high_availability_config.yml`
(also referred to as `ha_config.yml`)

This file configures Kubernetes control plane high availability (HA) using a
virtual IP address and load-balanced API servers.

## Parameter reference


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `ha_enabled` | Boolean | No | `false` | Enable Kubernetes control plane high availability. When `true`, multiple `kube_control_plane` nodes share a virtual IP. |
| `ha_virtual_ip` | String (IP) | Conditional | (none) | Virtual IP address for the Kubernetes API server. Clients and worker nodes connect to this IP instead of a single control plane node. Required when `ha_enabled` is `true`. Must be on the same subnet as the control plane nodes' admin network. |
| `ha_load_balancer` | String | No | `kube-vip` | Load balancer technology for the control plane virtual IP. Accepted values: `kube-vip`. Additional options may be supported in future releases. |
| `ha_control_plane_port` | Integer | No | `6443` | Port on which the Kubernetes API server listens. The virtual IP forwards traffic to this port on all control plane nodes. |
| `ha_etcd_external` | Boolean | No | `false` | Use an external etcd cluster instead of the embedded etcd that runs on each control plane node. When `true`, provide etcd endpoints via `ha_etcd_endpoints`. |
| `ha_etcd_endpoints` | List | Conditional | `[]` | List of external etcd endpoints (e.g., `["https://10.5.0.10:2379", "https://10.5.0.11:2379"]`). Required when `ha_etcd_external` is `true`. |

## HA architecture overview


| Component | Description |
| --- | --- |
| **kube-vip** | Runs as a static pod on each control plane node. One node is elected leader and holds the virtual IP. If the leader fails, another control plane node takes over within seconds. |
| **Virtual IP** | A floating IP that is always routable to the current leader. All `kubelet` and `kubectl` connections target this IP. |
| **etcd** | By default, each control plane node runs its own etcd instance (stacked topology). Alternatively, an external etcd cluster can be specified. |

## Prerequisites


- Minimum **3 control plane nodes** for a quorum-based HA deployment.
- The `ha_virtual_ip` must be a free IP on the admin network subnet --
  it must not be assigned to any physical server or DHCP range.
- All control plane nodes must have L2 connectivity on the admin network for
  ARP-based virtual IP failover.


## Usage example


```yaml title="File: /opt/omnia/input/project_default/high_availability_config.yml"
ha_enabled: true
ha_virtual_ip: "10.5.0.250"
ha_load_balancer: "kube-vip"
ha_control_plane_port: 6443
ha_etcd_external: false
```


!!! info

    - [Omnia Config](omnia_config.md) -- Kubernetes deployment settings.
    - [Minimum Nodes](../ClusterRequirements/minimum_nodes.md) -- Minimum node
      counts for HA deployments.
    - [Ports](../../Overview/security_configuration_guide.md#kubernetes-port-requirements) -- Kubernetes ports including
      the API server.
