
# Deploy External LDAP


Deploy a standalone, external OpenLDAP server using Bitnami containers for
environments that require a dedicated authentication server separate from
the OIM.

## Overview


While Omnia includes OpenLDAP in the `omnia_auth` container on the OIM,
some deployments benefit from a dedicated LDAP server:

- Separation of concerns (authentication independent of management node).
- Dedicated resources for LDAP operations.
- Existing infrastructure integration requirements.

This guide deploys OpenLDAP using Bitnami's container image on a dedicated
server (or K8s cluster), then configures Omnia cluster nodes to authenticate
against it.


## Prerequisites


- A dedicated server or the Omnia K8s service cluster is available.
- Podman or Docker is installed on the dedicated server (or Helm for K8s).
- Network connectivity between cluster nodes and the LDAP server.
- A planned base DN, admin credentials, and organizational structure.


## Procedure


### Standalone Server Deployment (Podman)


1. **Log in to the LDAP server host**:

   ```bash title="Run on: dedicated LDAP server"
   ssh root@<ldap-server-ip>
   ```


2. **Create persistent storage directories**:

   ```bash title="Run on: dedicated LDAP server"
   mkdir -p /opt/ldap/data
   mkdir -p /opt/ldap/config
   ```


3. **Deploy the Bitnami OpenLDAP container**:

   ```bash title="Run on: dedicated LDAP server"
   podman run -d \
     --name openldap \
     --restart=always \
     -p 389:1389 \
     -p 636:1636 \
     -e LDAP_ADMIN_USERNAME=admin \
     -e LDAP_ADMIN_PASSWORD=YourAdminPassword \
     -e LDAP_ROOT=dc=omnia,dc=example,dc=com \
     -e LDAP_ADMIN_DN=cn=admin,dc=omnia,dc=example,dc=com \
     -e LDAP_CUSTOM_LDIF_DIR=/ldifs \
     -v /opt/ldap/data:/bitnami/openldap:Z \
     -v /opt/ldap/config:/ldifs:Z \
     docker.io/bitnami/openldap:latest
   ```


4. **Create initial LDIF** for organizational structure:

   ```bash title="Run on: dedicated LDAP server"
   cat <<'EOF' > /opt/ldap/config/01-org.ldif
   dn: ou=People,dc=omnia,dc=example,dc=com
   objectClass: organizationalUnit
   ou: People

   dn: ou=Groups,dc=omnia,dc=example,dc=com
   objectClass: organizationalUnit
   ou: Groups
   EOF
   ```


5. **Load the initial LDIF**:

   ```bash title="Run on: dedicated LDAP server"
   podman exec openldap ldapadd -x \
     -D "cn=admin,dc=omnia,dc=example,dc=com" \
     -w YourAdminPassword \
     -f /ldifs/01-org.ldif
   ```


6. **Add users and groups**:

   ```bash title="Run on: dedicated LDAP server"
   cat <<'EOF' > /opt/ldap/config/02-users.ldif
   dn: cn=hpcusers,ou=Groups,dc=omnia,dc=example,dc=com
   objectClass: posixGroup
   cn: hpcusers
   gidNumber: 10000

   dn: uid=hpcuser1,ou=People,dc=omnia,dc=example,dc=com
   objectClass: inetOrgPerson
   objectClass: posixAccount
   objectClass: shadowAccount
   uid: hpcuser1
   cn: HPC User 1
   sn: User1
   uidNumber: 10001
   gidNumber: 10000
   homeDirectory: /home/hpcuser1
   loginShell: /bin/bash
   EOF

   podman exec openldap ldapadd -x \
     -D "cn=admin,dc=omnia,dc=example,dc=com" \
     -w YourAdminPassword \
     -f /ldifs/02-users.ldif
   ```


   Set the user password:

   ```bash title="Run on: dedicated LDAP server"
   podman exec openldap ldappasswd -x \
     -D "cn=admin,dc=omnia,dc=example,dc=com" \
     -w YourAdminPassword \
     -S "uid=hpcuser1,ou=People,dc=omnia,dc=example,dc=com"
   ```



### Kubernetes Deployment (Helm)


7. **(Alternative) Deploy on K8s** using Helm:

   ```bash title="Run on: K8s control plane node"
   helm repo add bitnami https://charts.bitnami.com/bitnami
   helm repo update

   helm install openldap bitnami/openldap \
     --namespace auth \
     --create-namespace \
     --set adminUsername=admin \
     --set adminPassword=YourAdminPassword \
     --set root=dc=omnia,dc=example,dc=com \
     --set service.type=LoadBalancer \
     --set persistence.enabled=true \
     --set persistence.size=10Gi
   ```



### Configure Omnia Nodes


8. **Update omnia_config.yml** to point to the external LDAP:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/omnia_config.yml
   ```


   ```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
   ---
   auth_type: "external_ldap"
   external_ldap_uri: "ldap://<ldap-server-ip>:389"
   external_ldap_base_dn: "dc=omnia,dc=example,dc=com"
   external_ldap_bind_dn: "cn=admin,dc=omnia,dc=example,dc=com"
   ```


9. **Run the auth playbook** to configure SSSD on cluster nodes:

   ```bash title="Run on: omnia_core container"
   cd /omnia
   ansible-playbook auth.yml --ask-vault-pass
   ```



## Verification


1. **Verify the LDAP container is running**:

   ```bash title="Run on: dedicated LDAP server"
   podman ps --filter name=openldap
   ```


2. **Test LDAP search**:

   ```bash title="Run on: OIM host"
   ldapsearch -x -H ldap://<ldap-server-ip> \
     -b "dc=omnia,dc=example,dc=com" "(uid=hpcuser1)"
   ```


3. **Verify user resolution on cluster nodes**:

   ```bash title="Run on: compute node"
   getent passwd hpcuser1
   id hpcuser1
   ```


4. **Test SSH login**:

   ```bash title="Run on: any node"
   ssh hpcuser1@<compute-node-ip>
   ```



## Next Steps


- [Replicate Ldap](replicate_ldap.md) -- Replicate the external LDAP for redundancy.
- [Setup Openldap Proxy](setup_openldap_proxy.md) -- Proxy an existing directory through Omnia.


## Troubleshooting


**Container fails to start**
   Check container logs:

   ```bash title="Run on: dedicated LDAP server"
   podman logs openldap
   ```


**Port 389 already in use**
   Check for existing LDAP processes:

   ```bash title="Run on: dedicated LDAP server"
   ss -tlnp | grep 389
   # Kill or stop the conflicting process
   ```


**SSSD cannot connect to external LDAP**
   Verify connectivity from a cluster node:

   ```bash title="Run on: compute node"
   ldapsearch -x -H ldap://<ldap-server-ip> -b "dc=omnia,dc=example,dc=com" "(objectClass=*)" dn
   ```


**Users not visible after LDAP add**
   Clear SSSD cache on cluster nodes:

   ```bash title="Run on: omnia_core container"
   ansible all -m shell -a "sss_cache -E && systemctl restart sssd"
   ```
