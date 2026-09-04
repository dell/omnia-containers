# Run Domains

## Overview

Domain execution runs the Ansible playbooks for specific domains using the omnia.sh CLI. Each domain supports standardized execution tags for different phases of the workflow.

## Prerequisites

- [Setup the OIM](setup_oim.md) is complete
- [Initialize Domains](initialize_domains.md) is complete
- Domain input files are configured in `/opt/omnia/<domain>/input/<project>/`

## Procedure

1. **Run a domain with default tags**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run repo_manager
    ```

2. **Run a domain with specific tags**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run repo_manager --tags validate
    ```

3. **Run multiple tags**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run repo_manager --tags prepare,execute
    ```

4. **Run with extra variables**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run repo_manager --tags execute -e "resync_repos=all"
    ```

## Standard Execution Tags

All domain playbooks support these common tags:

| Tag | Description | Credentials Required |
|-----|-------------|---------------------|
| `precheck` | Environment and connectivity checks | No |
| `validate` | Schema and runtime validation | No |
| `prepare` | Deploy prerequisites (containers, services) | Yes |
| `execute` | Main domain workflow | Yes |
| `cleanup` | Stop services and remove artifacts | Optional |

## Domain-Specific Examples

### Repository Manager

```bash title="Run on: OIM host"
# Validate configuration
./omnia.sh --run repo_manager --tags validate

# Deploy Pulp infrastructure
./omnia.sh --run repo_manager --tags prepare

# Synchronize repositories
./omnia.sh --run repo_manager --tags execute

# Resync all repositories
./omnia.sh --run repo_manager --tags execute -e "resync_repos=all"
```

### Image Build Manager

```bash title="Run on: OIM host"
# Validate configuration
./omnia.sh --run image_build_manager --tags validate

# Build OS images
./omnia.sh --run image_build_manager --tags build

# Build specific architecture
./omnia.sh --run image_build_manager --tags x86_64
```

### Discovery

```bash title="Run on: OIM host"
# Validate configuration
./omnia.sh --run discovery --tags validate

# Generate mapping files
./omnia.sh --run discovery --tags execute
```

### Orchestrator

```bash title="Run on: OIM host"
# Validate configuration
./omnia.sh --run orchestrator --tags validate

# Deploy Slurm
./omnia.sh --run orchestrator --tags deploy_slurm

# Deploy Kubernetes
./omnia.sh --run orchestrator --tags deploy_kubernetes
```

### Telemetry

```bash title="Run on: OIM host"
# Validate configuration
./omnia.sh --run telemetry --tags validate

# Deploy telemetry services
./omnia.sh --run telemetry --tags execute
```

## Execution Order

Standard execution order for tags:
```
precheck -> validate -> prepare -> execute -> cleanup
```

When multiple tags are specified, the playbook defines the execution order, not the order written after `--tags`.

## Verification

After domain execution:

1. **Check domain status**:
    ```bash
    omnia-cli status
    ```

2. **View domain logs**:
    ```bash
    omnia-cli logs repo_manager
    ```

3. **Check output files**:
    ```bash
    ls -la /opt/omnia/<domain>/output/<project>/
    ```

## Troubleshooting

- **Domain fails with validation error**: Check input files in `/opt/omnia/<domain>/input/<project>/` and run with `--tags validate` to diagnose.
- **Domain fails during prepare**: Check that prerequisites (containers, services) are available and credentials are configured.
- **Domain fails during execute**: Check domain-specific logs and verify that all dependencies are met.
- **Permission denied**: Ensure the script is run with appropriate privileges.

## Next Steps

- [Check Domain Status](check_domain_status.md) -- Monitor domain health
- [View Domain Logs](view_domain_logs.md) -- Troubleshoot domain issues