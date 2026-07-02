
# security_config.yml Reference

File path: `/opt/omnia/input/project_default/security_config.yml`

This file configures centralized authentication services for the
cluster.

## Security Configuration Parameters

--8<-- "html/security_config.html"

## Usage example

```yaml title="File: /opt/omnia/input/project_default/security_config.yml"
---
ldap_connection_type: "TLS"
```

!!! info

    - [Playbook Reference](../Playbooks/playbook_reference.md) -- The `auth.yml`
      playbook that deploys authentication services.
    - [Ports](../ClusterRequirements/ports.md) -- Ports required by LDAP.
