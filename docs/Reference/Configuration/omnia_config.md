
# omnia_config.yml

This file controls the deployment of Slurm and Kubernetes across cluster nodes.

## Parameter reference
### Slurm Configuration Parameters

--8<-- "html/omnia_config-slurm_cluster.html"

This release supports one Slurm cluster configuration. When Slurm is enabled,
supply one item in `slurm_cluster`; the current implementation reads only the
first item and does not process additional items. `vast_storage_name` is
optional. When it is empty or omitted, Orchestrator reuses `nfs_storage_name`
for Slurm shared-data and HPC-tools paths and skips the standard mount whose
`name` is `vast_storage`. When set, `vast_storage_name` must exactly match one
mount `name` in `storage_config.yml`.

### Kubernetes Configuration Parameters

--8<-- "html/omnia_config-k8s_cluster.html"

PowerScale CSI is controlled by `enable_powerscale_csi` on the
`service_k8s_cluster` selected with `deployment: true`. The optional Boolean
defaults to `false`. When set to `true`, both
`csi_powerscale_driver_secret_file_path` and
`csi_powerscale_driver_values_file_path` are required and must identify
existing regular files by absolute path. Catalog membership and populated file
paths do not enable CSI when the flag is `false` or omitted.

When service Kubernetes is configured, set `deployment: true` on exactly one
`service_k8s_cluster` item. Other entries may remain in the list with
`deployment: false`, but Orchestrator deploys only the selected item. Input
validation rejects configurations with no selected cluster or with multiple
entries marked `true`. When the PXE mapping selects Kubernetes functional
groups, the item selected with `deployment: true` must define a nonempty
`nfs_storage_name` that exists in `storage_config.yml`. Retained entries with
`deployment: false` are not deployed and need not define that storage name.

For the deployed cluster, `pod_external_ip_range`, `k8s_service_addresses`,
and `k8s_pod_network_cidr` must be valid, mutually non-overlapping IPv4
ranges. The service and pod CIDRs must be canonical networks and must not
overlap a physical network in `network_spec.yml`. The external pool must not
overlap a DHCP pool or contain an OIM address or any `ADMIN_IP`, `BMC_IP`, or
`IB_IP` from the PXE mapping file.

### Provisioning bolt-ons

The optional `orchestrator.bolt_ons` mapping overrides the bolt-on list for a
workload category. Supplying a category list replaces that category's default;
it does not extend it. Values must be unique and may contain only the names
shown below:

| Category | Default list | Accepted values |
| --- | --- | --- |
| `kubernetes` | `mount_config`, `k8s_config`, `telemetry` | `mount_config`, `k8s_config`, `telemetry`, `openldap` |
| `slurm` | `mount_config`, `slurm_config`, `openldap` | `mount_config`, `slurm_config`, `openldap` |

Adding `openldap` to the Kubernetes list enables LDAP client configuration
only when the selected catalog also enables OpenLDAP. The current Kubernetes
provisioning play does not invoke a telemetry role from the `telemetry` list
item; deploy Telemetry through its domain workflow.

## Usage example

```yaml title="File: $OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/omnia_config.yml"
---
slurm_cluster:
  - cluster_name: slurm_cluster
    nfs_storage_name: nfs_slurm
    vast_storage_name: vast_storage
    node_discovery_mode: "homogeneous"
    # Optional: Override Slurm and cgroup configuration
    config_sources:
      slurm: /path/to/custom/slurm.conf
      cgroup: /path/to/custom/cgroup.conf
      # slurm:
      #   SlurmctldTimeout: 60
      #   SlurmdTimeout: 150
    # Optional: Override hardware specs for specific node groups
    node_hardware_defaults:
      grp1:
        sockets: 2
        cores_per_socket: 64
        threads_per_core: 2
        real_memory: 512000
        gres: "gpu:4"
      grp2:
        sockets: 2
        cores_per_socket: 32
        threads_per_core: 2
        real_memory: 256000

service_k8s_cluster:
  - cluster_name: service_cluster
    deployment: true
    enable_powerscale_csi: false
    etcd_on_local_disk: false
    k8s_cni: "calico"
    pod_external_ip_range: "172.16.107.170-172.16.107.200"
    k8s_service_addresses: "10.233.0.0/18"
    k8s_pod_network_cidr: "10.233.64.0/18"
    nfs_storage_name: "nfs_k8s"
    k8s_crio_storage_size: "20G"
    csi_powerscale_driver_secret_file_path: ""
    csi_powerscale_driver_values_file_path: ""

# Optional: replace the default bolt-on lists for either category.
orchestrator:
  bolt_ons:
    kubernetes:
      - mount_config
      - k8s_config
      - openldap
    slurm:
      - mount_config
      - slurm_config
      - openldap
```


!!! info

    - [Orchestrator Config](orchestrator_config.md) -- Provisioning, catalog path, and upstream output settings.
    - [Slurm Conf](../SampleFiles/slurm_conf.md) -- Custom Slurm configuration.
    - [HA Config](high_availability_config.md) -- Kubernetes high-availability settings.
    - [Slurm Storage Architecture](../../HowTo/orchestrator/deploy_slurm.md#slurm-storage-architecture) -- How NFS and VAST mounts are used by Slurm.
    - [K8s Storage Architecture](../../HowTo/orchestrator/deploy_kubernetes.md#k8s-storage-architecture) -- How NFS mounts are used by service K8s.








