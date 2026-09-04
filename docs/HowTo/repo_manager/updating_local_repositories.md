# Update Local Repositories after Modifying JSON Files

## Overview

After repo_manager domain execution is complete, any modifications to `<software_name>.json` files (e.g., `service_k8s.json`, `slurm_custom.json`, `additional_software.json`) will **not** be reflected automatically. You must re-run the domain to apply changes.

## Prerequisites

- [Configure Repos](configure_repos.md) is complete
- repo_manager domain is initialized

## Procedure

1. **Modify the JSON configuration file**:

    ```bash title="Run on: OIM host"
    vi /opt/omnia/repo_manager/input/project_default/config/<architecture>/rhel/10.0/<software_name>.json
    ```

2. **Re-run the repo_manager domain**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run repo_manager --tags execute
    ```

    The domain will process the updated JSON files and synchronize the changes to the Pulp server.

## Common JSON Files

- `service_k8s.json` - Kubernetes service packages
- `slurm_custom.json` - Slurm job scheduler packages
- `additional_software.json` - Additional custom packages
- `openmpi.json` - OpenMPI configuration
- Other software-specific JSON files

## Related Guides

- [Configure Repos](configure_repos.md) -- Main repository configuration guide
- [Configuring Specific Software](configuring_specific_software.md) -- Configure specific software packages