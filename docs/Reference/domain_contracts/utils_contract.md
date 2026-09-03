# Utils Input/Output Contract

## Input Contract

### Input Files

|| File | Location | Required | Description |
||------|----------|----------|-------------|
|| `omnia_config.yml` | `/opt/omnia/orchestrator/input/project_default/` | Yes | Omnia cluster configuration |

### Input Parameters

|| Parameter | Type | Required | Default | Description |
||-----------|------|----------|---------|-------------|
|| `utility_type` | string | Yes | - | Utility type (backup, install, prepare) |
|| `target_nodes` | list | No | - | Target nodes for utility |

## Output Contract

### Output Files

|| File | Location | Description |
||------|----------|-------------|
|| `utility_status.yml` | `/opt/omnia/utils/output/` | Utility execution status |
|| `backup_archive.tar.gz` | `/opt/omnia/utils/output/` | Configuration backup archive |

### Output Artifacts

- Slurm configuration backups
- OS installation scripts
- aarch64 node preparation artifacts
- Utility execution logs

## Execution Flow

1. **Validate Configuration**: Check utility configuration
2. **Prepare Environment**: Prepare utility execution environment
3. **Execute Utility**: Execute utility task
4. **Generate Output**: Generate utility output artifacts
5. **Verify Results**: Verify utility execution results

## Related Documentation

- [Domain Overview](../../HowTo/utils/index.md)
- [Configuration Reference](../../Reference/Configuration/utils_config.md)


