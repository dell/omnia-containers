
# omnia_config.yml Reference


File path: `/opt/omnia/input/project_default/omnia_config.yml`

This file controls the deployment of Slurm, Kubernetes, and GPU software
across cluster nodes.

## Parameter reference


### Slurm settings

--8<-- "html/storage_config.html"

### Kubernetes settings


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `k8s_version` | String | No | `1.29` | Kubernetes version to deploy. Must match a version available in the local repository. |
| `k8s_cni` | String | No | `calico` | Container Network Interface plugin. Currently only `calico` is supported. |
| `k8s_pod_network_cidr` | String | No | `10.244.0.0/16` | CIDR block for Kubernetes pod networking. Must not overlap with any physical network. |
| `k8s_service_cidr` | String | No | `10.96.0.0/12` | CIDR block for Kubernetes ClusterIP services. |
| `metallb_address_range` | String | No | (none) | IP range for MetalLB external load balancer assignments (e.g., `192.168.1.240-192.168.1.250`). Required if MetalLB is enabled. |

### GPU settings


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `enable_nvidia_gpu` | Boolean | No | `false` | Install NVIDIA GPU drivers and CUDA Toolkit on nodes with NVIDIA GPUs. |
| `cuda_toolkit_version` | String | No | `12.4` | CUDA Toolkit version to install. Must be available in the configured repository. |
| `enable_amd_gpu` | Boolean | No | `false` | Install ROCm and AMD GPU drivers on nodes with AMD Instinct GPUs. |
| `rocm_version` | String | No | `6.1` | ROCm version to install. |
| `enable_gpu_slurm_gres` | Boolean | No | `true` | Register GPUs as Slurm GRES (Generic Resources) for GPU-aware job scheduling. Only effective when `scheduler_type` includes `slurm`. |

### Miscellaneous settings


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `login_node_required` | Boolean | No | `true` | Whether to configure a dedicated login node. If `false`, users SSH directly to the Slurm control node. |
| `auth_server_required` | Boolean | No | `true` | Whether to deploy a centralized authentication server (OpenLDAP or FreeIPA). |
| `nfs_client_params` | String | No | (none) | Additional NFS mount options applied to all client-side mounts (e.g., `vers=4.1,noatime`). |

## Usage example


```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
scheduler_type: "slurm,k8s"
slurm_installation_type: "nfs_share"
restart_slurm_services: true

k8s_version: "1.29"
k8s_cni: "calico"
k8s_pod_network_cidr: "10.244.0.0/16"
k8s_service_cidr: "10.96.0.0/12"
metallb_address_range: "192.168.1.240-192.168.1.250"

enable_nvidia_gpu: true
cuda_toolkit_version: "12.4"
enable_amd_gpu: false
enable_gpu_slurm_gres: true

login_node_required: true
auth_server_required: true
```


!!! info

    - [Software Config](software_config.md) -- Package-level software selection.
    - [Slurm Conf](../SampleFiles/slurm_conf.md) -- Custom Slurm configuration.
    - [Ha Config](ha_config.md) -- Kubernetes high-availability settings.
    - [Playbook Reference](../Playbooks/playbook_reference.md) -- The `omnia.yml`
      playbook that consumes this file.
