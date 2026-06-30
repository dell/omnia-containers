
# Replicate LDAP


Set up LDAP replication between the primary `omnia_auth` OpenLDAP server and
a secondary replica for redundancy and fault tolerance.

## Overview


LDAP replication ensures that:

- User authentication continues if the primary LDAP server is unavailable.
- Login latency is reduced for nodes closer to the replica.
- Data consistency is maintained across all replicas.

Omnia supports **provider-consumer** (master-slave) replication using
OpenLDAP's `syncrepl` mechanism. The primary server pushes changes to the
replica, which maintains a read-only copy of the directory.


## Prerequisites


- The [Setup Openldap](setup_openldap.md) procedure is complete (primary OpenLDAP is
  running in the `omnia_auth` container).
- A secondary server (or container) is available to host the replica.
- Network connectivity between the primary and replica LDAP servers.
- The secondary server has OpenLDAP packages installed.


## Procedure


1. **Configure the primary server** (provider) for replication:

   ```bash title="Run on: OIM host"
   podman exec -it omnia_auth bash
   ```


   ```bash title="Run on: omnia_auth container (primary)"
   cat <<'EOF' > /tmp/enable_syncprov.ldif
   dn: cn=module{0},cn=config
   changetype: modify
   add: olcModuleLoad
   olcModuleLoad: syncprov

   dn: olcOverlay=syncprov,olcDatabase={1}mdb,cn=config
   changetype: add
   objectClass: olcOverlayConfig
   objectClass: olcSyncProvConfig
   olcOverlay: syncprov
   olcSyncProvCheckpoint: 50 10
   olcSyncProvSessionlog: 100
   EOF

   ldapmodify -Q -Y EXTERNAL -H ldapi:/// -f /tmp/enable_syncprov.ldif
   ```


2. **Create a replication service account** on the primary:

   ```bash title="Run on: omnia_auth container (primary)"
   cat <<'EOF' > /tmp/repl_user.ldif
   dn: cn=replicator,dc=omnia,dc=example,dc=com
   objectClass: simpleSecurityObject
   objectClass: organizationalRole
   cn: replicator
   userPassword: {SSHA}ReplicaPassword
   EOF

   ldapadd -x -D "cn=admin,dc=omnia,dc=example,dc=com" -W -f /tmp/repl_user.ldif
   ```


3. **Configure the replica** (consumer) server:

   ```bash title="Run on: replica LDAP server"
   cat <<'EOF' > /tmp/syncrepl.ldif
   dn: olcDatabase={1}mdb,cn=config
   changetype: modify
   add: olcSyncRepl
   olcSyncRepl: rid=001
     provider=ldap://<primary-oim-ip>:389
     bindmethod=simple
     binddn="cn=replicator,dc=omnia,dc=example,dc=com"
     credentials=ReplicaPassword
     searchbase="dc=omnia,dc=example,dc=com"
     scope=sub
     schemachecking=on
     type=refreshAndPersist
     retry="30 5 300 3"
     interval=00:00:05:00
   EOF

   ldapmodify -Q -Y EXTERNAL -H ldapi:/// -f /tmp/syncrepl.ldif
   ```


   Replace `<primary-oim-ip>` with the actual IP of the OIM.

4. **Configure SSSD on cluster nodes** to use both LDAP servers:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/omnia_config.yml
   ```


   ```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
   ---
   ldap_uris:
     - "ldap://<primary-oim-ip>"
     - "ldap://<replica-ip>"
   ```


5. **Re-run the auth playbook** to update SSSD configuration:

   ```bash title="Run on: omnia_core container"
   cd /omnia
   ansible-playbook auth.yml --ask-vault-pass
   ```



## Verification


1. **Verify replication status** on the replica:

   ```bash title="Run on: replica LDAP server"
   ldapsearch -x -H ldap://localhost -b "dc=omnia,dc=example,dc=com" "(uid=testuser)"
   ```


   The user created on the primary should be visible on the replica.

2. **Add a user on the primary** and verify it replicates:

   ```bash title="Run on: omnia_auth container (primary)"
   cat <<'EOF' > /tmp/new_user.ldif
   dn: uid=repltest,ou=People,dc=omnia,dc=example,dc=com
   objectClass: inetOrgPerson
   objectClass: posixAccount
   uid: repltest
   cn: Replication Test
   sn: Test
   uidNumber: 10099
   gidNumber: 10099
   homeDirectory: /home/repltest
   loginShell: /bin/bash
   EOF

   ldapadd -x -D "cn=admin,dc=omnia,dc=example,dc=com" -W -f /tmp/new_user.ldif
   ```


   Then check the replica:

   ```bash title="Run on: replica LDAP server"
   ldapsearch -x -H ldap://localhost -b "dc=omnia,dc=example,dc=com" "(uid=repltest)"
   ```


3. **Test failover** by stopping the primary and verifying authentication
   still works:

   ```bash title="Run on: OIM host"
   podman stop omnia_auth
   ```


   ```bash title="Run on: compute node"
   # SSSD should failover to the replica
   id testuser
   ssh testuser@localhost
   ```


   Remember to restart the primary:

   ```bash title="Run on: OIM host"
   podman start omnia_auth
   ```



## Next Steps


- [Deploy External Ldap](deploy_external_ldap.md) -- Deploy a fully external LDAP setup.
- [Setup Slurm](../Slurm/setup_slurm.md) -- Slurm users authenticate via the
  replicated LDAP.


## Troubleshooting


**Replica does not receive updates**
   Check the syncrepl connection from the replica logs:

   ```bash title="Run on: replica LDAP server"
   journalctl -u slapd --no-pager -n 30
   ```


**"Invalid credentials" during replication**
   Verify the replicator account password matches between the provider
   configuration and the consumer's syncrepl credentials.

**Data is stale on the replica**
   Force a full resync by removing and re-adding the syncrepl configuration:

   ```bash title="Run on: replica LDAP server"
   ldapmodify -Q -Y EXTERNAL -H ldapi:/// <<'EOF'
   dn: olcDatabase={1}mdb,cn=config
   changetype: modify
   delete: olcSyncRepl
   EOF
   ```


   Then re-apply the syncrepl configuration from step 3.

**SSSD does not failover to the replica**
   Check the SSSD configuration on the compute node:

   ```bash title="Run on: compute node"
   cat /etc/sssd/sssd.conf | grep ldap_uri
   ```


   Ensure both LDAP URIs are listed with the primary first.
