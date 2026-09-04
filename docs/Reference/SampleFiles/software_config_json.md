
# software_config.json Sample Files

This page provides complete, annotated `software_config.json` examples for common deployment scenarios. Copy the scenario that best matches your
deployment and modify as needed.

## x86_64 - Slurm + Kubernetes

This example demonstrates a single-architecture full deployment of Slurm(slurm_custom) and Kubernetes(service_k8s) supporting only x86_64 nodes.

```json title="x86_64_slurm_k8s_config.json"
{
    "cluster_os_type": "rhel",
    "cluster_os_version": "10.0",
    "repo_config": "partial",
    "softwares": [
        {"name": "default_packages", "arch": ["x86_64"]},
        {"name": "admin_debug_packages", "arch": ["x86_64"]},
        {"name": "openldap", "arch": ["x86_64"]},
        {"name": "slurm_custom", "arch": ["x86_64"]},
        {"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]},
        {"name": "ucx", "version": "1.19.0", "arch": ["x86_64"]},
        {"name": "openmpi", "version": "5.0.8", "arch": ["x86_64"]},
        {"name": "csi_driver_powerscale", "version":"v2.16.0", "arch": ["x86_64"]},
        {"name": "ldms", "arch": ["x86_64"]},
        {"name": "additional_packages", "arch": ["x86_64"]}
    ],
    "slurm_custom": [
        {"name": "slurm_control_node"},
        {"name": "slurm_node"},
        {"name": "login_node"},
        {"name": "login_compiler_node"}
    ],
    "service_k8s": [
        {"name": "service_kube_control_plane_first"},
        {"name": "service_kube_control_plane"},
        {"name": "service_kube_node"}
    ],
     "additional_packages":[
        {"name": "service_kube_control_plane_first"},
        {"name": "service_kube_control_plane"},
        {"name": "service_kube_node"},
        {"name": "slurm_control_node"},
        {"name": "slurm_node"},
        {"name": "login_node"},
        {"name": "login_compiler_node"},
        {"name": "os"}
    ]
}
```
## Multi-Arch - Slurm + Kubernetes

This example demonstrates a multi-architecture deployment supporting both x86_64 and aarch64 nodes.
```json title="x86_64_aarch64_slurm_k8s_config.json"
{
    "cluster_os_type": "rhel",
    "cluster_os_version": "10.0",
    "repo_config": "partial",
    "softwares": [
        {"name": "default_packages", "arch": ["x86_64","aarch64"]},
        {"name": "admin_debug_packages", "arch": ["x86_64","aarch64"]},
        {"name": "openldap", "arch": ["x86_64","aarch64"]},
        {"name": "slurm_custom", "arch": ["x86_64","aarch64"]},
        {"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]},
        {"name": "ucx", "version": "1.19.0", "arch": ["x86_64","aarch64"]},
        {"name": "openmpi", "version": "5.0.8", "arch": ["x86_64","aarch64"]},
        {"name": "csi_driver_powerscale", "version":"v2.16.0", "arch": ["x86_64"]},
        {"name": "ldms", "arch": ["x86_64","aarch64"]},
        {"name": "additional_packages", "arch": ["x86_64","aarch64"]}
    ],
    "slurm_custom": [
        {"name": "slurm_control_node"},
        {"name": "slurm_node"},
        {"name": "login_node"},
        {"name": "login_compiler_node"}
    ],
    "service_k8s": [
        {"name": "service_kube_control_plane_first"},
        {"name": "service_kube_control_plane"},
        {"name": "service_kube_node"}
    ],
     "additional_packages":[
        {"name": "service_kube_control_plane_first"},
        {"name": "service_kube_control_plane"},
        {"name": "service_kube_node"},
        {"name": "slurm_control_node"},
        {"name": "slurm_node"},
        {"name": "login_node"},
        {"name": "login_compiler_node"},
        {"name": "os"}
    ]
}
```

## x86_64 - Slurm
Deploys a traditional HPC cluster with Slurm scheduling, LDAP, openmpi and ucx. No Kubernetes.

```json title="x86_64_slurm_config.json"
{
    "cluster_os_type": "rhel",
    "cluster_os_version": "10.0",
    "repo_config": "partial",
    "softwares": [
        {"name": "default_packages", "arch": ["x86_64"]},
        {"name": "admin_debug_packages", "arch": ["x86_64"]},
        {"name": "openldap", "arch": ["x86_64"]},
        {"name": "slurm_custom", "arch": ["x86_64"]},
        {"name": "ucx", "version": "1.19.0", "arch": ["x86_64"]},
        {"name": "openmpi", "version": "5.0.8", "arch": ["x86_64"]},
    ],
    "slurm_custom": [
        {"name": "slurm_control_node"},
        {"name": "slurm_node"},
        {"name": "login_node"},
        {"name": "login_compiler_node"}
    ]
}
```

## x86_64 - Kubernetes + Telemetry
Deploys a Kubernetes cluster with the full telemetry pipeline for
infrastructure monitoring without a job scheduler.

```json title="x86_64_k8s_telemetry_config.json"
{
    "cluster_os_type": "rhel",
    "cluster_os_version": "10.0",
    "repo_config": "partial",
    "softwares": [
        {"name": "default_packages", "arch": ["x86_64"]},
        {"name": "admin_debug_packages", "arch": ["x86_64"]},
        {"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]},
        {"name": "csi_driver_powerscale", "version":"v2.16.0", "arch": ["x86_64"]},
        {"name": "ldms", "arch": ["x86_64"]},
        {"name": "additional_packages", "arch": ["x86_64"]}
    ],
    "service_k8s": [
        {"name": "service_kube_control_plane_first"},
        {"name": "service_kube_control_plane"},
        {"name": "service_kube_node"}
    ],
     "additional_packages":[
        {"name": "service_kube_control_plane_first"},
        {"name": "service_kube_control_plane"},
        {"name": "service_kube_node"},
        {"name": "os"}
    ]
}
```

!!! note

    - Every `functional_group_name` must match an entry in the PXE mapping
      CSV (see [Pxe Mapping File](pxe_mapping_file.md)).
    - Kubernetes(service_k8s) cluster only supports x86_64 architecture.
    - Groups not listed in the JSON receive only base OS packages.

!!! info

    - [Software Config](../Configuration/software_config.md) -- Full parameter reference.
    - [PXE Mapping File](pxe_mapping_file.md) -- PXE mapping CSV that defines functional groups.


















