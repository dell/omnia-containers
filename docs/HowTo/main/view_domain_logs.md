# View Domain Logs

## Overview

Domain logs provide detailed information about domain execution, errors, and system state. Use omnia-cli to browse and tail domain logs for troubleshooting and monitoring.

## Prerequisites

- [Setup the OIM](setup_oim.md) is complete
- omnia-cli is installed
- Domains have been executed at least once

## Procedure

1. **View logs for a specific domain**:

    ```bash title="Run on: OIM host"
    omnia-cli logs repo_manager
    ```

2. **Tail logs in real-time**:

    ```bash title="Run on: OIM host"
    omnia-cli logs repo_manager --tail
    ```

3. **View logs for a specific project**:

    ```bash title="Run on: OIM host"
    omnia-cli logs repo_manager --project prod
    ```

4. **View recent logs**:

    ```bash title="Run on: OIM host"
    omnia-cli logs repo_manager --recent
    ```

## Log Locations

Domain logs are stored in standardized locations:

| Domain | Log Location |
|--------|-------------|
| repo_manager | `/opt/omnia/repo_manager/log/<project>/` |
| image_build_manager | `/opt/omnia/image_build_manager/log/<project>/` |
| discovery | `/opt/omnia/discovery/log/<project>/` |
| orchestrator | `/opt/omnia/orchestrator/log/<project>/` |
| telemetry | `/opt/omnia/telemetry/log/<project>/` |
| build_stream | `/opt/omnia/build_stream/log/<project>/` |
| utils | `/opt/omnia/utils/log/<project>/` |

## Log File Types

### Standard Logs

Each domain generates a standard log file:
```
/opt/omnia/<domain>/log/<project>/standard.log
```

Contains:
- Overall domain execution status
- Task execution order
- Error messages and warnings
- Execution timestamps

### Package-Specific Logs (repo_manager)

For repo_manager, each package download has its own log:
```
/opt/omnia/repo_manager/log/<os>/<version>/<arch>/<sw_name>/logs/
```

### Ansible Logs

Ansible playbook logs are stored in:
```
/var/log/omnia/<domain>/<domain>.log
```

## Log Analysis

### Common Log Patterns

**Successful execution:**
```
TASK [domain : Execute main workflow] ***
ok: [localhost]
```

**Validation failure:**
```
TASK [domain : Validate configuration] ***
fatal: [localhost]: FAILED! => {"msg": "Configuration validation failed"}
```

**Missing dependency:**
```
TASK [domain : Install dependencies] ***
fatal: [localhost]: FAILED! => {"msg": "Package not found"}
```

**Network connectivity issue:**
```
TASK [domain : Download from remote] ***
fatal: [localhost]: FAILED! => {"msg": "Connection timeout"}
```

## Manual Log Access

You can also access logs directly:

```bash title="Run on: OIM host"
# View standard log
cat /opt/omnia/repo_manager/log/project_default/standard.log

# View Ansible log
cat /var/log/omnia/repo_manager/repo_manager.log

# Tail log in real-time
tail -f /opt/omnia/repo_manager/log/project_default/standard.log

# Search for errors
grep -i error /opt/omnia/repo_manager/log/project_default/standard.log
```

## Log Rotation

Logs are automatically rotated based on size and age. Configure log rotation in `/etc/logrotate.d/omnia` if needed.

## Troubleshooting

- **No logs found**: Ensure the domain has been executed at least once. Check that log directories exist.
- **Permission denied**: Ensure the command is run with appropriate privileges to read log files.
- **Logs are empty**: Check that the domain execution completed successfully. Review the Ansible log for errors.

## Next Steps

- [Check Domain Status](check_domain_status.md) -- Monitor domain health
- [Edit Credentials](edit_credentials.md) -- Manage domain credentials