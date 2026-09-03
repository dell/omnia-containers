# Configuring Specific Software

## Overview

Configure specific software packages by adding entries to the software configuration file.

## Prerequisites

- [Configure Repos](configure_repos.md) is complete
- repo_manager domain is initialized

## Procedure

1. **Edit the software configuration**:

    ```bash title="Run on: OIM host"
    vi /opt/omnia/repo_manager/input/project_default/software_config.json
    ```

2. **Add the specific software entry** under the `softwares` list:

    ```json
    {
      "name": "software_name",
      "version": "1.0.0",
      "arch": ["x86_64"]
    }
    ```

## Common Software Entries

| Software | Entry | Notes |
| --- | --- | --- |
| Kubernetes | `{"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]}` | Only the specified version is supported. |
| Slurm | `{"name": "slurm_custom", "arch": ["x86_64", "aarch64"]}` | Provide the corresponding repository in `user_repo_url_<arch>` of `repo_manager_endpoint_config.yml`. |
| OpenLDAP | `{"name": "openldap", "arch": ["x86_64"]}` | |
| OpenMPI | `{"name": "openmpi", "version": "5.0.8", "arch": ["x86_64"]}` | If you change the version, update `openmpi.json` in the config directory as well. |
| UCX | `{"name": "ucx", "version": "1.19.0", "arch": ["x86_64"]}` | |
| Dell CSI PowerScale | `{"name": "csi_driver_powerscale", "version": "v2.17.0", "arch": ["x86_64"]}` | |

3. **Re-run the repo_manager domain**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run repo_manager --tags execute
    ```

## Related Guides

- [Configure Repos](configure_repos.md) -- Main repository configuration guide
- [Adding Additional Packages](adding_additional_packages.md) -- Add new packages