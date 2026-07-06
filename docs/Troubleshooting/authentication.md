# Authentication Issues

Issues related to LDAP authentication, user login, OpenLDAP service, and TLS certificate errors.

## LDAP user import fails due to whitespace in LDIF file

???+ note "Symptom"

    LDAP user import fails with syntax or formatting errors when processing the LDIF file.

??? note "Cause"

    The LDIF file contains trailing whitespace or improperly formatted entries that are rejected by the LDAP server.

??? note "Resolution"

    1. Open the LDIF file and verify there is no trailing whitespace at the end of lines.
    2. Ensure each entry is separated by exactly one blank line.
    3. Re-import the corrected LDIF file:

        ```bash title="Run on: auth server"
        ldapadd -x -D "cn=admin,dc=example,dc=com" -W -f users.ldif
        ```

## OpenLDAP login fails: stale SSH authorized key

???+ note "Symptom"

    A user can authenticate via LDAP (`ldapsearch` succeeds) but SSH login fails with `Permission denied (publickey)`.

??? note "Cause"

    The SSH public key stored in the user's LDAP entry does not match the current private key on the client, or the `sshPublicKey` attribute is empty or contains an outdated key.

??? note "Resolution"

    1. Verify the key stored in LDAP:

        ```bash title="Run on: auth server"
        ldapsearch -x -D "cn=admin,dc=example,dc=com" -W \
          -b "uid=<username>,ou=People,dc=example,dc=com" sshPublicKey
        ```

    2. Generate a new SSH key pair on the client if needed:

        ```bash title="Run on: client"
        ssh-keygen -t ed25519 -C "<username>@cluster"
        ```

    3. Update the LDAP entry with the correct public key:

        ```bash title="Run on: auth server"
        ldapmodify -x -D "cn=admin,dc=example,dc=com" -W <<EOF
        dn: uid=<username>,ou=People,dc=example,dc=com
        changetype: modify
        replace: sshPublicKey
        sshPublicKey: <paste_public_key_here>
        EOF
        ```

    4. Clear the SSSD cache and retry:

        ```bash title="Run on: compute node"
        sss_cache -E
        systemctl restart sssd
        ```

## User login fails on cluster nodes

???+ note "Symptom"

    Users cannot log in to Slurm compute nodes or login nodes via SSH. Login attempts fail with `Permission denied, please try again.` even though the user exists in LDAP and can authenticate on the auth server directly.

??? note "Cause"

    - The LDAP client (`sssd` or `nslcd`) is not running on the target node.
    - The LDAP client is configured with the wrong server URI or search base.
    - NSS (Name Service Switch) is not configured to use LDAP.
    - The user's home directory does not exist on the target node.

??? note "Resolution"

    1. Check SSSD status on the target node:

        ```bash title="Run on: compute node"
        systemctl status sssd
        ```

        If not running:

        ```bash title="Run on: compute node"
        systemctl start sssd
        ```

    2. Verify SSSD configuration:

        ```bash title="Run on: compute node"
        cat /etc/sssd/sssd.conf | grep -E 'ldap_uri|ldap_search_base'
        ```

    3. Test user lookup via NSS:

        ```bash title="Run on: compute node"
        getent passwd <username>
        ```

        If the user does not appear, SSSD or NSS is misconfigured.

    4. Check if the home directory exists:

        ```bash title="Run on: compute node"
        ls -la /home/<username>
        ```

        If it does not exist, enable automatic home directory creation:

        ```bash title="Run on: compute node"
        authconfig --enablemkhomedir --update
        ```

    5. Clear the SSSD cache and restart:

        ```bash title="Run on: compute node"
        sss_cache -E
        systemctl restart sssd
        ```

## Certificate errors

???+ note "Symptom"

    LDAP or other services fail with TLS certificate errors:

    ```text title="Expected output"
    TLS: peer cert untrusted or revoked
    SSL routines:ssl3_get_server_certificate:certificate verify failed
    ```

??? note "Cause"

    - The CA certificate used by step-ca is not installed on the client node.
    - The service certificate has expired.
    - The certificate's Subject Alternative Name (SAN) does not match the hostname or IP being used to connect.

??? note "Resolution"

    1. Check the certificate expiry:

        ```bash title="Run on: auth server"
        openssl x509 -in /etc/step/certs/server.crt -noout -dates
        step certificate inspect /etc/step/certs/server.crt --short
        ```

    2. If expired, renew the certificate:

        ```bash title="Run on: auth server"
        step ca renew /etc/step/certs/server.crt /etc/step/certs/server.key
        ```

    3. Verify the CA certificate is installed on client nodes:

        ```bash title="Run on: compute node"
        ls /etc/pki/ca-trust/source/anchors/
        ```

        If the CA cert is missing, copy it and update the trust store:

        ```bash title="Run on: OIM host"
        scp /etc/step/certs/root_ca.crt <client_node>:/etc/pki/ca-trust/source/anchors/
        ssh <client_node> update-ca-trust
        ```

    4. Verify the SAN matches the connection target:

        ```bash title="Run on: auth server"
        openssl x509 -in /etc/step/certs/server.crt -noout -ext subjectAltName
        ```

        If the SAN does not include the correct hostname or IP, reissue the certificate:

        ```bash title="Run on: auth server"
        step ca certificate <hostname> /etc/step/certs/server.crt \
          /etc/step/certs/server.key --san <hostname> --san <ip_address>
        ```

    5. Restart services after updating certificates:

        ```bash title="Run on: compute node"
        systemctl restart sssd
        ```

!!! info

    - [Deploy External LDAP](../HowTo/Authentication/deploy_external_ldap.md) -- External LDAP deployment guide.
