
# software_config.json Sample Files


File path: `/opt/omnia/input/project_default/software_config.json`

This page provides complete, annotated `software_config.json` examples for common deployment scenarios. Copy the scenario that best matches your
deployment and modify as needed.

## RHEL 10.0 x86_64 - Slurm + Kubernetes (full deployment)

This example demonstrates a single-architecture deployment supporting only x86_64 nodes.

```json title="Sample software_config.json"
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
## RHEL 10.0 Multi-Arch cluster

This example demonstrates a multi-architecture deployment supporting both x86_64 and aarch64 nodes.
```json
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

## Slurm-only cluster
Deploys a traditional HPC cluster with Slurm scheduling, LDAP, openmpi and ucx. No Kubernetes.

```json title="Sample software_config.json: Slurm-only cluster"
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

## Kubernetes + telemetry only (no Slurm)
Deploys a Kubernetes cluster with the full telemetry pipeline for
infrastructure monitoring without a job scheduler.

```json title="Sample software_config.json: Kubernetes + telemetry only"
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
