
# Setup OpenLDAP as Proxy


Configure OpenLDAP on the `omnia_auth` container as a proxy to an external
LDAP server, allowing your cluster to authenticate against an existing
corporate directory without migrating users.

## Overview


In many enterprise environments, a central LDAP directory (Active Directory,
OpenLDAP, 389 Directory Server) already exists. Rather than duplicating users,
Omnia can configure OpenLDAP in proxy mode to:

- Forward authentication requests to the external LDAP server.
- Cache user and group data locally for improved performance.
- Provide a consistent LDAP interface to cluster nodes.
- Maintain cluster operation even if the external LDAP is temporarily
  unreachable (via caching).


## Prerequisites


- The [Prepare Oim](../Setup/prepare_oim.md) procedure is complete (`omnia_auth`
  container is running).
- You have the external LDAP server's connection details:

  - Server URI (e.g., `ldaps://ldap.corp.example.com:636`)
  - Base DN (e.g., `dc=corp,dc=example,dc=com`)
  - Bind DN and password for a read-only service account
  - CA certificate if using LDAPS

- Network connectivity from the OIM to the external LDAP server.


## Procedure


1. **Enter the omnia_core container**:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```


2. **Configure proxy LDAP parameters** in `omnia_config.yml`:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/omnia_config.yml
   ```


   ```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
   ---
   auth_type: "openldap_proxy"
   external_ldap_uri: "ldaps://ldap.corp.example.com:636"
   external_ldap_base_dn: "dc=corp,dc=example,dc=com"
   external_ldap_bind_dn: "cn=omnia-readonly,ou=ServiceAccounts,dc=corp,dc=example,dc=com"
   external_ldap_bind_password: ""  # Set via credentials utility
   external_ldap_user_search_base: "ou=People,dc=corp,dc=example,dc=com"
   external_ldap_group_search_base: "ou=Groups,dc=corp,dc=example,dc=com"
   external_ldap_tls_ca_cert: "/etc/ssl/certs/corp-ca.pem"
   ```


3. **(If using LDAPS) Copy the CA certificate** to the omnia_auth container:

   ```bash title="Run on: OIM host"
   podman cp /path/to/corp-ca.pem omnia_auth:/etc/ssl/certs/corp-ca.pem
   ```


4. **Run the auth.yml playbook**:

   ```bash title="Run on: omnia_core container"
   cd /omnia
   ansible-playbook auth.yml --ask-vault-pass
   ```


   The playbook will:

   - Configure OpenLDAP's `slapd-ldap` backend for proxy pass-through.
   - Set up SSSD on cluster nodes to use the local proxy.
   - Configure TLS certificates if using LDAPS.
   - Enable caching for offline resilience.

5. **(Alternative) Manual proxy configuration** inside the `omnia_auth`
   container:

   ```bash title="Run on: OIM host"
   podman exec -it omnia_auth bash
   ```


   ```bash title="Run on: omnia_auth container"
   cat <<'EOF' >> /etc/openldap/slapd.d/cn=config/olcDatabase={2}ldap.ldif
   dn: olcDatabase={2}ldap
   objectClass: olcDatabaseConfig
   objectClass: olcLDAPConfig
   olcDatabase: {2}ldap
   olcSuffix: dc=corp,dc=example,dc=com
   olcDbURI: ldaps://ldap.corp.example.com:636
   olcDbRebindAsUser: TRUE
   EOF
   ```



## Verification


1. **Test proxy connectivity** to the external LDAP:

   ```bash title="Run on: omnia_auth container"
   ldapsearch -x -H ldaps://ldap.corp.example.com:636 \
     -D "cn=omnia-readonly,ou=ServiceAccounts,dc=corp,dc=example,dc=com" \
     -W -b "ou=People,dc=corp,dc=example,dc=com" "(uid=*)" dn | head -20
   ```


2. **Test local proxy** from the omnia_core container:

   ```bash title="Run on: omnia_core container"
   ldapsearch -x -H ldap://omnia_auth -b "dc=corp,dc=example,dc=com" "(uid=someuser)"
   ```


3. **Verify user resolution** on a compute node:

   ```bash title="Run on: compute node"
   getent passwd someuser
   id someuser
   ```


4. **Test SSH login** with a corporate LDAP user:

   ```bash title="Run on: any node"
   ssh someuser@<compute-node-ip>
   ```



## Next Steps


- [Replicate Ldap](replicate_ldap.md) -- Set up replication for the proxy.
- [Setup Slurm](../Slurm/setup_slurm.md) -- Slurm will authenticate users via the
  LDAP proxy.


## Troubleshooting


**Proxy returns "connection refused"**
   Verify the external LDAP server is reachable:

   ```bash title="Run on: OIM host"
   openssl s_client -connect ldap.corp.example.com:636
   ```


**Certificate verification failed**
   Ensure the CA certificate is correct and accessible:

   ```bash title="Run on: omnia_auth container"
   openssl verify -CAfile /etc/ssl/certs/corp-ca.pem /etc/ssl/certs/corp-ca.pem
   ```


**Users not found via proxy**
   Check the search base DN matches the external LDAP tree structure:

   ```bash title="Run on: omnia_auth container"
   ldapsearch -x -H ldaps://ldap.corp.example.com:636 \
     -D "<bind-dn>" -W -b "<base-dn>" "(objectClass=*)" dn | head
   ```


**SSSD cache stale data**
   Clear and restart:

   ```bash title="Run on: compute node"
   sss_cache -E
   systemctl restart sssd
   ```
