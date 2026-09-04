# Resync Local Repositories

## Overview

The Local Repository Resync feature updates the local RPM repositories by synchronizing them with their respective remote sources. During resynchronization, new and updated RPM packages are downloaded, repository metadata is refreshed, and only incremental changes are fetched while preserving the existing local cache.

## Prerequisites

- [Configure Repos](configure_repos.md) is complete
- repo_manager domain is initialized
- Pulp server is running

## Procedure

### Resync All RPM Repositories

```bash title="Run on: OIM host"
./omnia.sh --run repo_manager --tags execute -e "resync_repos=all"
```

### Resync a Specific RPM Repository

```bash title="Run on: OIM host"
./omnia.sh --run repo_manager --tags execute -e "resync_repos=x86_64_rhel_10.0_epel"
```

## Important Notes

- Use `all` to resync all configured RPM repositories
- Specify the exact RPM repository name for targeted resync
- Existing RPM packages remain available during sync
- Logs are created in `/opt/omnia/repo_manager/log/`

## Related Guides

- [Configure Repos](configure_repos.md) -- Main repository configuration guide
- [Adding Additional Repositories](adding_additional_repositories.md) -- Add new repositories