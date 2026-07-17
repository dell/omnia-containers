# OpenCHAMI Issues

Issues related to OpenCHAMI services, including stack health checks, certificate management, SMD node discovery, BSS boot parameters, cloud-init-server, and cloud-init execution failures.

## OpenCHAMI Stack Health Check — Diagnostic Command Reference

!!! note

    This section is a diagnostic command reference, not a troubleshooting entry. It does not describe a specific symptom, cause, or resolution. Use these commands to verify the overall health of the OpenCHAMI stack on the OIM before or after troubleshooting a specific issue, or as a routine operational check.

**When to use this reference:**

- Before running `provision.yml` to confirm the OpenCHAMI stack is ready
- After an OIM reboot to verify all services recovered
- When investigating any OpenCHAMI-related failure described in the sections below
- As a post-recovery validation after applying a fix

**Service health check:**

```bash title="Run on: OIM host"
# Check openchami.target and all component services
systemctl status openchami.target --no-pager
systemctl list-dependencies openchami.target --plain

# Verify individual services
systemctl status smd --no-pager
systemctl status bss --no-pager
systemctl status cloud-init-server --no-pager
systemctl status hydra --no-pager
systemctl status acme-deploy --no-pager
```

**API connectivity check:**

```bash title="Run on: OIM host"
# Verify API endpoints are responding
ochami smd service status
ochami bss service status
ochami cloud-init service status
```

**Log inspection:**

```bash title="Run on: OIM host"
# View recent logs for any component
journalctl -u smd -n 50 --no-pager
journalctl -u bss -n 50 --no-pager
journalctl -u cloud-init-server -n 50 --no-pager
journalctl -u hydra -n 50 --no-pager
```

**Certificate and token status:**

```bash title="Run on: OIM host"
# Check certificate expiry
openssl s_client -connect localhost:8443 -showcerts </dev/null 2>&1 | openssl x509 -noout -dates

# Check access token validity
echo $<OIM_HOSTNAME>_ACCESS_TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq .exp
```

**Recovery action (if any service is not active):**

```bash title="Run on: OIM host"
sudo systemctl restart openchami.target
sleep 15
systemctl status openchami.target --no-pager
```

If the restart does not resolve the issue, refer to the specific troubleshooting entry in the sections below that matches the failing service.

## Certificate Expiration

???+ note "Symptom"

    - `provision.yml` or `ochami` CLI commands fail with TLS errors
    - BSS or cloud-init-server returns connection refused or certificate errors
    - Nodes fail to PXE boot or cloud-init cannot reach the OIM

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

## Token Expired

???+ note "Symptom"

    - ochami CLI commands return 401 Unauthorized
    - provision.yml fails during OpenCHAMI authentication phase
    - BSS or SMD API calls return authentication errors

    **Example errors:**

    ```json
    {"error":"token is expired","status":401}
    ```

    ```text
    ochami bss boot params get: 401 Unauthorized
    Failed to generate access token after 5 retries
    ```

??? note "Cause"

    The OpenCHAMI access token (JWT issued via Hydra OIDC client_credentials grant) has reached its expiration time. Omnia's `openchami_auth.yml` task retries token generation up to 5 times with 5-second delays. Manual regeneration is required if automatic retries fail.

??? note "Resolution"

    **Diagnostics**

    ```bash title="Run on: OIM host"
    # Check if the token environment variable is set
    echo $<OIM_HOSTNAME>_ACCESS_TOKEN

    # Inspect the token expiry (if jq is available)
    echo $<OIM_HOSTNAME>_ACCESS_TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq .exp

    # Test BSS connectivity with the current token
    ochami bss service status
    ```

    **Resolution**

    ```bash title="Run on: OIM host"
    export <OIM_HOSTNAME>_ACCESS_TOKEN=$(sudo bash -lc 'gen_access_token')
    ```

    If `gen_access_token` fails, verify the Hydra OIDC service is running:

    ```bash title="Run on: OIM host"
    systemctl status hydra
    journalctl -u hydra -n 50 --no-pager
    ```

