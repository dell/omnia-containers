
# security_config.yml

This file configures centralized authentication services for the
cluster.

## Parameter Reference

--8<-- "html/security_config.html"

## Usage example

```yaml title="File: /opt/omnia/orchestrator/input/project_default/security_config.yml"
---
ldap_connection_type: "TLS"
```

!!! info

    - [Deployment LDAP Server](../../HowTo/orchestrator/configure_authentication.md) -- Centralized authentication for your Omnia cluster.
    - [Ports](../../SecurityConfigurationGuide/network_security.md#openldap-port-requirements) -- Ports required by LDAP.



















