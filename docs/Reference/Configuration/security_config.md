
# security_config.yml

This file configures centralized authentication services for the
cluster.

## Parameter Reference

--8<-- "html/security_config.html"

## Usage example

```yaml title="File: $OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/security_config.yml"
---
ldap_connection_type: "TLS"
```

`TLS` configures provisioned Slurm and login clients to use StartTLS on TCP
389. `SSL` configures those clients to use LDAPS on TCP 636. The OIM-hosted
`omnia_auth` Quadlet publishes both ports; this setting selects the client
connection mode.

!!! info

    - [Deploy OpenLDAP](../../HowTo/orchestrator/deploy_openldap.md) -- Deploy
      the OIM-hosted `omnia_auth` service used for centralized authentication.
    - [Ports](../../SecurityConfigurationGuide/network_security.md#openldap-port-requirements) -- Ports required by LDAP.















