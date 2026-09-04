# Deploy OpenLDAP

Deploy the internal OpenLDAP authentication server on the OIM using the orchestrator domain. This guide covers input configuration, deployment, and verification.

## Overview

Omnia deploys an internal OpenLDAP server as a containerized service on the OIM host. The server provides centralized user authentication for all cluster nodes. During provisioning, each node is automatically configured with SSSD to authenticate users against this LDAP server.

OpenLDAP has **independent lifecycle management** within the orchestrator domain with dedicated precheck, prepare, deploy, cleanup, upgrade, and rollback playbooks.

**Components deployed:**

- **OpenLDAP container** -- OpenLDAP directory service running on the OIM (ports 389 and 636)
- **TLS certificates** -- Auto-generated self-signed certificates for secure LDAP connections
- **SSSD** -- Configured on each cluster node during provisioning for LDAP client authentication

## Prerequisites

- The [Setup the OIM](../main/setup_oim.md) procedure is complete (main domain setup is complete)
- The [Initialize Domains](../main/initialize_domains.md) procedure is complete (orchestrator domain is initialized)
- The [Deploy OpenCHAMI](deploy_openchami.md) procedure is complete (OpenCHAMI containers are running)

### Input Contract

The orchestrator domain requires the following inputs for OpenLDAP deployment:

| Input | Location | Purpose |
|-------|----------|---------|
| `orchestrator_config.yml` | `/opt/omnia/orchestrator/input/<project>/orchestrator_config.yml` | Main orchestrator configuration with LDAP settings |
| `omnia_config_credentials.yml` | `/opt/omnia/orchestrator/input/<project>/omnia_config_credentials.yml` | Vault-encrypted LDAP credentials |

**Required Files:**
- `orchestrator_config.yml` - Always required
- `omnia_config_credentials.yml` - Auto-created if missing (with user-prompted LDAP credentials)

**Input Sources:**
- **Administrator** - Provides `orchestrator_config.yml` with LDAP configuration
- **Credential utility** - Auto-creates `omnia_config_credentials.yml` with user-prompted LDAP credentials
- **Domain initialization** - Stages input files from samples directory

## Procedure

1. **Initialize the orchestrator domain**:

    ```bash title="Run on: OIM host"
    ./omnia.sh -i orchestrator
    ```

    This stages input files and installs dependencies.

2. **Configure the orchestrator settings**:

    ```bash title="Run on: OIM host"
    vi /opt/omnia/orchestrator/input/project_default/orchestrator_config.yml
    ```

    Configure the following parameters:

    ```yaml title="File: orchestrator_config.yml"
    # LDAP configuration
    ldap_enabled: true
    ldap_domain_name: "omnia.test"
    ldap_admin_dn: "cn=admin,dc=omnia,dc=test"
    ldap_connection_type: "TLS"
    ```

    | Parameter | Description |
    |-----------|-------------|
    | `ldap_enabled` | Enable OpenLDAP deployment |
    | `ldap_domain_name` | LDAP domain name (e.g., omnia.test) |
    | `ldap_admin_dn` | LDAP admin distinguished name |
    | `ldap_connection_type` | Connection security: `TLS` (port 389) or `SSL` (port 636) |

3. **Run the OpenLDAP deployment**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run orchestrator --tags deploy_openldap
    ```

    This performs the following:
    - Validates LDAP prerequisites
    - Generates SSHA password hashes for the OpenLDAP database
    - Creates the `slapd.conf` configuration with the domain name and admin credentials
    - Generates the `bootstrap.ldif` file for initial directory setup
    - Creates self-signed TLS certificates for secure LDAP connections
    - Deploys the OpenLDAP container via Podman Quadlet (systemd)
    - Validates OpenLDAP container health

## Verification

1. **Verify the OpenLDAP container**:

    ```bash title="Run on: OIM host"
    podman ps --filter name=openldap
    ```

    Expected output:

    ```text title="Expected output"
    CONTAINER ID  IMAGE             COMMAND  CREATED      STATUS      PORTS                                       NAMES
    abc123def456  openldap:latest           2 hours ago  Up 2 hours  0.0.0.0:389->389/tcp, 0.0.0.0:636->636/tcp  openldap
    ```

2. **Verify LDAP ports are listening**:

    ```bash title="Run on: OIM host"
    ss -tlnp | grep -E '389|636'
    ```

3. **Test LDAP connectivity**:

    ```bash title="Run on: OIM host"
    ldapsearch -x -H ldap://<oim_admin_ip>:389 -b "dc=omnia,dc=test" -D "cn=admin,dc=omnia,dc=test" -W
    ```

    Replace `<oim_admin_ip>` with the OIM admin IP, and update the domain components (`dc=omnia,dc=test`) to match your domain name.

## Output Contract

After successful execution, the orchestrator domain produces the following output contract for OpenLDAP:

| Output | Location | Purpose |
|--------|----------|---------|
| OpenLDAP container | Podman on OIM | Running OpenLDAP directory service |
| TLS certificates | `/opt/omnia/orchestrator/output/<project>/orchestrator/` | Self-signed certificates for secure LDAP connections |
| LDAP configuration | `/opt/omnia/orchestrator/output/<project>/orchestrator/` | LDAP directory configuration |

This contract is consumed by:
- **Provisioning** - For SSSD configuration on cluster nodes
- **Cluster workflows** - For ongoing authentication operations

## Next Steps

- [Provision Nodes](provision_nodes.md) -- Provision cluster nodes with LDAP authentication

## Troubleshooting

**OpenLDAP container fails to start**

Check container logs for errors:

```bash title="Run on: OIM host"
podman logs openldap
podman images | grep openldap
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

If the ports are not listed, manually add them:

```bash title="Run on: OIM host"
firewall-cmd --permanent --add-port=389/tcp --add-port=636/tcp
firewall-cmd --reload
```



















