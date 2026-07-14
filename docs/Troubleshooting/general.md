# General Issues

Issues that affect the OIM, core containers, OpenCHAMI services, SSH connectivity, system recovery, and Ansible Vault operations.

## Omnia Core Container Fails to Deploy

???+ note "Symptom"

    - `omnia.sh` aborts early.
    - `podman pull` fails.
    - Container starts but cannot write to shared path.

??? note "Cause"

    - Podman pull or authentication issues.
    - Time synchronization failure.
    - Invalid OIM hostname.
    - NFS or SELinux permission issues.

??? note "Resolution"

    1. Check container status:

        ```bash title="Run on: OIM host"
        podman ps --format 'table {{.Names}}\t{{.Status}}'
        ```

    2. Check container logs:

        ```bash title="Run on: OIM host"
        podman logs -n 200 omnia_core
        ```

    3. Check time synchronization:

        ```bash title="Run on: OIM host"
        timedatectl status
        chronyc tracking || chronyc sources -v
        ```

    4. Validate OIM hostname (no dots, underscores, commas, uppercase, leading/trailing hyphens, or leading digits; FQDN must be 64 characters or fewer).

    5. Validate NFS mount and SELinux labeling:

        ```bash title="Run on: OIM host"
        podman run --rm -v /shared:/mnt:z registry.access.redhat.com/ubi10/ubi sh -lc 'touch /mnt/.rw'
        ```

    6. Re-run `omnia.sh`.

## Prepare OIM Failures

???+ note "Symptom"

    - Certificate or TLS failures during `prepare_oim.yml`.
    - Expected container not created.
    - Service is running but unreachable.

??? note "Cause"

    - Invalid or expired TLS certificates.
    - Container image pull failures.
    - Network connectivity issues.
    - Incorrect configuration parameters.

??? note "Resolution"

    1. Verify container inventory:

        ```bash title="Run on: OIM host"
        podman ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
        ```

    2. Review container logs for specific error messages.
    3. Verify network connectivity and TLS certificate validity.
    4. Re-run `prepare_oim.yml` after correcting the issue.

## Ansible Vault Decryption Failures

???+ note "Symptom"

    Playbook execution fails with:

    ```text title="Expected output"
    ERROR! Attempting to decrypt but no vault secrets found
    ```

??? note "Cause"

    The vault password file (`.omnia_config_credentials_key`) is missing, incorrect, or inaccessible to the playbook execution context.