## provision.yml Fails — OpenCHAMI Services Not Running

???+ note "Symptom"

    - `provision.yml` fails during the "Provision nodes, configure bss and cloud-init" play
    - Playbook output contains one of the following error messages:
        - `cloud-init-server is not running after 16 retries`
        - `openchami.target is not up after 16 retries`
        - `Failed to discover ochami nodes after retries`
        - `smd service is not running`
        - `ochami bss boot params get: 401 Unauthorized` (token expired)

    **Example errors:**

    **cloud-init-server is not running after 16 retries.**

    Next steps:
    1. Check service status: `systemctl status cloud-init-server`
    2. Check if openchami.target dependencies are satisfied: `systemctl list-dependencies openchami.target`

    **openchami.target is not up after 16 retries.**

    Next steps:
    1. Check target status: `systemctl status openchami.target`
    2. View logs: `journalctl -u openchami.target -n 50`

    **Failed to discover ochami nodes after retries.**

    Next steps:
    1. Verify nodes.yaml is valid
    2. Check SMD connectivity (see below)

??? note "Cause"

    `provision.yml` requires the OpenCHAMI stack (`openchami.target`, which manages `smd`, `bss`, `cloud-init-server`, `hydra`, `acme-deploy`) to be running on the OIM. Common causes of failure:

    - `prepare_oim.yml` was not run or failed partway through, leaving OpenCHAMI services undeployed
    - OpenCHAMI service crashed after deployment (certificate expiry, database failure, port conflict)
    - OIM was rebooted and `openchami.target` did not recover automatically (dependency ordering, NIC autoconnect disabled)
    - Access token expired — the JWT token issued by Hydra OIDC has a limited lifetime; `provision.yml` calls `openchami_auth.yml` to regenerate it, but if Hydra itself is down, token generation fails
    - SELinux context on OpenCHAMI workdir is incorrect (`provision.yml` sets `container_file_t` but this can be reset after NFS remount)
    - `nodes.yaml` generation failed — invalid `pxe_mapping_file.csv` or missing `functional_groups_config.yml` produced malformed input for `ochami discover`

