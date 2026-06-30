
# Authentication Issues


Issues related to LDAP authentication, user login, the `omnia_auth`
container, and TLS certificate errors.

## LDAP bind failures


???+ note "Symptom"

    LDAP client operations fail with bind errors:

    ```text
    ldap_bind: Invalid credentials (49)
    ```


    Or Ansible playbooks fail when attempting to configure LDAP with
    authentication errors.

??? note "Cause"

    - The LDAP admin bind DN or password is incorrect.
    - The LDAP server is not running.
    - TLS certificate verification fails, preventing the secure bind.

??? note "Resolution"

    1. Verify the LDAP server is running:

       ```bash
       # If running as a container on the auth_server node
       ssh <auth_server> podman ps | grep ldap
       # or
       ssh <auth_server> systemctl status slapd
       ```


    2. Test a manual bind:

       ```bash
       ldapsearch -x -H ldap://<auth_server>:389 \
         -D "cn=admin,dc=example,dc=com" \
         -W -b "dc=example,dc=com" "(objectClass=*)"
       ```


    3. Verify credentials in the Omnia vault:

       ```bash
       ssh omnia_core
       ansible-vault view /omnia/input/credentials.yml
       ```


       Confirm the LDAP bind DN and password match what the LDAP server expects.

    4. If TLS is the issue, test without TLS first to isolate:

       ```bash
       ldapsearch -x -H ldap://<auth_server>:389 \
         -D "cn=admin,dc=example,dc=com" -W -b "dc=example,dc=com"
       ```


       Then test with TLS:

       ```bash
       ldapsearch -x -H ldaps://<auth_server>:636 \
         -D "cn=admin,dc=example,dc=com" -W -b "dc=example,dc=com"
       ```


## User login fails on cluster nodes


???+ note "Symptom"

    Users cannot log in to Slurm compute nodes or login nodes via SSH. Login
    attempts fail with:

    ```text
    Permission denied, please try again.
    ```


    Even though the user exists in LDAP and can authenticate on the auth server
    directly.

??? note "Cause"

    - The LDAP client (`sssd` or `nslcd`) is not running on the target node.
    - The LDAP client is configured with the wrong server URI or search base.
    - NSS (Name Service Switch) is not configured to use LDAP.
    - The user's home directory does not exist on the target node.

??? note "Resolution"

    1. Check SSSD status on the target node:

       ```bash
       ssh <node> systemctl status sssd
       ```


       If not running:

       ```bash
       ssh <node> systemctl start sssd
       ```


    2. Verify SSSD configuration:

       ```bash
       ssh <node> cat /etc/sssd/sssd.conf | grep -E 'ldap_uri|ldap_search_base'
       ```


    3. Test user lookup via NSS:

       ```bash
       ssh <node> getent passwd <username>
       ```


       If the user does not appear, SSSD or NSS is misconfigured.

    4. Check if the home directory exists:

       ```bash
       ssh <node> ls -la /home/<username>
       ```


       If it does not exist, enable automatic home directory creation:

       ```bash
       ssh <node> authconfig --enablemkhomedir --update
       ```


    5. Clear the SSSD cache and restart:

       ```bash
       ssh <node> sss_cache -E
       ssh <node> systemctl restart sssd
       ```


## `omnia_auth` container not starting


???+ note "Symptom"

    The `omnia_auth` container fails to start or repeatedly crashes. ``podman
    ps -a` shows it in `Exited`` state.

??? note "Cause"

    - Port conflicts (another service is using ports 389 or 636).
    - Missing or corrupt TLS certificates.
    - Insufficient permissions on data volumes.
    - The container image is missing or corrupt.

??? note "Resolution"

    1. Check container logs:

       ```bash
       podman logs omnia_auth
       ```


    2. Check for port conflicts:

       ```bash
       ss -tlnp | grep -E '389|636'
       ```


       If another service is using the ports, stop it or reconfigure:

       ```bash
       systemctl stop <conflicting_service>
       ```


    3. Verify TLS certificate files exist and are readable:

       ```bash
       ls -la /etc/omnia/certs/ldap/
       ```


    4. Verify data directory permissions:

       ```bash
       ls -la /var/lib/omnia/ldap/
       ```


    5. Re-pull the container image if it is corrupt:

       ```bash
       podman pull <registry>/omnia_auth:<tag>
       ```


    6. Re-run the authentication playbook:

       ```bash
       ssh omnia_core
       cd /omnia
       ansible-playbook playbooks/auth.yml
       ```


## Certificate errors


???+ note "Symptom"

    LDAP or other services fail with TLS certificate errors:

    ```text
    TLS: peer cert untrusted or revoked
    SSL routines:ssl3_get_server_certificate:certificate verify failed
    ```


??? note "Cause"

    - The CA certificate used by step-ca is not installed on the client node.
    - The service certificate has expired.
    - The certificate's Subject Alternative Name (SAN) does not match the
      hostname or IP being used to connect.

??? note "Resolution"

    1. Check the certificate expiry:

       ```bash
       # Using openssl
       openssl x509 -in /etc/step/certs/server.crt -noout -dates

       # Using step-cli
       step certificate inspect /etc/step/certs/server.crt --short
       ```


    2. If expired, renew the certificate:

       ```bash
       step ca renew /etc/step/certs/server.crt /etc/step/certs/server.key
       ```


    3. Verify the CA certificate is installed on client nodes:

       ```bash
       ssh <client_node> ls /etc/pki/ca-trust/source/anchors/
       ```


       If the CA cert is missing, copy it and update the trust store:

       ```bash
       scp /etc/step/certs/root_ca.crt <client_node>:/etc/pki/ca-trust/source/anchors/
       ssh <client_node> update-ca-trust
       ```


    4. Verify the SAN matches the connection target:

       ```bash
       openssl x509 -in /etc/step/certs/server.crt -noout -ext subjectAltName
       ```


       If the SAN does not include the correct hostname or IP, reissue the
       certificate:

       ```bash
       step ca certificate <hostname> /etc/step/certs/server.crt \
         /etc/step/certs/server.key --san <hostname> --san <ip_address>
       ```


    5. Restart services after updating certificates:

       ```bash
       systemctl restart sssd
       podman restart omnia_auth
       ```


!!! info

    - [Setup Openldap](../HowTo/Authentication/setup_openldap.md) -- OpenLDAP setup guide.
    - [Security Hardening](../Operations/security_hardening.md) -- TLS and LDAP hardening.
    - [Security Hardening](../Operations/security_hardening.md) -- Credential rotation procedures.
