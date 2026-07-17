# OpenCHAMI Upgrade/Rollback Issues

Issues related to OpenCHAMI services during Omnia upgrade and rollback operations, including certificate renewal gate failures and cloud-init/BSS update failures.

## Upgrade or Rollback Fails at the Cloud-Init/BSS Verification Gate

???+ note "Symptom"

    - `upgrade/upgrade.yml` or `rollback/rollback.yml` fails during the `renew_certificates.yml` step with the error: `Certificate recovery gate FAILED. Services still unreachable after acme-deploy restart.`
    - `ochami bss service status` or `ochami cloud-init service status` returns `connection refused` or a non-zero exit code
    - Critical OpenCHAMI services (for example, `haproxy`, `coresmd`, `cloud-init-server`) are inactive or in a failed state after certificate renewal

??? note "Cause"

    - OpenCHAMI services have not fully stabilized following the certificate update and container restart
    - HAProxy is using a stale backend or DNS cache, or an outdated TLS certificate
    - The `coresmd` service (v2.1) or the `coresmd-coredhcp`/`coresmd-coredns` services (v2.2) did not restart after HAProxy

??? note "Resolution"

    Perform the following commands on the OIM node to verify and recover the services:

    1. Identify services that are not running:

    ```bash title="Run on: OIM host"
    systemctl list-dependencies openchami.target --plain | while read svc; do
      echo "$svc: $(systemctl is-active $svc)"
    done
    ```

    2. Verify BSS and cloud-init service status:

    ```bash title="Run on: OIM host"
    ochami bss service status
    ochami cloud-init service status
    ```

    3. Reset failed services and restart the OpenCHAMI target:

    ```bash title="Run on: OIM host"
    systemctl reset-failed
    systemctl restart openchami.target
    sleep 30
    ```

    4. If cloud-init or BSS remains unreachable, refresh HAProxy and the certificate:

    ```bash title="Run on: OIM host"
    systemctl restart acme-deploy.service
    sleep 10
    systemctl stop haproxy.service
    systemctl start haproxy.service
    sleep 10
    ```

    5. Verify that all OpenCHAMI services are operational:

    ```bash title="Run on: OIM host"
    systemctl list-dependencies openchami.target
    ```

    6. Re-run the upgrade or rollback playbook:

    ```bash title="Run on: OIM host"
    # For upgrade
    cd /omnia/upgrade
    ansible-playbook upgrade.yml

    # For rollback
    cd /omnia/rollback
    ansible-playbook rollback.yml
    ```

## Cloud-Init/BSS Updates Fail During Upgrade or Rollback

???+ note "Symptom"

    - The OpenCHAMI `update_cloud_init_bss` step (executed as part of `upgrade/upgrade.yml` or `rollback/rollback.yml`) fails with the error: `OpenCHAMI services are unreachable after certificate renewal and HAProxy restart.`
    - `ochami cloud-init service status` or `ochami bss service status` fails before the BSS or cloud-init updates are applied

??? note "Cause"

    - OpenCHAMI services are not yet reachable when the step begins
    - HAProxy or `cloud-init-server` has not completed startup following the certificate renewal or container restart

??? note "Resolution"

    1. Verify OpenCHAMI service health on the OIM:

    ```bash title="Run on: OIM host"
    ochami cloud-init service status
    ochami bss service status
    systemctl status haproxy.service
    podman logs cloud-init-server
    ```

    2. Recover the services using the procedure in [Upgrade or Rollback Fails at the Cloud-Init/BSS Verification Gate](#upgrade-or-rollback-fails-at-the-cloud-initbss-verification-gate).

    3. Re-run the failed playbook:

    ```bash title="Run on: OIM host"
    # For upgrade
    cd /omnia/upgrade
    ansible-playbook upgrade.yml

    # For rollback
    cd /omnia/rollback
    ansible-playbook rollback.yml
    ```

!!! info

    - [OpenCHAMI Issues](openchami.md) — General OpenCHAMI troubleshooting.
    - [Upgrade Omnia](../Operations/upgrade_omnia.md) — Upgrade procedure.
    - [Rollback Omnia](../Operations/rollback_omnia.md) — Rollback procedure.
