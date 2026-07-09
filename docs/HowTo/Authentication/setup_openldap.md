# Set Up OpenLDAP

Deploy the internal OpenLDAP authentication server on the OIM using
Omnia. This guide covers input configuration, deployment, and
verification.

## Overview

Omnia deploys an internal OpenLDAP server as a containerized service
(`omnia_auth`) on the OIM host. The server provides centralized user
authentication for all cluster nodes. During provisioning, each node
is automatically configured with SSSD to authenticate users against
this LDAP server.

The `prepare_oim.yml` playbook deploys the `omnia_auth` container on
the OIM with OpenLDAP configured using the domain name, admin
credentials, and TLS certificates. When nodes are subsequently
provisioned using `provision.yml`, SSSD is configured on each node
to connect to this OpenLDAP server for user authentication.

**Components deployed:**

- **omnia_auth** -- OpenLDAP container running on the OIM (ports 389
  and 636)
- **TLS certificates** -- Auto-generated self-signed certificates for
  secure LDAP connections
- **SSSD** -- Configured on each cluster node during provisioning for
  LDAP client authentication

## Prerequisites

- The OIM is prepared and the `omnia_core` container is accessible (see
  [Prepare OIM](../Setup/prepare_oim.md)).

## Procedure

1. **Enter the omnia_core container:**

    ```bash title="Run on: OIM host"
    ssh omnia_core
    ```

    All subsequent commands run inside the `omnia_core` container.

2. **Edit software_config.json** -- Add `openldap` to the `softwares`
   list in
   [`software_config.json`](../../Reference/Configuration/software_config.md):

    ```json title="File: /opt/omnia/input/project_default/software_config.json"
    {
        "cluster_os_type": "rhel",
        "cluster_os_version": "10.0",
        "repo_config": "partial",
        "softwares": [
            {"name": "default_packages", "arch": ["x86_64"]},
            {"name": "openldap", "arch": ["x86_64"]}
        ]
    }
    ```

    !!! important
        The `openldap` entry in `softwares` is what triggers Omnia to
        deploy the `omnia_auth` container during `prepare_oim.yml` and
        configure SSSD on nodes during `provision.yml`.

3. **Edit security_config.yml** -- Set the LDAP connection type in
   [`security_config.yml`](../../Reference/Configuration/security_config.md):

    ```yaml title="File: /opt/omnia/input/project_default/security_config.yml"
    ldap_connection_type: "TLS"
    ```

    | Parameter | Description |
    |---|---|
    | `ldap_connection_type` | Connection security type: `TLS` (port 389) or `SSL` (port 636) |

    For the full parameter reference, see
    [security_config.yml Reference](../../Reference/Configuration/security_config.md).

4. **Run prepare_oim.yml** -- Deploy the OIM infrastructure. When
   OpenLDAP is enabled in `software_config.json`, this playbook
   automatically:

    - Generates SSHA password hashes for the OpenLDAP database
    - Creates the `slapd.conf` configuration with the domain name and
      admin credentials
    - Generates the `bootstrap.ldif` file for initial directory setup
    - Creates self-signed TLS certificates for secure LDAP connections
    - Deploys the `omnia_auth` container via Podman Quadlet (systemd)

    ```bash title="Run on: omnia_core container"
    cd /omnia/prepare_oim
    ansible-playbook prepare_oim.yml
    ```

## Verification

1. **Verify the omnia_auth container:**

    ```bash title="Run on: OIM host"
    podman ps --filter name=omnia_auth
    ```

    Expected output:

    ```text title="Expected output"
    CONTAINER ID  IMAGE             COMMAND  CREATED      STATUS      PORTS                                       NAMES
    abc123def456  omnia_auth:1.1             2 hours ago  Up 2 hours  0.0.0.0:389->389/tcp, 0.0.0.0:636->636/tcp  omnia_auth
    ```

2. **Verify LDAP ports are listening:**

    ```bash title="Run on: OIM host"
    ss -tlnp | grep -E '389|636'
    ```

3. **Test LDAP connectivity:**

    ```bash title="Run on: omnia_core container"
    ldapsearch -x -H ldap://<oim_admin_ip>:389 -b "dc=omnia,dc=test" -D "cn=admin,dc=omnia,dc=test" -W
    ```

    Replace `<oim_admin_ip>` with the OIM admin IP, and update the
    domain components (`dc=omnia,dc=test`) to match your domain name.

## Next Steps

- [Configure OpenLDAP as Proxy](configure_openldap_proxy.md) --
  Configure the internal OpenLDAP server to proxy authentication
  requests to an external LDAP server.
- [Deploy External LDAP](deploy_external_ldap.md) -- Set up an external
  Bitnami OpenLDAP server for centralized authentication.

## Troubleshooting

**omnia_auth container fails to start**

Check container logs for errors:

```bash title="Run on: OIM host"
podman logs omnia_auth
podman images | grep omnia_auth
```

**LDAP ports 389/636 are already in use**

Check which process is using the ports:

```bash title="Run on: OIM host"
ss -tlnp | grep -E '389|636'
```

**Cannot connect to LDAP from cluster nodes**

Verify that ports 389 and 636 are open on the OIM firewall:

```bash title="Run on: OIM host"
firewall-cmd --list-ports
```

If the ports are not listed, `prepare_oim.yml` should have opened them.
Re-run the playbook or manually add them:

```bash title="Run on: OIM host"
firewall-cmd --permanent --add-port=389/tcp --add-port=636/tcp
firewall-cmd --reload
```
