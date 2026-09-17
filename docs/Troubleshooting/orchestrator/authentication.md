# Authentication issues

Omnia runs OpenLDAP in the OIM-hosted `omnia_auth` Podman container and
configures SSSD on supported Slurm and login nodes. The LDAP search base is
derived from `SYSTEM_DOMAIN_NAME`; it is not a fixed `dc=omnia,dc=local`
value.

## Establish a baseline

Check the server on the OIM:

```bash title="Run on: OIM"
source /etc/profile.d/omnia-env.sh
systemctl status omnia_auth --no-pager
podman ps -a --filter name=omnia_auth
podman logs --tail 100 omnia_auth
podman exec omnia_auth ldapsearch -x -H ldap://127.0.0.1 \
  -b '' -s base namingContexts
```

The final command mirrors Orchestrator's local container health check. It
proves that the LDAP endpoint responds inside the container; verify the
configured StartTLS or LDAPS path separately from a provisioned client.

Check a provisioned client:

```bash title="Run on: affected Slurm or login node"
systemctl status sssd --no-pager
authselect current
grep -E 'ldap_uri|ldap_search_base|ldap_id_use_start_tls|ldap_tls_cacert' \
  /etc/sssd/sssd.conf
getent passwd <ldap-user>
```

Do not check the host `slapd` service on the OIM. OpenLDAP is owned by the
`omnia_auth` Quadlet service in this release.

## `omnia_auth` is not running

???+ note "Symptom"

    `systemctl status omnia_auth` is failed or inactive, the container is
    absent, or clients cannot contact the port selected by
    `ldap_connection_type` (TCP 389 for `TLS` or TCP 636 for `SSL`).

??? note "Resolution"

    1. Inspect the service and container logs:

        ```bash title="Run on: OIM"
        systemctl status omnia_auth --no-pager
        journalctl -u omnia_auth -b -n 200 --no-pager
        podman logs --tail 200 omnia_auth
        ```

    2. Confirm that the selected catalog enables OpenLDAP and that the active
       Orchestrator credential file contains the configured OpenLDAP username
       and password. Do not print the decrypted password into a terminal log.
    3. Rerun the supported preparation and validation flows:

        === "Using omnia.sh (recommended)"

            ```bash title="Run on: OIM host"
            cd <OMNIA_SOURCE_PATH>/src/main
            ./omnia.sh --run orchestrator --tags prepare
            ./omnia.sh --run orchestrator --tags validate-deployment
            ```

        === "Using ansible-playbook"

            ```bash title="Run on: OIM host"
            source /opt/omnia/activate-omnia.sh
            cd <OMNIA_SOURCE_PATH>/src/orchestrator
            ansible-playbook playbooks/orchestrator.yml --tags prepare
            ansible-playbook playbooks/orchestrator.yml --tags validate-deployment
            ```

## LDAP user is not found on a node

???+ note "Symptom"

    `id <ldap-user>` or `getent passwd <ldap-user>` reports no entry even
    though the user exists in LDAP.

??? note "Cause"

    The user may be outside the configured search base, may lack POSIX
    attributes, or SSSD may have stale cached data or an incorrect generated
    configuration.

??? note "Resolution"

    1. Read the actual search base from the node and query that base on the
       OIM. Replace placeholders with the values from the active environment:

        ```bash title="Run on: affected node"
        grep '^ldap_search_base' /etc/sssd/sssd.conf
        getent passwd <ldap-user>
        sssctl user-show <ldap-user>
        ```

        ```bash title="Run on: OIM"
        podman exec omnia_auth ldapsearch -x -H ldap://127.0.0.1 \
          -b '<configured-search-base>' '(uid=<ldap-user>)' \
          objectClass uidNumber gidNumber homeDirectory loginShell
        ```

    2. Ensure the entry has the `posixAccount` attributes required by the
       cluster. Use the site's approved LDAP administration workflow to repair
       the entry; do not copy a fixed administrator DN from an example.
    3. If the server entry is correct, clear only SSSD's cached entry and
       restart SSSD:

        ```bash title="Run on: affected node"
        sss_cache -u <ldap-user>
        systemctl restart sssd
        getent passwd <ldap-user>
        ```

## User authentication fails on a cluster node

???+ note "Symptom"

    The LDAP identity resolves, but SSH, `su`, or PAM authentication fails.

??? note "Resolution"

    1. Verify SSSD and the active authselect profile:

        ```bash title="Run on: affected node"
        systemctl status sssd --no-pager
        authselect current
        journalctl -u sssd -b -n 200 --no-pager
        ```

    2. Confirm the node can reach the URI and port in `/etc/sssd/sssd.conf`.
       `TLS` in `security_config.yml` uses StartTLS on port 389; `SSL` uses
       LDAPS on port 636.
    3. Confirm the generated profile enables SSSD and home-directory creation:

        ```bash title="Run on: affected node"
        authselect select sssd with-mkhomedir --force
        systemctl enable --now sssd
        ```

       `authconfig` and `nslcd` are legacy mechanisms and are not used by the
       current Orchestrator templates.
    4. When generated settings are wrong, correct the Orchestrator input and
       rerun `precheck` and `provision`. Avoid maintaining a manual SSSD
       configuration that the next provisioning run will replace.

## LDAP TLS certificate error

???+ note "Symptom"

    SSSD or `ldapsearch` reports an untrusted, expired, or mismatched
    certificate.

??? note "Resolution"

    1. Inspect the certificate generated for `omnia_auth` on the OIM:

        ```bash title="Run on: OIM"
        source /etc/profile.d/omnia-env.sh
        openssl x509 -in "$OMNIA_DATA_PATH/auth/tls_certs/ldapserver.crt" \
          -noout -subject -issuer -dates -ext subjectAltName
        ```

    2. Inspect the provisioned client copy and SSSD reference:

        ```bash title="Run on: affected node"
        openssl x509 -in /etc/openldap/certs/ldapserver.crt \
          -noout -subject -issuer -dates -ext subjectAltName
        grep -E 'ldap_uri|ldap_tls_cacert|ldap_tls_reqcert' /etc/sssd/sssd.conf
        ```

    3. If the client copy differs, rerun Orchestrator provisioning so the
       generated metadata copies the current certificate and configuration.
       Do not use the obsolete `/opt/omnia/omnia/openldap/certs` path.
    4. Restart SSSD and verify identity lookup:

        ```bash title="Run on: affected node"
        systemctl restart sssd
        getent passwd <ldap-user>
        ```

## SSH reports a changed host key

This is an SSH trust failure, not an LDAP authentication failure. Confirm that
the host was intentionally reprovisioned before removing its old key:

```bash title="Run on: SSH client"
ssh-keygen -R <node-hostname-or-IP>
ssh-keyscan <node-hostname-or-IP> | ssh-keygen -lf -
```

Verify the displayed fingerprint through the site's trusted inventory before
adding it to `known_hosts`.

See [Deploy OpenLDAP](../../HowTo/orchestrator/deploy_openldap.md) for the
supported configuration and deployment workflow.