??? note "Resolution"

    **Diagnostics**

    Run these on the OIM to identify the specific failure:

    ```bash title="Run on: OIM host"
    # 1. Check openchami.target and all its component services
    systemctl status openchami.target --no-pager
    systemctl list-dependencies openchami.target --plain
    systemctl status smd bss cloud-init-server hydra acme-deploy --no-pager

    # 2. Check for failed services
    systemctl --failed --no-pager

    # 3. View service logs for the first failure
    journalctl -u openchami.target -b --no-pager | tail -30
    journalctl -u smd -b --no-pager | tail -30
    journalctl -u cloud-init-server -b --no-pager | tail -30

    # 4. Verify API connectivity
    /usr/bin/ochami smd service status
    /usr/bin/ochami bss service status
    /usr/bin/ochami cloud-init service status

    # 5. Check certificate validity
    openssl s_client -connect localhost:8443 -showcerts </dev/null 2>&1 | openssl x509 -noout -dates

    # 6. Check access token
    echo $<OIM_HOSTNAME>_ACCESS_TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq .exp

    # 7. Verify nodes.yaml was generated correctly
    cat /opt/omnia/openchami/workdir/nodes/nodes.yaml

    # 8. Verify Omnia containers are running
    podman ps -a --format "{{.Names}} {{.Status}}"
    ```

    Follow the appropriate resolution based on the diagnostic findings:

    **1. If prepare_oim.yml was never run or failed:** Run the cleanup and re-deploy:

    ```bash title="Run on: OIM host"
    ansible-playbook utils/oim_cleanup.yml
    ansible-playbook prepare_oim/prepare_oim.yml
    ```

    After `prepare_oim.yml` completes successfully, re-run `provision.yml`.

    **2. If openchami.target services are down but were previously deployed:** Restart the target and wait for all services:

    ```bash title="Run on: OIM host"
    sudo systemctl restart openchami.target
    sleep 15
    systemctl status openchami.target --no-pager
    /usr/bin/ochami smd service status
    /usr/bin/ochami cloud-init service status
    ```

    **3. If certificates have expired:** Renew and restart:

    ```bash title="Run on: OIM host"
    sudo openchami-certificate-update update <OIM_hostname>.<domain>
    sudo systemctl restart acme-deploy
    sleep 10
    sudo systemctl restart openchami.target
    ```

    **4. If the access token is expired and Hydra is running:** Regenerate the token:

    ```bash title="Run on: OIM host"
    export <OIM_HOSTNAME>_ACCESS_TOKEN=$(sudo bash -lc 'gen_access_token')
    ```

    **5. If nodes.yaml is malformed:** Verify `pxe_mapping_file.csv` has valid entries (MAC addresses, xnames, functional groups), then re-run `provision.yml` — it regenerates `nodes.yaml` from the CSV on every run.

    **6. If SELinux context is incorrect:** Re-apply the context:

    ```bash title="Run on: OIM host"
    chcon -R system_u:object_r:container_file_t:s0 /opt/omnia/openchami
    ```

    After resolving the issue, re-run `provision.yml`:

    ```bash title="Run on: OIM host"
    ansible-playbook provision/provision.yml
    ```

    !!! note

        `provision.yml` automatically retries cloud-init-server (16 retries × 15 seconds) and attempts an `openchami.target` restart if the initial check fails. If the playbook still fails after these retries, the underlying service has a persistent problem that requires manual diagnosis.

## SMD Node Discovery Fails

???+ note "Symptom"

    - `provision.yml` fails at "Discover ochami nodes" task
    - `ochami smd component get` returns empty results or HTTP 404
    - Nodes are not visible in SMD after running `provision.yml`

    **Example errors:**

    - Failed to discover ochami nodes after retries
    - smd service is not running
    - ochami smd component get: no components found
    - HTTP 404: node `<xname>` not found in SMD

??? note "Cause"

    - SMD service is not running or failed to start
    - `openchami.target` and its dependencies are not fully active
    - Invalid or malformed `nodes.yaml` (generated from `pxe_mapping_file.csv`)
    - Network connectivity issues between the OIM and SMD

??? note "Resolution"

    **Diagnostics**

    ```bash title="Run on: OIM host"
    # Check SMD service status
    systemctl status smd
    journalctl -u smd -n 50 --no-pager

    # Check openchami.target and all dependencies
    systemctl status openchami.target
    systemctl list-dependencies openchami.target --plain

    # Verify SMD API is reachable
    ochami smd service status

    # List registered nodes
    ochami smd component get | jq '.Components[] | select(.Type == "Node")'

    # Verify nodes.yaml is valid
    cat /opt/omnia/openchami/workdir/nodes/nodes.yaml
    ```

    1. Restart `openchami.target` and verify all services are active:

        ```bash title="Run on: OIM host"
        sudo systemctl restart openchami.target
        sleep 15
        ochami smd service status
        ```

    2. Verify `pxe_mapping_file.csv` contains valid MAC addresses and xnames, then re-run `provision.yml`.

## BSS Boot Parameters Not Applied

???+ note "Symptom"

    - Nodes boot with the default image instead of the expected functional group image
    - `ochami bss boot params get` returns empty or incorrect kernel/initrd paths
    - Nodes do not pick up updated boot parameters after re-running `provision.yml`

    **Example errors:**

    - node boots default image, ignoring BSS boot parameters
    - ochami bss boot params get: no params found for MAC `<mac>`
    - Missing kernel or initrd in BSS boot parameters

