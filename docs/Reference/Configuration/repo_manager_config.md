# repo_manager Config Reference

The `repo_manager_config.yml` file configures repository mirroring and synchronization.

## Location

```
/opt/omnia/repo_manager/input/project_default/repo_manager_config.yml
```

## Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `repo_type` | string | Yes | - | Repository type (local, remote) |
| `repo_url` | string | Yes | - | Repository URL |
| `repo_ssl_verify` | boolean | No | true | SSL verification for HTTPS repos |
| `sync_enabled` | boolean | No | true | Enable repository synchronization |
| `sync_schedule` | string | No | - | Sync schedule (cron format) |

## Usage Example

```yaml title="File: /opt/omnia/repo_manager/input/project_default/repo_manager_config.yml"
repo_type: local
repo_url: https://repo.example.com
repo_ssl_verify: true
sync_enabled: true
sync_schedule: "0 2 * * *"
```

## Related Configuration

- [omnia_env.md](omnia_env.md)
- [Domain Contract](../domain_contracts/repo_manager_contract.md)





