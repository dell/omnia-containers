
# security_config.yml Reference


File path: `/opt/omnia/input/project_default/security_config.yml`

This file configures centralized authentication and security services for the
cluster, including LDAP, Kerberos, and FreeIPA integration.

## Authentication method


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `auth_type` | String | No | `ldap` | Authentication backend to deploy. Accepted values: `ldap` (OpenLDAP), `freeipa` (FreeIPA). Determines which subsequent parameters are required. |

## LDAP settings


These parameters apply when `auth_type` is `ldap`.

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `ldap_uri` | String | Conditional | (none) | URI of the LDAP server (e.g., `ldap://10.5.0.50` or `ldaps://ldap.hpc.example.com`). Required when `auth_type` is `ldap`. |
| `ldap_base_dn` | String | Conditional | (none) | Base Distinguished Name for LDAP queries (e.g., `dc=hpc,dc=example,dc=com`). |
| `ldap_bind_dn` | String | Conditional | (none) | Bind DN for LDAP authentication (e.g., `cn=admin,dc=hpc,dc=example,dc=com`). |
| `ldap_bind_password` | String | Conditional | (vault-managed) | Password for the bind DN. Set via `credentials_utility.yml`. |
| `ldap_user_search_base` | String | No | `ou=People,<ldap_base_dn>` | Subtree where user entries are stored. |
| `ldap_group_search_base` | String | No | `ou=Group,<ldap_base_dn>` | Subtree where group entries are stored. |
| `ldap_tls_enabled` | Boolean | No | `false` | Enable TLS encryption for LDAP connections (`ldaps://`). |
| `ldap_tls_ca_cert` | String | No | (none) | Path to the CA certificate file for TLS verification. |

## Kerberos settings


Kerberos can be enabled alongside LDAP or FreeIPA for ticket-based
authentication.

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `enable_kerberos` | Boolean | No | `false` | Enable Kerberos authentication on cluster nodes. |
| `kerberos_realm` | String | Conditional | (none) | Kerberos realm name (e.g., `HPC.EXAMPLE.COM`). Must be uppercase. Required when `enable_kerberos` is `true`. |
| `kerberos_kdc` | String | Conditional | (none) | Hostname or IP of the Key Distribution Center. |
| `kerberos_admin_server` | String | Conditional | (none) | Hostname or IP of the Kerberos admin server (kadmind). |

## FreeIPA settings


These parameters apply when `auth_type` is `freeipa`.

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `freeipa_server` | String | Conditional | (none) | Hostname or IP of the FreeIPA server. Required when `auth_type` is `freeipa`. |
| `freeipa_domain` | String | Conditional | (none) | FreeIPA domain name (e.g., `hpc.example.com`). |
| `freeipa_realm` | String | Conditional | (none) | FreeIPA Kerberos realm (e.g., `HPC.EXAMPLE.COM`). Uppercase. |
| `freeipa_admin_password` | String | Conditional | (vault-managed) | FreeIPA admin password. Set via `credentials_utility.yml`. |

## General security settings


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `enable_firewall` | Boolean | No | `true` | Configure firewalld rules on cluster nodes for required services. |
| `enable_selinux` | Boolean | No | `true` | Enforce SELinux on cluster nodes. Omnia configures necessary SELinux booleans and file contexts. |
| `ssh_key_auth_only` | Boolean | No | `false` | Disable SSH password authentication and require key-based auth only. |

## Usage example


```yaml title="File: /opt/omnia/input/project_default/security_config.yml"
auth_type: "ldap"
ldap_uri: "ldap://10.5.0.50"
ldap_base_dn: "dc=hpc,dc=example,dc=com"
ldap_bind_dn: "cn=admin,dc=hpc,dc=example,dc=com"
ldap_tls_enabled: false

enable_kerberos: false

enable_firewall: true
enable_selinux: true
ssh_key_auth_only: false
```


!!! info

    - [Playbook Reference](../Playbooks/playbook_reference.md) -- The `auth.yml`
      playbook that deploys authentication services.
    - [Ports](../../Overview/security_configuration_guide.md#openldap-port-requirements) -- Ports required by LDAP,
      Kerberos, and FreeIPA.
