# Adding Additional Packages

## Overview

Add additional software packages to your local repositories by updating the software configuration and re-running the repo_manager domain.

## Prerequisites

- [Configure Repos](configure_repos.md) is complete
- repo_manager domain is initialized

## Procedure

1. **Edit the software configuration**:

    ```bash title="Run on: OIM host"
    vi /opt/omnia/repo_manager/input/project_default/software_config.json
    ```

2. **Add the new software entry** to the `softwares` list:

    ```json
    {
      "name": "additional_software",
      "version": "1.0.0",
      "arch": ["x86_64"]
    }
    ```

3. **Re-run the repo_manager domain**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run repo_manager --tags execute
    ```

    The domain will download and synchronize the new packages to the Pulp server.

## Verification

Check that the new packages were successfully synchronized:

```bash title="Run on: OIM host"
pulp rpm distribution list
```

## Troubleshooting

- **Package not found**: Verify the package exists in the configured repository
- **Download fails**: Check network connectivity and repository accessibility
- **Version mismatch**: Ensure the specified version is available in the repository

## Related Guides

- [Configure Repos](configure_repos.md) -- Main repository configuration guide
- [Adding Additional Repositories](adding_additional_repositories.md) -- Add new repositories