
# software_config.json Reference


File path: `/opt/omnia/input/project_default/software_config.json`

This file defines which software packages are installed on each functional
group of nodes. It is a JSON array where each element maps a functional group
to a list of software packages.

## Schema


`software_config.json` is a JSON array of objects. Each object represents
one functional group and specifies the software packages to install on nodes
belonging to that group.

```json title="File: /opt/omnia/input/project_default/software_config.json"
[
  {
    "functional_group_name": "<group_name>",
    "software": [
      {
        "name": "<package_name>",
        "version": "<version>"
      }
    ]
  }
]
```



## Field reference


| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `functional_group_name` | String | Yes | Name of the functional group as defined in the PXE mapping CSV (e.g., `slurm_control_node`, `slurm_node`, `kube_control_plane`, `kube_node`, `login_node`, `auth_server`). |
| `software` | Array | Yes | List of software package objects to install on nodes in this group. |
| `software[].name` | String | Yes | Package or component name. Must match a package known to the Omnia software catalog (see table below). |
| `software[].version` | String | No | Specific version to install. If omitted, the default version bundled with Omnia v2.1 is used. |

## Supported software packages


| Package Name | Applicable Groups | Description |
| --- | --- | --- |
| `slurm` | `slurm_control_node`, `slurm_node`, `login_node` | Slurm workload manager (slurmctld, slurmd, or client tools depending on group). |
| `kubernetes` | `kube_control_plane`, `kube_node` | Kubernetes cluster components (kubeadm, kubelet, kubectl). |
| `calico` | `kube_control_plane` | Calico CNI plugin for pod networking. |
| `metallb` | `kube_control_plane` | MetalLB bare-metal load balancer. |
| `nfs_csi` | `kube_control_plane` | NFS CSI driver for persistent volume provisioning. |
| `nvidia_gpu` | `slurm_node`, `kube_node` | NVIDIA GPU drivers and CUDA Toolkit. |
| `amd_gpu` | `slurm_node`, `kube_node` | AMD ROCm GPU drivers. |
| `openldap` | `auth_server` | OpenLDAP authentication server. |
| `freeipa` | `auth_server` | FreeIPA identity management (alternative to OpenLDAP). |
| `beegfs_client` | `slurm_node`, `kube_node` | BeeGFS parallel filesystem client. |
| `telemetry` | `kube_control_plane`, `kube_node` | Telemetry stack (Kafka, VictoriaMetrics, Grafana). |
| `ldms` | `slurm_node` | LDMS metric samplers for OS-level telemetry. |
| `node_exporter` | All groups | Prometheus-compatible node metrics exporter. |

## Usage example


See [Software Config Json](../SampleFiles/software_config_json.md) for complete annotated
examples covering Slurm-only, Slurm + K8s, and telemetry-only scenarios.

```json title="File: /opt/omnia/input/project_default/software_config.json"
[
  {
    "functional_group_name": "slurm_control_node",
    "software": [
      {"name": "slurm", "version": "23.11"},
      {"name": "node_exporter"}
    ]
  },
  {
    "functional_group_name": "slurm_node",
    "software": [
      {"name": "slurm", "version": "23.11"},
      {"name": "nvidia_gpu"},
      {"name": "ldms"},
      {"name": "node_exporter"}
    ]
  },
  {
    "functional_group_name": "kube_control_plane",
    "software": [
      {"name": "kubernetes", "version": "1.29"},
      {"name": "calico"},
      {"name": "metallb"},
      {"name": "nfs_csi"}
    ]
  }
]
```


!!! note

    - The `functional_group_name` must exactly match the value in the
      `FUNCTIONAL_GROUP_NAME` column of the PXE mapping CSV.
    - If a functional group has no entry in `software_config.json`, only
      the base OS packages are installed on those nodes.
    - Invalid package names cause `input_validator.yml` to fail with a
      descriptive error.

!!! info

    - [Software Config Json](../SampleFiles/software_config_json.md) -- Complete sample
      files for different scenarios.
    - [Pxe Mapping File](../SampleFiles/pxe_mapping_file.md) -- PXE mapping CSV that
      defines functional groups.
    - [Local Repo Config](local_repo_config.md) -- Repository sources for these packages.
