
# software_config.json Sample Files


File path: `/opt/omnia/input/project_default/software_config.json`

This page provides complete, annotated `software_config.json` examples for
common deployment scenarios. Copy the scenario that best matches your
deployment and modify as needed.

## Scenario 1: Slurm-only cluster


Deploys a traditional HPC cluster with Slurm scheduling, NVIDIA GPU support,
and LDMS telemetry on compute nodes. No Kubernetes.

```json title="Sample software_config.json: Slurm-only cluster"
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
    "functional_group_name": "login_node",
    "software": [
      {"name": "slurm", "version": "23.11"},
      {"name": "node_exporter"}
    ]
  },
  {
    "functional_group_name": "auth_server",
    "software": [
      {"name": "openldap"},
      {"name": "node_exporter"}
    ]
  }
]
```


**Scenario 1 component summary**

| Group | Installed Software |
| --- | --- |
| `slurm_control_node` | Slurm 23.11 (slurmctld, slurmdbd), Node Exporter |
| `slurm_node` | Slurm 23.11 (slurmd), NVIDIA GPU drivers/CUDA, LDMS samplers, Node Exporter |
| `login_node` | Slurm 23.11 (client tools), Node Exporter |
| `auth_server` | OpenLDAP, Node Exporter |

## Scenario 2: Slurm + Kubernetes (full deployment)


Production-grade deployment with Slurm for HPC compute and Kubernetes for
platform services, monitoring, and storage.

```json title="Sample software_config.json: Slurm + Kubernetes"
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
      {"name": "beegfs_client"},
      {"name": "node_exporter"}
    ]
  },
  {
    "functional_group_name": "login_node",
    "software": [
      {"name": "slurm", "version": "23.11"},
      {"name": "node_exporter"}
    ]
  },
  {
    "functional_group_name": "kube_control_plane",
    "software": [
      {"name": "kubernetes", "version": "1.29"},
      {"name": "calico"},
      {"name": "metallb"},
      {"name": "nfs_csi"},
      {"name": "telemetry"},
      {"name": "node_exporter"}
    ]
  },
  {
    "functional_group_name": "kube_node",
    "software": [
      {"name": "kubernetes", "version": "1.29"},
      {"name": "node_exporter"}
    ]
  },
  {
    "functional_group_name": "auth_server",
    "software": [
      {"name": "openldap"},
      {"name": "node_exporter"}
    ]
  }
]
```


**Scenario 2 component summary**

| Group | Installed Software |
| --- | --- |
| `slurm_control_node` | Slurm 23.11 (slurmctld, slurmdbd), Node Exporter |
| `slurm_node` | Slurm 23.11 (slurmd), NVIDIA GPU, LDMS, BeeGFS client, Node Exporter |
| `login_node` | Slurm 23.11 (client), Node Exporter |
| `kube_control_plane` | K8s 1.29, Calico, MetalLB, NFS CSI, Telemetry stack, Node Exporter |
| `kube_node` | K8s 1.29, Node Exporter |
| `auth_server` | OpenLDAP, Node Exporter |

## Scenario 3: Kubernetes + telemetry only (no Slurm)


Deploys a Kubernetes cluster with the full telemetry pipeline for
infrastructure monitoring without a job scheduler.

```json title="Sample software_config.json: Kubernetes + telemetry only"
[
  {
    "functional_group_name": "kube_control_plane",
    "software": [
      {"name": "kubernetes", "version": "1.29"},
      {"name": "calico"},
      {"name": "metallb"},
      {"name": "nfs_csi"},
      {"name": "telemetry"},
      {"name": "node_exporter"}
    ]
  },
  {
    "functional_group_name": "kube_node",
    "software": [
      {"name": "kubernetes", "version": "1.29"},
      {"name": "node_exporter"}
    ]
  }
]
```


**Scenario 3 component summary**

| Group | Installed Software |
| --- | --- |
| `kube_control_plane` | K8s 1.29, Calico, MetalLB, NFS CSI, Telemetry stack (Kafka, VictoriaMetrics, Grafana), Node Exporter |
| `kube_node` | K8s 1.29, Node Exporter |

## Scenario 4: AMD GPU compute nodes


Slurm cluster with AMD Instinct GPU nodes instead of NVIDIA.

```json title="Sample software_config.json: AMD GPU compute nodes"
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
      {"name": "amd_gpu"},
      {"name": "ldms"},
      {"name": "node_exporter"}
    ]
  },
  {
    "functional_group_name": "login_node",
    "software": [
      {"name": "slurm", "version": "23.11"},
      {"name": "node_exporter"}
    ]
  }
]
```



!!! note

    - The `version` field is optional. When omitted, Omnia installs the
      default version bundled with the release.
    - Every `functional_group_name` must match an entry in the PXE mapping
      CSV (see [Pxe Mapping File](pxe_mapping_file.md)).
    - Groups not listed in the JSON receive only base OS packages.

!!! info

    - [Software Config](../Configuration/software_config.md) -- Full schema reference.
    - [Pxe Mapping File](pxe_mapping_file.md) -- PXE mapping CSV that defines functional groups.
    - [Installed Software](../SupportMatrix/installed_software.md) -- Complete software
      bill of materials.
