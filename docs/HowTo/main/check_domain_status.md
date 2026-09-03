# Check Domain Status

## Overview

The omnia-cli tool provides status and diagnostics information for all domains. Use it to check domain health, view configuration, and monitor system state. This tool is automatically installed during the setup process.

## Prerequisites

- [Setup the OIM](setup_oim.md) is complete
- omnia-cli is installed (automatically installed during setup)

## Procedure

1. **Check status of all domains**:

    ```bash title="Run on: OIM host"
    omnia-cli status
    ```

    This displays status for all domains:
    - repo_manager
    - image_build_manager
    - discovery
    - orchestrator
    - telemetry
    - build_stream
    - utils

2. **Check status of a specific domain**:

    ```bash title="Run on: OIM host"
    omnia-cli repo-manager
    ```

3. **Check status for a specific project**:

    ```bash title="Run on: OIM host"
    omnia-cli status --project prod
    ```

4. **Check version information**:

    ```bash title="Run on: OIM host"
    omnia-cli version
    ```

5. **Get help**:

    ```bash title="Run on: OIM host"
    omnia-cli help
    ```

## Status Information

The status command provides:

- **Domain health**: Whether each domain is operational
- **Configuration status**: Input file validation
- **Service status**: Running services for each domain
- **Last execution**: Timestamp of last domain run
- **Project information**: Active project and configuration

## Domain-Specific Status

### Repository Manager

```bash
omnia-cli repo-manager
```

Shows:
- Pulp server status
- Repository synchronization status
- Catalog information
- Storage usage

### Image Build Manager

```bash
omnia-cli image-build
```

Shows:
- MinIO S3 storage status
- Container registry status
- Image build history
- Storage usage

### Discovery

```bash
omnia-cli discovery
```

Shows:
- Node inventory status
- Mapping file status
- OME connection status

### Orchestrator

```bash
omnia-cli orchestrator
```

Shows:
- Slurm cluster status
- Kubernetes cluster status
- Service status
- Network configuration

### Telemetry

```bash
omnia-cli telemetry
```

Shows:
- Telemetry service status
- Data collection status
- Storage usage

## Multi-Project Support

Omnia supports multiple projects for different environments:

```bash title="Run on: OIM host"
# Check status for development project
omnia-cli status --project dev

# Check status for production project
omnia-cli status --project prod

# Set project via environment variable
OMNIA_PROJECT_NAME=staging omnia-cli status
```

Each project has its own `input/` and `output/` directories under each domain.

## Troubleshooting

- **omnia-cli command not found**: Ensure setup was completed with omnia-cli installed. Run `./omnia.sh -s` if needed.
- **Status shows domain as unhealthy**: Check domain logs and verify configuration files.
- **Permission denied**: Ensure the command is run with appropriate privileges.

## Next Steps

- [View Domain Logs](view_domain_logs.md) -- Troubleshoot domain issues
- [Edit Credentials](edit_credentials.md) -- Manage domain credentials