??? note "Resolution"

    1. Verify the vault password file exists in the correct location.
    2. Ensure the file has the correct permissions (readable by the user running the playbook).
    3. Re-run the playbook with the correct vault password file:

        ```bash title="Run on: omnia_core container"
        ansible-playbook playbooks/omnia.yml --vault-password-file /root/.vault_pass
        ```

    4. If the vault password is lost, recreate the credentials file:

        ```bash title="Run on: omnia_core container"
        cp input/credentials.yml input/credentials.yml.bak
        ansible-vault create input/credentials.yml
        ```

    For more information on managing encrypted parameters, see [Encrypted Parameters Management](../SecurityConfigurationGuide/misc_configuration.md#encrypted-parameters-management).

## OIM Cleanup NFS Directory Deletion Failure

???+ note "Symptom"

    - `oim_cleanup.yml` fails with: `rmtree failed: [Errno 39] Directory not empty`.
    - Specific error on directories like `/share_omnia_k8s/<node_ip>/kubelet/pods`.
    - Cleanup process completes partially but leaves NFS share directories intact.

    ```text title="Expected output"
    [ERROR]: Task failed: Module failed: rmtree failed: [Errno 39] Directory not empty: '/share_omnia_k8s/10.20.0.15/kubelet/pods'
    ```

??? note "Cause"

    - Kubernetes processes (`kubelet`, `crio`) on compute nodes or OIM have open file handles to NFS share directories.
    - NFS shares are still mounted and in use on compute nodes.

    !!! note

        The OIM cleanup process cleans the contents of NFS shares for both Slurm and Kubernetes. Active processes or mounts may prevent successful cleanup.

??? note "Resolution"

    1. Manually delete the problematic directories on the OIM node:

        ```bash title="Run on: OIM host"
        # /share_omnia_k8s is the mounted NFS share directory
        cd /share_omnia_k8s/<node_ip>/kubelet/pods
        rm -rf *
        cd /share_omnia_k8s/
        rm -rf <node_ip>
        ```

    2. Re-run the OIM cleanup playbook:

        ```bash title="Run on: omnia_core container"
        cd /omnia/utils
        ansible-playbook oim_cleanup.yml
        ```

    !!! tip

        If manual deletion also fails with "Device or resource busy" errors, power off the compute nodes before attempting manual cleanup.

## SSH Key Mismatches and Root Login Failures

???+ note "Symptom"

    SSH connections fail with one of the following errors:

    - `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!`
    - `Permission denied (publickey,gssapi-keyex,gssapi-with-mic)`
    - `ssh: connect to host <ip> port 22: Connection refused`

??? note "Cause"

    - Outdated SSH key after node re-provisioning.
    - cloud-init not rendered on the target node.

??? note "Resolution"

    1. Remove the stale key:

        ```bash title="Run on: OIM host"
        ssh-keygen -R <hostname_or_ip>
        ```

    2. Retry login or reprovision the node.

## SSH to omnia_core Container Fails After Switching to Root With Sudo

???+ note "Symptom"

    After successful execution of the `omnia.sh` script, a message is displayed indicating that you can log in to the `omnia_core` container using `ssh omnia_core`. However, this fails if you initially logged in to the OIM node as a non-root user and then switched to the root user using the `sudo` command.

??? note "Cause"

    SSH access to the `omnia_core` container depends on direct root login. When a user logs in as a non-root user and switches to root using the `sudo` command, the SSH session may not have the required permissions or environment configuration to access the container using `ssh omnia_core`.

??? note "Resolution"

    1. Edit the SSH configuration file and set `PermitRootLogin yes`:

        ```bash title="File: /etc/ssh/sshd_config"
        PermitRootLogin yes
        ```

    2. Restart the SSH service:

        ```bash title="Run on: OIM host"
        systemctl restart sshd
        ```

    3. Log out and re-login to the OIM node directly as the `root` user.

    4. Restart the `omnia_core` container:

        ```bash title="Run on: OIM host"
        podman restart omnia_core
        ```

## OpenCHAMI Issues

### Certificate Expiration

???+ note "Symptom"

    OpenCHAMI certificates have expired, causing service communication failures. This can also cause the cloud-init server to fail when running `provision.yml`.

??? note "Cause"

    The OpenCHAMI certificate has expired, or one or more `openchami.target` services are not running.

??? note "Resolution"

    1. Check if OpenCHAMI target dependencies are satisfied:

        ```bash title="Run on: OIM host"
        systemctl list-dependencies openchami.target
        ```

    2. Update the certificate and restart the target:

        ```bash title="Run on: OIM host"
        sudo openchami-certificate-update update <OIM_hostname>.<domain>
        sudo systemctl restart openchami.target
        ```

    3. If certificate expiry issues persist, restart the `acme-deploy` service:

        ```bash title="Run on: OIM host"
        systemctl restart acme-deploy
        ```

    4. If any other service under the OpenCHAMI target failed, restart it:

        ```bash title="Run on: OIM host"
        systemctl restart <service_name>
        ```

    5. Wait for the OpenCHAMI target and all its dependencies to become active:

        ```bash title="Run on: OIM host"
        systemctl is-active openchami.target
        ```

### Token Expired

???+ note "Symptom"

    OpenCHAMI access token has expired.

??? note "Resolution"

    ```bash title="Run on: OIM host"
    export <OIM_HOSTNAME>_ACCESS_TOKEN=$(sudo bash -lc 'gen_access_token')
    ```

### `provision.yml` Fails: prepare_oim Needs to Be Executed

???+ note "Symptom"

    The `provision.yml` playbook fails with an error indicating that `prepare_oim` needs to be executed first.

??? note "Cause"

    The OpenCHAMI container is not up and running.

??? note "Resolution"

    Perform a cleanup using `oim_cleanup.yml` and re-run `prepare_oim.yml` to bring up the OpenCHAMI containers. After `prepare_oim.yml` completes successfully, re-deploy the cluster.

## Cluster Not Recovering After Power Cycle

???+ note "Symptom"

    After a power cycle, the Omnia cluster does not recover. Nodes fail to rejoin or services do not start.

??? note "Cause"

    - OIM was not powered on before compute nodes.
    - Network connectivity issues after power cycle.
    - Persistent storage or NFS mount failures.

??? note "Resolution"

    1. Follow the proper startup sequence: power on OIM first, then compute nodes.
    2. Verify OIM is fully operational before powering on compute nodes.
    3. Check network connectivity between OIM and compute nodes.
    4. Verify NFS mounts are accessible.
    5. If issues persist, reprovision affected nodes.

## InfiniBand Ports Stuck in Initializing State

???+ note "Symptom"

    InfiniBand ports remain in `Initializing` state after boot.

??? note "Cause"

    The Open Subnet Manager (OpenSM) service is not running on the InfiniBand switch.

??? note "Resolution"

    1. Ensure the Open Subnet Manager service is enabled and running on the InfiniBand switch.
    2. After enabling OpenSM, PXE boot all IB NIC-based nodes.
    3. Verify port state on the host:

        ```bash title="Run on: compute node"
        ibstat
        ```

    4. Confirm the InfiniBand ports transition to `State: Active`.

## System Recovery Issues

### Omnia Containers Not Coming Up After OIM Reboot

???+ note "Symptom"

    Omnia containers fail to start after OIM reboot.

??? note "Cause"

    The Admin NIC on the OIM may have its autoconnect settings disabled (`autoconnect=no`), preventing it from reconnecting automatically after a reboot.

??? note "Resolution"

    Ensure the Admin NIC on the OIM is configured with `autoconnect=yes`. If you changed this configuration, reboot the OIM once to clear any cache-related or stale configuration issues.

### Cluster Nodes Get Incorrect Hostname (nid) After OIM Reboot

???+ note "Symptom"

    Compute nodes are assigned default hostnames such as `nid00...` instead of their configured hostnames from the PXE mapping file, after the OIM has been rebooted.

??? note "Cause"

    If the OIM is rebooted after clusters are deployed, cloud-init files are no longer retained on the OIM. When compute nodes are PXE booted afterwards, they cannot access the cloud-init configuration on the OIM. This results in default hostnames like `nid00...` instead of the configured hostnames from the PXE mapping file.

??? note "Resolution"

    Run the `provision.yml` playbook again with the same PXE mapping file. This ensures cloud-init files are properly recreated and compute nodes receive their correct configured hostnames from the PXE mapping file.

### PostgreSQL Container Deployment Fails After Cleanup

???+ note "Symptom"

    PostgreSQL container deployment fails after running `oim_cleanup.yml`.

??? note "Cause"

    Database initialization issues when existing data is present.

??? note "Resolution"

    - To reuse existing PostgreSQL data at `postgres_data_dir`, re-run `prepare_oim.yml` using the same PostgreSQL database credentials from the previous deployment.
    - To delete existing data and create a new database:

        ```bash title="Run on: omnia_core container"
        ansible-playbook utils/oim_cleanup.yml -e postgres_backup=false
        ```

        After cleanup completes, re-run `prepare_oim.yml` to deploy a new `postgres_container_name` container.

## Playbook Fails Due to Hardware, Network, or Storage Issues

???+ note "Symptom"

    Playbook execution fails due to underlying hardware, network, or storage problems.

??? note "Resolution"

    Identify and fix the underlying issue, then re-run the playbook.

!!! info

    - [Log Management](../Operations/log_management.md) -- Where to find logs for deeper diagnosis.
    - [OIM Cleanup](../Operations/oim_cleanup.md) -- Full OIM reset if issues persist.
    - [Provisioning](provisioning.md) -- PXE boot issues.
    - [Upgrade and Rollback](upgrade_rollback.md) -- Upgrade and rollback failures.
