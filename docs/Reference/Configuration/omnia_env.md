# omnia.env Reference

The `omnia.env` file contains environment variables for the Omnia deployment.

## Location

```
/opt/omnia/omnia.env
```

## Environment Variables

| Variable | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `OMNIA_VERSION` | string | Yes | - | Omnia version |
| `OMNIA_BRANCH` | string | Yes | - | Omnia branch |
| `OIM_HOSTNAME` | string | Yes | - | OIM hostname |
| `OIM_IP` | string | Yes | - | OIM IP address |
| `ADMIN_PASSWORD` | string | Yes | - | Admin password |
| `TIMEZONE` | string | No | UTC | System timezone |
| `LANG` | string | No | en_US.UTF-8 | System language |

## Usage Example

```bash title="File: /opt/omnia/omnia.env"
OMNIA_VERSION=2.3.0
OMNIA_BRANCH=main
OIM_HOSTNAME=oim.example.com
OIM_IP=192.168.1.100
ADMIN_PASSWORD=your_password
TIMEZONE=UTC
LANG=en_US.UTF-8
```

## Related Configuration

- [repo_manager_config.md](repo_manager_config.md)
- [provision_config.md](provision_config.md)




