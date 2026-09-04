# Domain Execution

Omnia 2.3 uses a domain-based execution model that organizes functionality into independent domains with clear contracts and workflows.

## Overview

The domain-based architecture provides:

- **Clear separation of concerns** - Each domain has a specific responsibility
- **Independent execution** - Domains can be executed independently or together
- **Standardized contracts** - Input/output contracts define domain interfaces
- **Improved maintainability** - Easier to understand and modify individual domains

## Domain Architecture

### Domain Responsibilities

| Domain | Responsibility | Dependencies |
|--------|---------------|--------------|
| repo_manager | Repository mirroring and synchronization | None |
| image_build_manager | Image building and S3 storage | repo_manager |
| discovery | Node discovery and mapping file generation | None |
| orchestrator | Slurm, Kubernetes, networking, storage, authentication | repo_manager, image_build_manager, discovery |
| telemetry | Monitoring and metrics collection | orchestrator |
| build_stream | GitOps-based CI/CD pipelines | image_build_manager, orchestrator |
| utils | Helper utilities (backup, install, prepare) | None |
| cross_domain | Cross-domain workflows | All domains |

### Execution Flow

```
1. repo_manager: Synchronize repositories
2. image_build_manager: Build images
3. discovery: Generate mapping files
4. orchestrator: Deploy Slurm/Kubernetes
5. telemetry: Configure monitoring
6. build_stream: Execute CI/CD pipelines (optional)
7. utils: Helper utilities (independent, not in execution flow)
8. cross_domain: Configure inputs and credentials (can be run at any time)
```

## Domain Execution Commands

### Basic Execution

Execute a single domain:

```bash title="Run on: OIM host"
./omnia.sh --run <domain> --tags <tag>
```

**Example**: Execute repo_manager with execute tag
```bash
./omnia.sh --run repo_manager --tags execute
```

### Available Tags

Each domain supports the following tags:

| Tag | Description |
|-----|-------------|
| `validate` | Validate configuration only |
| `prepare` | Deploy prerequisites (containers, services) |
| `execute` | Main domain workflow |
| `cleanup` | Remove infrastructure and artifacts |

### Multi-Domain Execution

Execute multiple domains in sequence:

```bash title="Run on: OIM host"
./omnia.sh --run repo_manager,image_build_manager --tags execute
```

### Full Deployment

Execute all domains for a full deployment:

```bash title="Run on: OIM host"
./omnia.sh --run all --tags execute
```

## Domain Configuration

### Configuration Files

Each domain has its own configuration file:

| Domain | Configuration File |
|--------|-------------------|
| repo_manager | `repo_manager_config.yml` |
| image_build_manager | `image_build_manager_config.yml` |
| discovery | `discovery_config.yml` |
| orchestrator | `orchestrator_config.yml` |
| telemetry | `telemetry_config.yml` |
| build_stream | `build_stream_config.yml` |
| utils | `utils_config.yml` |

### Global Configuration

Global settings are in `omnia.env`:

```bash title="File: /opt/omnia/omnia.env"
OMNIA_VERSION=2.3.0
OMNIA_BRANCH=main
OIM_HOSTNAME=oim.example.com
OIM_IP=192.168.1.100
ADMIN_PASSWORD=your_password
```

## Domain Contracts

Each domain has input/output contracts that define:

- **Input files** - Required configuration files
- **Input parameters** - Configuration parameters
- **Output files** - Generated output files
- **Output artifacts** - Produced artifacts
- **Execution flow** - Step-by-step execution

See [Domain Contracts](../Reference/domain_contracts/repo_manager_contract.md) for detailed contract documentation.

## Verification

### Check Domain Status

```bash title="Run on: OIM host"
./omnia.sh --status
```

### Validate Configuration

```bash title="Run on: OIM host"
./omnia.sh --validate
```

### Verify Domain Output

```bash title="Run on: OIM host"
cat /opt/omnia/<domain>/output/project_default/<output_file>.yml
```

## Troubleshooting

### Common Issues

**Domain fails to execute**

- Check domain configuration file
- Verify prerequisites are met
- Check domain logs: `./omnia.sh --logs <domain>`

**Configuration validation fails**

- Check configuration file syntax
- Verify required parameters are set
- Check configuration file location

**Domain dependencies not met**

- Execute prerequisite domains first
- Check dependency status: `./omnia.sh --status`
- Review domain contracts for dependencies

### Domain-Specific Troubleshooting

See [Troubleshooting](../Troubleshooting/index.md) for domain-specific troubleshooting guides.

## Related Documentation

- [Migration Guide](../GetStarted/migration_guide.md)
- [Domain Contracts](../Reference/domain_contracts/repo_manager_contract.md)
- [Getting Started: Full Deployment](../GetStarted/full_deployment.md)




