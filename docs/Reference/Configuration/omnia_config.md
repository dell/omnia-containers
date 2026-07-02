
# omnia_config.yml Reference

File path: `/opt/omnia/input/project_default/omnia_config.yml`

This file controls the deployment of Slurm and Kubernetes across cluster nodes.

## Parameter reference
### Slurm Configuration Parameters

--8<-- "html/omnia_config-slurm_cluster.html"

### Kubernetes Configuration Parameters

--8<-- "html/omnia_config-k8s_cluster.html"

## Usage example

```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
---
slurm_cluster:
  - cluster_name: slurm_cluster
    nfs_storage_name: nfs_slurm
    vast_storage_name: vast_storage
    # Optional: Override Slurm and cgroup configuration
    config_sources:
      slurm:
        SlurmctldTimeout: 60
        SlurmdTimeout: 150
        NodeName:
          - NodeName: newnode1
            CPUs: 16
            RealMemory: 64000
          - NodeName: newnode2
            CPUs: 16
            RealMemory: 64000
      cgroup:
        CgroupPlugin: autodetect
        ConstrainCores: True
        ConstrainDevices: True
        ConstrainRAMSpace: True
        ConstrainSwapSpace: True   
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
    etcd_on_local_disk: false
    k8s_cni: "calico"
    pod_external_ip_range: "172.16.107.170-172.16.107.200"
    k8s_service_addresses: "10.233.0.0/18"
    k8s_pod_network_cidr: "10.233.64.0/18"
    nfs_storage_name: "nfs_k8s"
    k8s_crio_storage_size: "20G"
    csi_powerscale_driver_secret_file_path: ""
    csi_powerscale_driver_values_file_path: ""
```


!!! info

    - [Software Config](software_config.md) -- Package-level software selection.
    - [Slurm Conf](../SampleFiles/slurm_conf.md) -- Custom Slurm configuration.
    - [HA Config](high_availability_config.md) -- Kubernetes high-availability settings.
    - [Playbook Reference](../Playbooks/playbook_reference.md) -- The `provision.yml` playbook that consumes this file.
