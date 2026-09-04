# Migration Guide

This guide helps you migrate from Omnia 2.2 to Omnia 2.3.

## Overview

Omnia 2.3 introduces a domain-based architecture that reorganizes the documentation and execution model. This guide helps you understand the changes and migrate your deployment.

## Key Changes in 2.3

### Domain-Based Architecture

Omnia 2.3 organizes functionality into domains:

- **repo_manager** - Repository management
- **image_build_manager** - Image building
- **discovery** - Node discovery
- **orchestrator** - Slurm, Kubernetes, networking, storage, authentication
- **telemetry** - Monitoring and metrics
- **build_stream** - BuildStreaM CI/CD
- **utils** - Utilities and helpers
- **cross_domain** - Cross-domain workflows

### Execution Model Changes

**2.2**: Container-based execution
```bash
podman exec -it omnia_core bash
cd /omnia/<domain>
ansible-playbook playbook.yml
```

**2.3**: Domain-based execution
```bash
./omnia.sh --run <domain> --tags <tag>
```

## Migration Steps

### Step 1: Update Configuration Files

Update your configuration files to use the new domain-based structure:

- Move global settings to `omnia.env`
- Use domain-specific config files (e.g., `repo_manager_config.yml`)
- Update configuration parameters to match new schema

### Step 2: Update Execution Commands

Replace container-based commands with domain-based commands:

**Old (2.2)**:
```bash
podman exec -it omnia_core bash
cd /omnia/repo_manager
ansible-playbook repo.yml
```

**New (2.3)**:
```bash
./omnia.sh --run repo_manager --tags execute
```

### Step 3: Update Documentation References

Update any documentation references to use the new domain-based structure:

- Update links from `HowTo/Setup/` to domain-specific paths
- Update links from `HowTo/Slurm/` to `HowTo/orchestrator/`
- Update links from `HowTo/Kubernetes/` to `HowTo/orchestrator/`

### Step 4: Verify Deployment

After migration, verify your deployment:

```bash
# Check domain status
./omnia.sh --status

# Validate configuration
./omnia.sh --validate

# Test domain execution
./omnia.sh --run <domain> --tags validate
```

## Troubleshooting

If you encounter issues during migration:

1. Check the [Domain Execution](../Overview/domain_execution.md) guide
2. Review the [Domain Contracts](../Reference/domain_contracts/repo_manager_contract.md) for your domain
3. Consult the [Troubleshooting](../Troubleshooting/index.md) section

## Related Documentation

- [Domain Execution](../Overview/domain_execution.md)
- [Domain Contracts](../Reference/domain_contracts/repo_manager_contract.md)
- [Getting Started: Full Deployment](full_deployment.md)



