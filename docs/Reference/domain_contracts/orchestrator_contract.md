# Orchestrator Input/Output Contract

## Input Contract

### Input Files

| File | Location | Required | Description |
|------|----------|----------|-------------|
| `orchestrator_config.yml` | `/opt/omnia/input/project_default/` | Yes | Provision configuration |
| `omnia_config.yml` | `/opt/omnia/input/project_default/` | Yes | Omnia cluster configuration |
| `network_spec.yml` | `/opt/omnia/input/project_default/` | Yes | Network configuration |
| `storage_config.yml` | `/opt/omnia/input/project_default/` | Yes | Storage configuration |
| `security_config.yml` | `/opt/omnia/input/project_default/` | Yes | Security configuration |

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `deploy_slurm` | boolean | No | false | Deploy Slurm job scheduler |
| `deploy_kubernetes` | boolean | No | false | Deploy Kubernetes services |
| `configure_infiniband` | boolean | No | false | Configure InfiniBand networking |
| `configure_ldap` | boolean | No | false | Configure LDAP authentication |

## Output Contract

### Output Files

| File | Location | Description |
|------|----------|-------------|
| `orchestrator_status.yml` | `/opt/omnia/orchestrator/output/` | Orchestrator deployment status |
| `slurm_config.yml` | `/opt/omnia/orchestrator/output/` | Slurm configuration |
| `kubernetes_config.yml` | `/opt/omnia/orchestrator/output/` | Kubernetes configuration |

### Output Artifacts

- Deployed Slurm cluster (if enabled)
- Deployed Kubernetes cluster (if enabled)
- Configured networking (InfiniBand, DNS)
- Configured storage (NFS, PowerScale)
- Configured authentication (LDAP)

## Execution Flow

1. **Validate Configuration**: Check Provision configuration
2. **Deploy Prerequisites**: Deploy containers and services
3. **Deploy Slurm**: Deploy Slurm job scheduler (if enabled)
4. **Deploy Kubernetes**: Deploy Kubernetes services (if enabled)
5. **Configure Networking**: Configure InfiniBand and DNS
6. **Configure Storage**: Configure NFS and PowerScale
7. **Configure Authentication**: Configure LDAP

## Related Documentation

- [Domain Overview](../../HowTo/orchestrator/index.md)
- [Configuration Reference](../../Reference/Configuration/provision_config.md)















