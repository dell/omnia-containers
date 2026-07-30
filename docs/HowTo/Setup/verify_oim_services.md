
# Verify OIM Services


Perform a comprehensive health check of all Omnia Infrastructure Manager (OIM)
services after running `prepare_oim.yml`. This guide walks through every
service in the `omnia.target` dependency tree.

## Overview


After the OIM is prepared, the following services should be running as systemd-managed Podman containers:

- **omnia_core** -- Ansible control plane
- **OpenCHAMI stack** -- SMD, BSS, CoreDHCP, TFTP, DNS, and related services
- **Pulp** -- RPM repository management
- **MinIO** -- S3-compatible object storage
- **Registry** -- Local container image registry
- **Omnia Auth** *(optional)* -- Centralized authentication

This guide helps you verify each service is healthy and troubleshoot any that
are not.


## Prerequisites
- The [Prepare OIM](prepare_oim.md) procedure has been completed successfully.
- You have `root` or `sudo` access to the OIM host.

## Procedure


1. **Check the omnia_core service**:

    ```bash title="Run on: OIM host"
    systemctl status omnia_core.service
    ```

    Expected: `Active: active (running)`

2. **List the complete omnia.target dependency tree**:

    ```bash title="Run on: OIM host"
    systemctl list-dependencies omnia.target
    ```

    Expected output:

    ```text title="Expected output on: OIM host"
    omnia.target
    ● ├─minio.service
    ● ├─omnia_auth.service
    ● ├─omnia_build_stream.service
    ● ├─omnia_core.service
    ● ├─omnia_postgres.service
    ● ├─playbook_watcher.service
    ● ├─pulp.service
    ● ├─registry.service
    ● ├─network-online.target
    ● │ └─NetworkManager-wait-online.service
    ● └─openchami.target
    ●   ├─acme-deploy.service
    ●   ├─acme-register.service
    ●   ├─bss-init.service
    ●   ├─bss.service
    ●   ├─cloud-init-server.service
    ●   ├─coresmd.service
    ●   ├─haproxy.service
    ●   ├─hydra-gen-jwks.service
    ●   ├─hydra-migrate.service
    ●   ├─hydra.service
    ●   ├─opaal-idp.service
    ●   ├─opaal.service
    ●   ├─openchami-cert-trust.service
    ●   ├─postgres.service
    ●   ├─smd.service
    ●   └─step-ca.service
    ```

    The following service status indicators are displayed on the live cluster:

    - A **green circle** indicates the service is running.
    - A **grey circle** indicates the service is not running.
    - A **circle with a cross** indicates the service failed to start.

    !!! note

        The `omnia_auth.service` runs only when OpenLDAP is specified in `/opt/omnia/input/project_default/software_config.json`.

    !!! note

        The `omnia_build_stream.service`, `omnia_postgres.service`, and `playbook_watcher.service` run only when BuildStreaM is enabled in `/opt/omnia/input/project_default/build_stream_config.yml`.

3. **Check each top-level service individually**:

    ```bash title="Run on: OIM host"
    for svc in minio omnia_auth omnia_build_stream omnia_core omnia_postgres playbook_watcher pulp registry; do
      echo "=== $svc ==="
      systemctl is-active ${svc}.service
    done
    ```

4. **Check OpenCHAMI sub-services**:

    ```bash title="Run on: OIM host"
    for svc in acme-deploy acme-register bss-init bss cloud-init-server coresmd haproxy hydra-gen-jwks hydra-migrate hydra opaal-idp opaal openchami-cert-trust postgres smd step-ca; do
      echo "=== $svc ==="
      systemctl is-active ${svc}.service
    done
    ```

5. **Verify running Podman containers**:

    ```bash title="Run on: OIM host"
    podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    ```

