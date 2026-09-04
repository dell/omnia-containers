# Repository Manager Input/Output Contract

## Input Contract

### Input Files

| File | Location | Required | Description |
|------|----------|----------|-------------|
| `repo_manager_config.yml` | `/opt/omnia/repo_manager/input/project_default/` | Yes | Repository configuration |
| `omnia_config.yml` | `/opt/omnia/repo_manager/input/project_default/` | Yes | Omnia cluster configuration |
| `network_spec.yml` | `/opt/omnia/repo_manager/input/project_default/` | Yes | Network configuration |

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `repo_type` | string | Yes | - | Repository type (local, remote) |
| `repo_url` | string | Yes | - | Repository URL |
| `repo_ssl_verify` | boolean | No | true | SSL verification for HTTPS repos |
| `sync_enabled` | boolean | No | true | Enable repository synchronization |

## Output Contract

### Output Files

| File | Location | Description |
|------|----------|-------------|
| `repo_sync_status.yml` | `/opt/omnia/repo_manager/output/` | Repository synchronization status |
| `repo_inventory.yml` | `/opt/omnia/repo_manager/output/` | Repository package inventory |

### Output Artifacts

- Synchronized package repositories in Pulp
- Repository sync logs
- Package inventory manifest

## Execution Flow

1. **Validate Configuration**: Check repository configuration
2. **Deploy Pulp**: Deploy Pulp repository service
3. **Sync Repositories**: Synchronize packages from remote to local
4. **Generate Inventory**: Create package inventory manifest

## Related Documentation

- [Domain Overview](../../HowTo/repo_manager/index.md)
- [Configuration Reference](../../Reference/Configuration/repo_manager_config.md)







