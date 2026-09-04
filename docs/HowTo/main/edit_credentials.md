# Edit Credentials

## Overview

Domain credentials are stored in Ansible Vault encrypted files. Use omnia-cli to securely edit and manage domain credentials without exposing them in plain text.

## Prerequisites

- [Setup the OIM](setup_oim.md) is complete
- omnia-cli is installed
- Domain has been initialized at least once

## Procedure

1. **Edit credentials for a specific domain**:

    ```bash title="Run on: OIM host"
    omnia-cli vault edit repo_manager
    ```

    This opens the encrypted credentials file in your default editor (vi, nano, etc.).

2. **Save and exit** the editor after making changes.

3. **Verify the changes** by running the domain with validation:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run repo_manager --tags validate
    ```

## Credential File Locations

Encrypted credential files are stored in:

```
/opt/omnia/<domain>/input/<project>/repo_manager_config_credentials.yml
/opt/omnia/<domain>/input/<project>/.repo_manager_config_credentials_key
```

## Supported Domains

The following domains support credential editing:

| Domain | Credential File |
|--------|----------------|
| repo_manager | `repo_manager_config_credentials.yml` |
| image_build_manager | `image_build_manager_config_credentials.yml` |
| orchestrator | `orchestrator_config_credentials.yml` |
| telemetry | `telemetry_config_credentials.yml` |

## Common Credential Types

### Repository Manager

```yaml
pulp_admin_password: your_password
registry_credentials:
  - registry: registry.example.com
    username: your_username
    password: your_password
subscription_credentials:
  username: your_subscription_username
  password: your_subscription_password
```

### Image Build Manager

```yaml
s3_access_key: your_access_key
s3_secret_key: your_secret_key
registry_credentials:
  - registry: registry.example.com
    username: your_username
    password: your_password
```

### Orchestrator

```yaml
ldap_admin_password: your_ldap_password
ldap_bind_dn: cn=admin,dc=example,dc=com
```

### Telemetry

```yaml
influxdb_password: your_influxdb_password
grafana_admin_password: your_grafana_password
```

## Security Best Practices

1. **Use strong passwords**: Minimum 12 characters with mixed case, numbers, and symbols
2. **Rotate credentials regularly**: Update credentials periodically
3. **Limit access**: Only authorized personnel should have access to edit credentials
4. **Audit changes**: Keep track of when credentials are changed
5. **Backup vault key**: Keep the `.vault_key` file in a secure location

## Vault Key Management

The vault key file (`.repo_manager_config_credentials_key`) is critical for decrypting credentials:

- **Location**: `/opt/omnia/<domain>/input/<project>/.<domain>_config_credentials_key`
- **Permissions**: Root-owned, mode 0600
- **Backup**: Store a secure backup in a separate location

!!! warning

    If the vault key is lost, credentials cannot be recovered. Always maintain a secure backup.

## Troubleshooting

- **Editor not found**: Set the `EDITOR` environment variable to your preferred editor:
    ```bash
    export EDITOR=nano
    omnia-cli vault edit repo_manager
    ```

- **Vault decryption fails**: Ensure the vault key file exists and has correct permissions. Check that the credentials file hasn't been corrupted.

- **Permission denied**: Ensure the command is run with root or equivalent privileges.

- **Validation fails after editing**: Check that the credential file format is correct and all required fields are present.

## Next Steps

- [Check Domain Status](check_domain_status.md) -- Verify domain health after credential changes
- [Run Domains](run_domains.md) -- Execute domain workflows with updated credentials