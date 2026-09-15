# Configure OpenLDAP as a Proxy Server

Configure the internal OpenLDAP server deployed by Omnia to act as a
proxy, using an external LDAP server as the backend database for user
authentication.

## Overview

Omnia allows the internal OpenLDAP server to be configured as a proxy,
where it utilizes external LDAP servers as a backend database to store
user data and acts as an authentication entity to allow or deny access
to the cluster. The OpenLDAP client on each node is configured through
the proxy server, which means there is no direct communication between
the OpenLDAP client and the external LDAP server.

!!! note
    If the OpenLDAP server is set up as a proxy, the user database is
    not replicated onto the internal server. All user management must
    be done on the external LDAP server.

## Prerequisites

- The internal OpenLDAP server is deployed on the OIM (see
  [Set Up OpenLDAP](setup_openldap.md)).
- An external LDAP server is running and reachable from the OIM.
- Admin credentials for both the internal and external LDAP servers.

## Procedure

1. **Locate the slapd.conf file** in the omnia_core container at
   `/opt/omnia/auth/slapd.conf`.

2. **Replace the slapd.conf contents** with the proxy configuration
   shown below. Update the placeholder values with your environment
   details:

    ```text title="File: /opt/omnia/auth/slapd.conf (RHEL)"
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
    suffix          "dc=phantom,dc=test"
    rootdn          cn=admin,dc=phantom,dc=test
    rootpw          <password>

    uri             "ldap://10.5.0.104:389/dc=phantom,dc=test"
    suffixmassage   "dc=phantom,dc=test" "dc=perf,dc=test"
    idassert-bind
     bindmethod=simple
     binddn="cn=admin,dc=perf,dc=test"
     credentials="<password>"
     flags=override
     mode=none

    TLSCACertificateFile    /etc/openldap/certs/ldapserver.crt
    TLSCertificateFile      /etc/openldap/certs/ldapserver.crt
    TLSCertificateKeyFile   /etc/openldap/certs/ldapserver.key
    ```

3. **Update the parameter values** in the configuration file as
   described below:

    | Parameter | Description |
    |---|---|
    | `database` | Database type used in the `slapd.conf` file that captures the details of the external LDAP server. For example, `meta` |
    | `suffix` | Domain name of the internal OpenLDAP user, used to refine the user search while authenticating. For example, `"dc=omnia,dc=test"` |
    | `rootdn` | Admin or root username of the internal OpenLDAP server set up by Omnia. For example, `cn=admin,dc=omnia,dc=test` |
    | `rootpw` | Admin password for the internal OpenLDAP server |
    | `uri` | IP of the external LDAP server with port and domain in `"ldap://<IP>:<port>/<suffix>"` format. For example, `"ldap://10.5.0.104:389/dc=omnia,dc=test"` |
    | `suffixmassage` | Dynamically maps LDAP client information from the internal server to the external server. Format: `suffixmassage <suffix1> <suffix2>` where `<suffix1>` is the internal server suffix (base DN) and `<suffix2>` is the external server suffix (base DN) |
    | `binddn` | Admin username and domain of the external LDAP server |
    | `credentials` | Admin password for the external LDAP server |
    | `TLSCACertificateFile` | Path to the TLS CA certificate. Omnia creates this at `/etc/openldap/certs/ldapserver.crt` |
    | `TLSCertificateFile` | Path to the TLS certificate. Omnia creates this at `/etc/openldap/certs/ldapserver.crt` |
    | `TLSCertificateKeyFile` | Path to the certificate key file. Omnia creates this at `/etc/openldap/certs/ldapserver.key` |

    !!! note
        The values for `suffix` and `rootdn` parameters in the
        `slapd.conf` file must be the same as those provided during the
        `get_config_credentials.yml` step.

4. **Restart the omnia_auth container** to apply the new configuration:

    ```bash title="Run on: OIM host"
    podman restart omnia_auth
    ```

Once these configurations are applied, the internal OpenLDAP server
routes all authentication requests to the external LDAP server. The
internal server does not store any user data and no users can be
created or modified from it.

### Configure Multiple External LDAP Servers

Multiple external LDAP servers can be configured on the proxy server.
The OpenLDAP proxy allows users from multiple external LDAP servers to
authenticate onto the cluster. Add multiple `uri` and `idassert-bind`
blocks in the `slapd.conf` file:

```text title="File: /opt/omnia/auth/slapd.conf (multiple servers)"
uri "ldap://10.5.0.104:389/dc=omnia1,dc=test"
idassert-bind
 bindmethod=simple
 binddn="cn=admin,dc=omnia,dc=test"
 credentials="<password>"
 flags=override
 mode=none

uri "ldap://10.5.0.105:389/dc=omnia2,dc=test"
idassert-bind
 bindmethod=simple
 binddn="cn=admin,dc=omnia,dc=test"
 credentials="<password>"
 flags=override
 mode=none
```

After adding the new server blocks, restart the `omnia_auth` container:

```bash title="Run on: OIM host"
podman restart omnia_auth
```

## Verification

Test the proxy by searching the LDAP directory:

```bash title="Run on: omnia_auth container"
ldapsearch -x -H ldap://localhost:389 -b "<internal_suffix>" -D "cn=<admin_username>,<internal_suffix>" -W
```

Replace `<internal_suffix>` with your internal domain (e.g.,
`dc=omnia,dc=test`) and `<admin_username>` with your admin username.
You should see entries from the external LDAP server in the results.

## Next Steps

- [Set Up OpenLDAP](setup_openldap.md) -- Configure OpenLDAP for cluster authentication.
- [Deploy External LDAP](deploy_external_ldap.md) -- Deploy an external LDAP server for centralized authentication.

## Troubleshooting

**Proxy returns empty search results**

Verify that the `uri` in `slapd.conf` points to the correct external
LDAP server IP and port. Test connectivity from the OIM host:

```bash title="Run on: omnia_auth container"
ldapsearch -x -H ldap://<external_ldap_ip>:<port> -b "<external_suffix>" -D "cn=<external_admin>,<external_suffix>" -W
```

**omnia_auth container fails after slapd.conf update**

Check the container logs for configuration errors:

```bash title="Run on: OIM host"
podman logs omnia_auth
```

Common causes: syntax errors in `slapd.conf`, incorrect module paths,
or mismatched `suffix`/`rootdn` values.