??? note "Cause"

    - BSS service is not running or has stale data
    - The kernel/initrd images were not built or uploaded to S3 (`build_image_x86_64.yml` not run)
    - MAC addresses in `pxe_mapping_file.csv` do not match the node hardware

??? note "Resolution"

    **Diagnostics**

    ```bash title="Run on: OIM host"
    # Check BSS service status
    ochami bss service status

    # List all boot parameters
    ochami bss boot params get -F yaml

    # Verify kernel/initrd in S3
    s3cmd ls -Hr s3://boot-images
    ```

    1. Ensure `build_image_x86_64.yml` (or `build_image_aarch64.yml`) completed successfully and images exist in S3.
    2. Verify MAC addresses in `pxe_mapping_file.csv` match node hardware.
    3. Re-run `provision.yml` to refresh BSS boot parameters.

## cloud-init-server Not Reachable

???+ note "Symptom"

    - `provision.yml` fails at "Verify cloud-init-server is reachable" task
    - Nodes complete PXE boot but cloud-init fails to fetch user-data from the OIM

    **Example errors:**

    - cloud-init-server is not running after 16 retries
    - ochami cloud-init service status: connection refused

??? note "Cause"

    - `cloud-init-server` systemd service is not running
    - `openchami.target` dependencies are not satisfied
    - Certificate issues preventing the service from starting

??? note "Resolution"

    **Diagnostics**

    ```bash title="Run on: OIM host"
    # Check cloud-init-server status
    systemctl status cloud-init-server
    journalctl -u cloud-init-server -n 50 --no-pager

    # Check if openchami.target dependencies are satisfied
    systemctl list-dependencies openchami.target --plain

    # Test cloud-init endpoint from OIM
    ochami cloud-init service status
    ```

    ```bash title="Run on: OIM host"
    # If certificate issues, restart acme-deploy first
    sudo systemctl restart acme-deploy
    sleep 10

    # Restart the cloud-init-server
    sudo systemctl restart cloud-init-server

    # If still failing, restart the full openchami stack
    sudo systemctl restart openchami.target
    ```

    Once the service is running, re-run `provision.yml`.

## Cloud-init Execution Failures on Compute Nodes

???+ note "Symptom"

    - Node completes PXE boot but cloud-init does not finish successfully
    - Services (Slurm, Kubernetes, LDMS) are not configured after provisioning
    - Node is reachable via SSH but cloud-init scripts did not execute
    - Upgrade playbook reports "Cloud-init did not complete within timeout"

    **Example errors:**

    In `/var/log/cloud-init-output.log` or `/var/log/cloud-init.log` on the compute node:

    ```text
    cloud-init[ERROR]: Failed running module cc_scripts_user
    cloud-init status: error
    WARNING: could not determine cloud type
    stage failed: 'init-network' (duration: 120.0s, error: timeout waiting for metadata)
    ```

??? note "Cause"

    - Network not ready when cloud-init attempts to fetch metadata from the OIM (`http://<admin_nic_ip>:8081/cloud-init/`)
    - cloud-init user-data or vendor-data contains errors (invalid YAML, missing scripts)
    - NFS mount failures during `runcmd` scripts (NFS server unreachable, incorrect `fstab` entries)
    - Stale cloud-init state on re-provisioned nodes (cloud-init skips modules it has already run)
    - Pulp certificate trust not established (`pulp_webserver.crt` copy failed), causing `dnf` package installs to fail
    - Timeout on CUDA driver installation or DOCA setup during `runcmd` phase

