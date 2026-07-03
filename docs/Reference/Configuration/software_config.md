
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

--8<-- "html/software_config.html"

## Usage example
See [Software Config Json](../SampleFiles/software_config_json.md) for complete annotated
examples covering Slurm-only, Slurm + K8s, and K8s-only scenarios.

```json title="File: /opt/omnia/input/project_default/software_config.json"
{
    "cluster_os_type": "rhel",
    "cluster_os_version": "10.0",
    "repo_config": "partial",
    "softwares": [
        {"name": "default_packages", "arch": ["x86_64","aarch64"]},
        {"name": "admin_debug_packages", "arch": ["x86_64","aarch64"]},
        {"name": "openldap", "arch": ["x86_64","aarch64"]},
        {"name": "service_k8s","version": "1.35.1", "arch": ["x86_64"]},
        {"name": "slurm_custom", "arch": ["x86_64","aarch64"]},
        {"name": "csi_driver_powerscale", "version":"v2.17.0", "arch": ["x86_64"]},
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


!!! note

    - The `functional_group_name` must exactly match the value in the
      `FUNCTIONAL_GROUP_NAME` column of the PXE mapping CSV.

!!! info

    - [Software Config Json](../SampleFiles/software_config_json.md) -- Complete sample
      files for different scenarios.
    - [PXE Mapping File](../SampleFiles/pxe_mapping_file.md) -- PXE mapping CSV that
      defines functional groups.
    - [Local Repo Config](local_repo_config.md) -- Repository sources for these packages.
