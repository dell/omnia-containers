# repo_manager_endpoint_config.yml

This file defines the host-facing HTTPS endpoint for the Pulp service deployed
by Repository Manager.

## Location

```text
$OMNIA_DATA_PATH/repo_manager/input/$OMNIA_PROJECT_NAME/repo_manager_endpoint_config.yml
```

## Parameters

| Parameter | Type | Required | Default or behavior |
|---|---|---|---|
| `pulp_server_port` | integer | Yes | `2225`; valid range is 1 through 65535. |
| `pulp_server_ip` | IPv4 string | No | Uses the validated `SYSTEM_ADMIN_NIC_IPV4` value when omitted. |

HTTPS is mandatory. Protocol and certificate paths are derived by Repository Manager
and are not fields in this file. Unknown fields are rejected.

## Usage example

```yaml title="File: /opt/omnia/repo_manager/input/project_default/repo_manager_endpoint_config.yml"
pulp_server_port: 2225
# pulp_server_ip: "192.0.2.10"
```

## Related configuration

- [Repository Manager configuration](repo_manager_config.md)
- [Main environment](omnia_env.md)