??? note "Resolution"

    **Diagnostics**

    Run these commands on the affected compute node:

    ```bash title="Run on: compute node"
    # Overall cloud-init status
    cloud-init status --long

    # Execution log (shows runcmd script output)
    tail -100 /var/log/cloud-init-output.log

    # Detailed error log
    grep -i error /var/log/cloud-init.log | tail -30

    # What user-data was injected by the OIM
    cloud-init query userdata

    # Which cloud-init modules completed successfully
    ls /var/lib/cloud/instance/sem/

    # Check NFS mounts (many cloud-init scripts depend on NFS)
    mount | grep nfs
    cat /etc/fstab | grep nfs

    # Check Pulp certificate trust
    ls /etc/pki/ca-trust/source/anchors/pulp_webserver.crt
    openssl s_client -connect <admin_nic_ip>:2225 -showcerts </dev/null 2>&1 | grep -i verify
    ```

    1. If cloud-init is still running, wait for it to complete (check with `cloud-init status --long`).

    2. If cloud-init completed with errors, review the specific failure in `/var/log/cloud-init-output.log`. Common sub-failures:

        - **NFS mount failure**: Verify OIM NFS service is reachable from the node (`showmount -e <admin_nic_ip>`)
        - **Pulp cert trust failure**: Manually copy the certificate and update trust:

        ```bash title="Run on: compute node"
        cp /cert/pulp_webserver.crt /etc/pki/ca-trust/source/anchors/ && update-ca-trust
        ```

        - **CUDA/DOCA timeout or failure**: These are non-critical — cloud-init scripts use `|| echo "failed (non-critical)"` so the overall provisioning continues. However, GPU workloads will not function until these components are recovered. Verify the status and recover if needed:

        **Verify CUDA driver:**

        ```bash title="Run on: compute node"
        # Check if NVIDIA driver is functional
        nvidia-smi
        # Expected: GPU listing with driver version. If "command not found" or error, driver needs recovery.

        # Review driver install log
        tail -30 /var/log/nvidia_install.log
        ```

        **Verify CUDA toolkit:**

        ```bash title="Run on: compute node"
        # Check if toolkit is available
        ls /usr/local/cuda/bin/nvcc 2>/dev/null && nvcc --version || echo "CUDA toolkit NOT available"

        # Check NFS mount for shared toolkit
        mount | grep cuda

        # Check toolkit installation log
        tail -30 /var/log/cuda_toolkit_install.log

        # Check lock manager status (shared NFS install)
        cat /hpc_tools/cuda/.cuda_install_status.log 2>/dev/null
        ```

        **Verify DCGM:**

        ```bash title="Run on: compute node"
        # Check DCGM service
        systemctl status nvidia-dcgm --no-pager
        dcgmi discovery -l

        # Review DCGM setup log
        tail -30 /var/log/dcgm_setup.log
        ```

        **Verify DOCA-OFED:**

        ```bash title="Run on: compute node"
        # Check if DOCA is installed
        rpm -q doca-ofed && echo "DOCA-OFED installed" || echo "DOCA-OFED NOT installed"

        # Check InfiniBand device status
        ibstat 2>/dev/null || echo "ibstat not available"

        # Check DOCA MPI environment
        ls /opt/mellanox/doca/tools/ 2>/dev/null
        ```

        **Verify nvidia-peermem (RDMA environments only):**

        ```bash title="Run on: compute node"
        # Check if peermem module is loaded
        lsmod | grep -E 'nv_peer_mem|nvidia_peermem'

        # Review install log
        tail -20 /var/log/nvidia_peermem_install.log
        ```

        If any component failed, refer to the Slurm troubleshooting section for CUDA Toolkit and DCGM Setup Failure recovery procedures.

    3. For stale cloud-init state on re-provisioned nodes, the node image should be rebuilt via `build_image_x86_64.yml` to ensure a clean `/var/lib/cloud` state. Do not manually run `cloud-init clean` on provisioned nodes as this may break existing configuration.

    4. If cloud-init timed out during upgrade, SSH to the node and wait for completion, then re-run the upgrade playbook (completed steps are skipped automatically).

    !!! note

        Omnia collects cloud-init logs from all node types during log collection (`log_collector/collect.yml`). The collected files include `/var/log/cloud-init.log` and `/var/log/cloud-init-output.log`.

