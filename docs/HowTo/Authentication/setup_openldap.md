# Set Up OpenLDAP

Deploy the internal OpenLDAP authentication server on the OIM using
Omnia. This guide covers input configuration, deployment, verification,
and optional proxy setup for external LDAP integration.

## Overview

Omnia deploys an internal OpenLDAP server as a containerized service
(`omnia_auth`) on the OIM host. The server provides centralized user
authentication for all cluster nodes. During provisioning, each node
is automatically configured with SSSD to authenticate users against
this LDAP server.

### How It Works

1. `prepare_oim.yml` deploys the `omnia_auth` container on the OIM
   with OpenLDAP configured using the domain name, admin credentials,
   and TLS certificates.
2. `provision.yml` configures SSSD on each provisioned node to connect
   to the OpenLDAP server for user authentication.
3. Users can then log in to any cluster node using LDAP credentials.

### Components Deployed

- **omnia_auth** -- OpenLDAP container running on the OIM (ports 389
  and 636)
- **TLS certificates** -- Auto-generated self-signed certificates for
  secure LDAP connections
- **SSSD** -- Configured on each cluster node during provisioning for
  LDAP client authentication

## Prerequisites

- The OIM is prepared and the `omnia_core` container is accessible (see
  [Prepare OIM](../Setup/prepare_oim.md)).
- The domain name is configured in
  [`provision_config.yml`](../../Reference/Configuration/provision_config.md).

## Procedure

### Step 1: Enter the omnia_core Container

```bash title="Run on: OIM host"
ssh omnia_core
```

All subsequent commands run inside the `omnia_core` container unless
stated otherwise.

### Step 2: Edit Input Files

Edit the following input files in `/opt/omnia/input/project_default/`.

#### 2a. Edit software_config.json

Edit [`software_config.json`](../../Reference/Configuration/software_config.md)
and add `openldap` to the `softwares` list:

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
    The `openldap` entry in `softwares` is what triggers Omnia to deploy
    the `omnia_auth` container during `prepare_oim.yml` and configure
    SSSD on nodes during `provision.yml`.

#### 2b. Edit security_config.yml

Edit [`security_config.yml`](../../Reference/Configuration/security_config.md)
and set the LDAP connection type:

```yaml title="File: /opt/omnia/input/project_default/security_config.yml"
ldap_connection_type: "TLS"
```

| Parameter | Description |
|---|---|
| `ldap_connection_type` | Connection security type: `TLS` (port 389) or `SSL` (port 636) |

For the full parameter reference, see
[security_config.yml Reference](../../Reference/Configuration/security_config.md).

### Step 3: Set Credentials

Run the credential utility to store the OpenLDAP admin credentials.
When `openldap` is present in `software_config.json`, the credential
utility prompts for OpenLDAP-specific passwords in addition to the
standard provisioning credentials.

```bash title="Run on: omnia_core container"
cd /omnia/utils/credential_utility
ansible-playbook get_config_credentials.yml
```

You will be prompted for:

- **Provision password** -- Root password for provisioned nodes
- **OpenLDAP admin username** -- Admin bind DN username (e.g., `admin`)
- **OpenLDAP admin password** -- Password for the OpenLDAP admin account

### Step 4: Run prepare_oim.yml

Run `prepare_oim.yml` to deploy the OIM infrastructure. When OpenLDAP
is enabled in `software_config.json`, this playbook automatically:

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

### Step 5: Run provision.yml

Run `provision.yml` to provision the cluster nodes. For nodes with
OpenLDAP enabled, the playbook configures SSSD on each node to
authenticate against the internal OpenLDAP server.

```bash title="Run on: omnia_core container"
cd /omnia/provision
ansible-playbook provision.yml
```

During provisioning, Omnia configures each node with:

- **LDAP server IP** -- Set to the OIM admin IP
- **LDAP search base** -- Derived from the domain name (e.g.,
  `dc=omnia,dc=test` for domain `omnia.test`)
- **LDAP bind DN** -- Admin username and search base
  (e.g., `cn=admin,dc=omnia,dc=test`)
- **Connection type** -- TLS or SSL as configured in
  `security_config.yml`

### Step 6: PXE Boot Nodes

After `provision.yml` completes, PXE boot the cluster nodes:

**Option 1: Manual PXE Boot**

Configure each node to boot from the network via iDRAC or BIOS settings.

**Option 2: Automated PXE Boot via iDRAC**

```bash title="Run on: omnia_core container"
cd /omnia/utils
ansible-playbook set_pxe_boot.yml
```

Wait for all nodes to complete booting and cloud-init to finish.

## Verification

### 1. Verify the omnia_auth container

```bash title="Run on: OIM host"
podman ps --filter name=omnia_auth
```

Expected output:

```text title="Expected output"
CONTAINER ID  IMAGE                    COMMAND  CREATED      STATUS      PORTS                                     NAMES
abc123def456  omnia_auth:1.1                    2 hours ago  Up 2 hours  0.0.0.0:389->389/tcp, 0.0.0.0:636->636/tcp  omnia_auth
```

### 2. Verify LDAP ports are listening

```bash title="Run on: OIM host"
ss -tlnp | grep -E '389|636'
```

### 3. Test LDAP connectivity from omnia_core

