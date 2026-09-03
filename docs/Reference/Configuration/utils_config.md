# utils Config Reference

The `utils_config.yml` file configures utility tasks for backup, installation, and node preparation.

## Location

```
/opt/omnia/input/project_default/utils_config.yml
```

## Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `utility_type` | string | Yes | - | Utility type (backup, install, prepare) |
| `target_nodes` | list | No | - | Target nodes for utility |
| `backup_location` | string | No | - | Backup location |
| `os_image_path` | string | No | - | OS image path |

## Usage Example

```yaml title="File: /opt/omnia/input/project_default/utils_config.yml"
utility_type: backup
target_nodes:
  - slurm-control-node
  - slurm-node1
backup_location: /opt/omnia/backups
```

## Related Configuration

- [omnia_env.md](omnia_env.md)
- [Domain Contract](../domain_contracts/utils_contract.md)



