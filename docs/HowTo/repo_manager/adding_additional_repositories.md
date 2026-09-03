# Adding Additional Repositories

## Overview

Add additional repositories to your local repositories by updating the endpoint configuration and re-running the repo_manager domain.

## Prerequisites

- [Configure Repos](configure_repos.md) is complete
- repo_manager domain is initialized

## Procedure

1. **Edit the endpoint configuration**:

    ```bash title="Run on: OIM host"
    vi /opt/omnia/repo_manager/input/project_default/repo_manager_endpoint_config.yml
    ```

2. **Add the new repository configuration**:

    ```yaml
    user_repo_url_x86_64:
      - "https://additional-repo.example.com/rhel/10.0/x86_64/"
    user_repo_url_aarch64:
      - "https://additional-repo.example.com/rhel/10.0/aarch64/"
    ```

3. **Update the catalog** to include packages from the new repository (if needed).

4. **Re-run the repo_manager domain**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run repo_manager --tags execute
    ```

    The domain will synchronize content from the new repository.

## Verification

Check that the new repository was successfully synchronized:

```bash title="Run on: OIM host"
pulp rpm repository list
```

## Troubleshooting

- **Repository not accessible**: Verify the repository URL is correct and accessible from the OIM
- **Authentication fails**: Ensure credentials are configured for private repositories
- **Sync fails**: Check network connectivity and repository availability

## Related Guides

- [Configure Repos](configure_repos.md) -- Main repository configuration guide
- [Adding Additional Packages](adding_additional_packages.md) -- Add new packages