```bash title="Run on: omnia_core container"
ldapsearch -x -H ldap://<oim_admin_ip>:389 -b "dc=omnia,dc=test" -D "cn=admin,dc=omnia,dc=test" -W
```

Replace `<oim_admin_ip>` with the OIM admin IP, and update the domain
components (`dc=omnia,dc=test`) to match your domain name.

### 4. Verify SSSD on cluster nodes

After PXE boot completes, verify SSSD is configured on the nodes:

```bash title="Run on: omnia_core container"
ssh <hostname> 'systemctl status sssd'
```

Replace `<hostname>` with any provisioned node hostname from the PXE
mapping file.

## Next Steps

- [Deploy External LDAP](deploy_external_ldap.md) -- Set up an external
  Bitnami OpenLDAP server for centralized authentication.
- [Configure OpenLDAP as Proxy](#configure-openldap-as-proxy) -- Configure
  the internal OpenLDAP server to proxy authentication requests to an
  external LDAP server.

## Configure OpenLDAP as Proxy

The internal OpenLDAP server can be configured as a **proxy** to use an
external LDAP server as a backend database. In this mode, OpenLDAP acts
as an authentication relay -- user data is stored on the external LDAP
server and is not replicated onto the internal server.

!!! note
    When OpenLDAP is configured as a proxy, users cannot be
    created or modified from the internal server. All user management
    must be done on the external LDAP server.

### Procedure

1. **Edit the slapd.conf file** on the OIM host:

    ```bash title="Run on: OIM host"
    vi /opt/omnia/authservice/slapd.conf
    ```

2. **Replace the contents** with the proxy configuration. Update the
   placeholder values with your external LDAP server details:

    ```text title="File: /opt/omnia/authservice/slapd.conf (RHEL)"
    include        /etc/openldap/schema/core.schema
    include        /etc/openldap/schema/cosine.schema
    include        /etc/openldap/schema/nis.schema
    include        /etc/openldap/schema/inetorgperson.schema

    pidfile         /run/openldap/slapd.pid
    argsfile        /run/openldap/slapd.args

    # Load dynamic backend modules:
    modulepath      /usr/lib64/openldap
    moduleload      back_ldap.la
    moduleload      back_meta.la

    #######################################################################
    # Meta database definitions
    #######################################################################
    database        meta
    suffix          "<internal_suffix>"
    rootdn          cn=<admin_username>,<internal_suffix>
    rootpw          <admin_password>

    uri             "ldap://<external_ldap_ip>:<port>/<external_suffix>"
    suffixmassage   "<internal_suffix>" "<external_suffix>"
    idassert-bind
     bindmethod=simple
     binddn="cn=<external_admin>,<external_suffix>"
     credentials="<external_password>"
     flags=override
     mode=none

    TLSCACertificateFile    /etc/openldap/certs/ldapserver.crt
    TLSCertificateFile      /etc/openldap/certs/ldapserver.crt
    TLSCertificateKeyFile   /etc/openldap/certs/ldapserver.key
    ```

    | Parameter | Description |
    |---|---|
    | `database` | Backend database type. Use `meta` for proxy mode |
    | `suffix` | Domain name of the internal OpenLDAP server (e.g., `"dc=omnia,dc=test"`) |
    | `rootdn` | Admin bind DN of the internal server |
    | `rootpw` | Admin password of the internal server |
    | `uri` | External LDAP server URI in `"ldap://<IP>:<port>/<suffix>"` format |
    | `suffixmassage` | Maps internal suffix to external suffix for DN translation |
    | `binddn` | Admin bind DN of the external LDAP server |
    | `credentials` | Admin password of the external LDAP server |

    !!! note
        - The `suffix` and `rootdn` values must match those provided
          during the `get_config_credentials.yml` step.
        - Multiple external LDAP servers can be configured by adding
          additional `uri` and `idassert-bind` blocks.

3. **Restart the omnia_auth container**:

    ```bash title="Run on: OIM host"
    podman restart omnia_auth
    ```

4. **Verify the proxy is working**:

    ```bash title="Run on: OIM host"
    ldapsearch -x -H ldap://localhost:389 -b "<internal_suffix>" -D "cn=<admin_username>,<internal_suffix>" -W
    ```

    You should see entries from the external LDAP server in the search
    results.

## Troubleshooting

### omnia_auth container fails to start

Check container logs and verify the image is available:

```bash title="Run on: OIM host"
podman logs omnia_auth
podman images | grep omnia_auth
```

If the image is not available, build it from the omnia-artifactory
repository:

```bash
git clone https://github.com/dell/omnia-artifactory -b omnia-container
cd omnia-artifactory
./build_images.sh auth
```

### LDAP ports 389/636 are already in use

Check which process is using the ports and stop it:

```bash title="Run on: OIM host"
ss -tlnp | grep -E '389|636'
```

### SSSD not starting on cluster nodes

Check the SSSD configuration and logs on the node:

```bash title="Run on: omnia_core container"
ssh <hostname> 'systemctl status sssd'
ssh <hostname> 'journalctl -u sssd --no-pager -n 30'
```

Common causes: incorrect domain name in `provision_config.yml`, OIM
admin IP not reachable from the node, or TLS certificate issues.

### Cannot connect to LDAP from cluster nodes

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