6. **Test the OpenCHAMI CLI**:

    ```bash title="Run on: omnia_core container"
    ochami --help
    ```

    The help menu lists the supported commands for node discovery, provisioning, and service management:

    - `bss` -- Communicate with the Boot Script Service (BSS).
    - `cloud-init` -- Interact with the cloud-init service.
    - `completion` -- Generate the autocompletion script for the specified shell.
    - `config` -- View or modify configuration options.
    - `discover` -- Perform static or dynamic discovery of nodes.
    - `pcs` -- Interact with the Power Control Service (PCS).
    - `smd` -- Communicate with the State Management Database (SMD).
    - `version` -- Display detailed version information and exit.
    - `help` -- Display help for a specific command.

    For more details about a specific command, run:

    ```bash title="Run on: omnia_core container"
    ochami [command] --help
    ```

    Useful `ochami` commands:

    ```bash title="Run on: omnia_core container"
    # Check BSS service status
    ochami bss service status

    # Check SMD service status
    ochami smd service status
    ```

7. **Test MinIO / S3 access**:

    ```bash title="Run on: omnia_core container"
    s3cmd ls
    ```

8. **Test Pulp accessibility**:

    ```bash title="Run on: OIM host"
    curl -s http://localhost:8080/pulp/api/v3/status/ | python3 -m json.tool
    ```

    Expected: a JSON response with `"online_workers"` and `"versions"`.

9. **Verify PowerScale S3 connection** (if PowerScale is configured as S3 storage):

    ```bash title="Run on: omnia_core container"
    # Verify the S3 buckets are created
    s3cmd ls

    # List the images present in a specific S3 bucket
    s3cmd ls s3://<bucket-name>/
    ```

    See [Configure PowerScale as S3 storage](prepare_oim.md#configure-powerscale-as-s3-storage) for setup instructions.


## Verification

All services should report `active (running)`. Use this summary check:

```bash title="Run on: OIM host"
systemctl is-active omnia.target
```


Expected output: `active`

If any service is `inactive` or `failed`, note which one and refer to the
Troubleshooting section below.

**Quick health summary script**:

```bash title="Run on: OIM host"
echo "=== Omnia Service Health ==="
echo "omnia.target:        $(systemctl is-active omnia.target)"
echo "omnia_core:          $(systemctl is-active omnia_core.service)"
echo "openchami.target:    $(systemctl is-active openchami.target)"
echo "pulp:                $(systemctl is-active pulp.service)"
echo "minio:               $(systemctl is-active minio.service)"
echo "registry:            $(systemctl is-active registry.service)"
echo "omnia_auth:          $(systemctl is-active omnia_auth.service)"
echo "omnia_build_stream:  $(systemctl is-active omnia_build_stream.service)"
echo "omnia_postgres:      $(systemctl is-active omnia_postgres.service)"
echo "playbook_watcher:    $(systemctl is-active playbook_watcher.service)"
```

!!! note

    `omnia_auth`, `omnia_build_stream`, `omnia_postgres`, and `playbook_watcher` report `inactive` when OpenLDAP or BuildStreaM are not enabled -- this does not indicate a failure.

## Next Steps

- [Create Local Repos](create_local_repos.md) -- Sync RPM repositories via Pulp.
- [Build Cluster Images](build_cluster_images.md) -- Build OS boot images.
- [Discover Nodes](discover_nodes.md) -- Discover and provision bare-metal servers.


## Troubleshooting


**A service shows "inactive (dead)"**
   Restart the specific service:

   ```bash title="Run on: OIM host"
   systemctl restart <service-name>.service
   journalctl -u <service-name>.service --no-pager -n 50
   ```

**OpenCHAMI services fail with connection errors**
   Verify if all openchami services are running:

   ```bash title="Run on: OIM host"
   systemctl list-dependencies openchami.target
   systemctl restart openchami.target
   ```

**omnia.target not found**
   Re-run the `prepare_oim.yml` playbook to regenerate systemd unit files:

   ```bash title="Run on: omnia_core container"
   cd /omnia/prepare_oim
   ansible-playbook prepare_oim.yml
   ```

