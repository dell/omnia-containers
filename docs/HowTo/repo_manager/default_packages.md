# Configure Default Packages and Admin Debug Packages

## Overview

The `softwares` list in `software_config.json` supports two foundational package entries that control system packages and debugging tools.

## Default Packages

**Mandatory** - Installs essential system packages and core dependencies required for basic Omnia cluster operation. This entry **must always** be present in the `softwares` list.

### Configuration

```json
{"name": "default_packages", "arch": ["x86_64", "aarch64"]}
```

### Package List

The full list of packages included in `default_packages` is defined in the corresponding JSON files located at:
```
/opt/omnia/repo_manager/input/project_default/config/<architecture>/rhel/10.0/
```

## Admin Debug Packages

**Optional** - Installs debugging, profiling, and development tools (e.g., `gdb`, `strace`, `valgrind`, `gcc`, `perf`) on the cluster nodes.

### Configuration

To enable admin debug packages, add the following entry to the `softwares` list:

```json
{"name": "admin_debug_packages", "arch": ["x86_64", "aarch64"]}
```

### Package List

The full list of packages included in `admin_debug_packages` is defined in the corresponding JSON files located at:
```
/opt/omnia/repo_manager/input/project_default/config/<architecture>/rhel/10.0/
```

## Important Notes

- `default_packages` is mandatory and must not be removed from the `softwares` list
- Deploying `admin_debug_packages` increases the size of the local repository and requires additional disk space
- The accepted software names are taken from `/opt/omnia/repo_manager/input/project_default/config/<architecture>/<cluster_os_type>/<cluster_os_version>`

## Procedure

1. **Edit the software configuration**:

    ```bash title="Run on: OIM host"
    vi /opt/omnia/repo_manager/input/project_default/software_config.json
    ```

2. **Add the admin debug packages entry** (optional):

    ```json
    {
      "name": "admin_debug_packages",
      "arch": ["x86_64", "aarch64"]
    }
    ```

3. **Re-run the repo_manager domain**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run repo_manager --tags execute
    ```

## Related Guides

- [Configure Repos](configure_repos.md) -- Main repository configuration guide
- [Configuring Specific Software](configuring_specific_software.md) -- Configure specific software packages