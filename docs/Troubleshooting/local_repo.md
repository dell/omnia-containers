# Local Repository and Pulp Issues

Issues related to the `local_repo.yml` playbook, Pulp container operations, and repository synchronization.

## `local_repo.yml` Download Failures

???+ note "Symptom"

    The `local_repo.yml` playbook fails during package download, displaying errors such as "TASK [parse_and_download : Display Failed Packages]" or indicating that specific software packages could not be downloaded.

??? note "Cause"

    - Incorrect URLs in software JSON configuration files.
    - Docker pull limit reached or invalid Docker credentials.
    - Insufficient disk space on Pulp NFS storage.
    - Unreachable software repositories.

??? note "Resolution"

    1. Verify and correct URLs in the software JSON configuration files.
    2. Provide valid Docker credentials in `input/omnia_config_credentials.yml`.
    3. Ensure adequate disk space is available on Pulp NFS storage.
    4. Re-run the `local_repo.yml` playbook.

    **Log analysis for download failures:**

    - Overall download status:

        ```text title="Example"
        /opt/omnia/log/local_repo/<cluster_os>/<cluster_os_version>/<arch>/software.csv
        ```

        Example: `/opt/omnia/log/local_repo/rhel/10.0/x86_64/software.csv`

    - Per-software task results:

        ```text title="Example"
        /opt/omnia/log/local_repo/rhel/10.0/x86_64/<sw>_task_results.log
        ```

        Example for OpenLDAP: `/opt/omnia/log/local_repo/rhel/10.0/x86_64/openldap_task_results.log`

    - Package-level status:

        ```text title="Example"
        /opt/omnia/log/local_repo/<cluster_os>/<cluster_os_version>/<arch>/<sw>/status.csv
        ```

        Example: `/opt/omnia/log/local_repo/rhel/10.0/x86_64/openldap/status.csv`

    - Detailed failure information. View the reason a job was unsuccessful in the `package_status_<pid>.log` file referenced in the `<sw>_task_results.log`:

        ```text title="Example"
        /opt/omnia/log/local_repo/rhel/10.0/x86_64/<sw>/logs/package_status_<pid>.log
        ```

        Example: `/opt/omnia/log/local_repo/rhel/10.0/x86_64/openldap/logs/package_status_858667.log`

    !!! note

        If `local_repo.yml` completes without any package download failures, a `Successful` message is displayed.

## Playbook Fails When Re-Run Multiple Times

???+ note "Symptom"

    The `local_repo.yml` playbook fails when re-run multiple times in quick succession.

??? note "Cause"

    Pulp container resource saturation.

??? note "Resolution"

    Allow the system to idle approximately 1 hour before re-running.

## Pulp Reset Password Failed

???+ note "Symptom"

    Pulp reset password operation fails during `prepare_oim.yml` execution.

??? note "Cause"

    - NFS Storage Export Configuration (PowerScale): Missing or incorrect settings for `nfsv4-no-names`, `nfsv4-no-domain`, `nfsv4-no-domain-uids`, and `nfsv4-allow-numeric-ids`.
    - Inconsistent UID and GID mappings between NFS server and client.
    - Missing `no_root_squash` option in NFS export configuration.
    - NFS server connectivity issues or firewall blocking ports 2049, 111, and 20048.

??? note "Resolution"

    Verify the NFS export configurations and settings mentioned above, then re-run the `prepare_oim.yml` playbook.

## EPEL Repository Instability

???+ note "Symptom"

    EPEL repository is unstable or unavailable during package installation.

??? note "Cause"

    EPEL repository server issues or network connectivity problems.

??? note "Resolution"

    - If no packages depend on EPEL, remove the EPEL URL from the configuration.
    - If required, wait for repository stability or host EPEL packages locally.

## Intermittent Local Repository Sync Failure Due to Non-Persistent Iptables Rules

???+ note "Symptom"

    Local repository sync fails intermittently due to blocked outbound internet access from containers.

??? note "Cause"

    iptables rules on the OIM node are not persistent. After OIM startup, restrictive iptables policies block outbound internet access from containers.

??? note "Resolution"

    As a workaround, relax the iptables default policies on the OIM node:

    ```bash title="Run on: OIM host"
    iptables -P INPUT ACCEPT
    iptables -P FORWARD ACCEPT
    iptables -P OUTPUT ACCEPT
    ```

## Connectivity Issues

???+ note "Symptom"

    The `local_repo.yml` playbook fails with connectivity errors.

??? note "Cause"

    The OIM was unable to reach a required online resource due to a network glitch.

??? note "Resolution"

    Verify all connectivity and re-run the playbook.

## Software Installation Fails With Checksum Error

???+ note "Symptom"

    Software installation fails with a checksum error.

??? note "Cause"

    A local repository for the software has not been configured by the `local_repo.yml` playbook.

??? note "Resolution"

    1. Re-run the `local_repo.yml` playbook with proper inputs to download the software package to the Pulp repository.
    2. Once the local repository has been configured successfully, re-run the failed installation script.

## Pulp Certificate Trust Failure on Compute Nodes

???+ note "Symptom"

    - `dnf install` fails with SSL certificate errors on provisioned compute nodes.
    - Package installation during cloud-init `runcmd` phase fails.
    - Container image pulls from the Pulp mirror fail on nodes.

    Example errors on the compute node:

    ```text title="Expected output"
    SSL certificate problem: unable to get local issuer certificate
    Peer's certificate issuer is not recognized
    Error: Failed to download metadata for repo 'pulp_mirror'
    ```

??? note "Cause"

    The Pulp webserver certificate (`pulp_webserver.crt`) was not copied or trusted on the node. All cloud-init templates include a `runcmd` step that copies the certificate from the NFS-mounted `/cert` directory:

    ```bash
    cp /cert/pulp_webserver.crt /etc/pki/ca-trust/source/anchors && update-ca-trust
    ```

    This step can fail if the NFS mount for `/cert` was not established before the certificate copy step executes.

??? note "Resolution"

    1. Verify the certificate and NFS mount status:

        ```bash title="Run on: compute node"
        # Check if the certificate is present and trusted
        ls -la /etc/pki/ca-trust/source/anchors/pulp_webserver.crt
        ls -la /cert/pulp_webserver.crt

        # Verify the NFS mount for /cert
        mount | grep /cert

        # Test SSL connectivity to Pulp
        openssl s_client -connect <admin_nic_ip>:2225 -showcerts </dev/null 2>&1 | grep -i verify

        # Test package manager connectivity
        dnf repolist
        ```

    2. Mount the certificate NFS share and copy the certificate manually:

        ```bash title="Run on: compute node"
        mount | grep /cert || mount -t nfs <admin_nic_ip>:<share_path>/cert /cert
        cp /cert/pulp_webserver.crt /etc/pki/ca-trust/source/anchors/
        update-ca-trust
        ```

    3. Verify package manager connectivity:

        ```bash title="Run on: compute node"
        dnf repolist
        dnf makecache
        ```

    4. If the issue recurs on re-provisioned nodes, verify the NFS export for the `/cert` directory is accessible from the node network.

## Container Image Pull Fails From Pulp Mirror

???+ note "Symptom"

    - Container images (SIF format) fail to download on Slurm/HPC nodes.
    - `/var/log/apptainer_pull.log` shows pull failures.
    - Expected container images are missing under `/hpc_tools/container_images`.

    Example errors in `/var/log/container_image_download.log` or `/var/log/apptainer_pull.log`:

    ```text title="Expected output"
    [ERROR] Failed to pull container image from Pulp mirror (exit code: 1).
    [INFO] Image may not be available in Pulp or download was interrupted.
    Error: error pulling image: unable to pull <image>: Error initializing source
    TIMEOUT: Container image pull timed out after 1800 seconds
    ```

??? note "Cause"

    - Container image was not synced to Pulp during `local_repo.yml` execution.
    - Pulp mirror endpoint is unreachable from the node (firewall, network issues).
    - Pulp certificate not trusted on the node (see [Pulp certificate trust failure](#pulp-certificate-trust-failure-on-compute-nodes) above).
    - Image tag mismatch between `container_image.list` and what is available in Pulp.

??? note "Resolution"

    1. Check download logs and image status:

        ```bash title="Run on: compute node"
        # Check download log
        tail -50 /var/log/container_image_download.log
        tail -50 /var/log/apptainer_pull.log

        # Check if Pulp mirror is reachable from the node
        curl -sk https://<admin_nic_ip>:2225/v2/_catalog

        # Check what images are expected
        cat /hpc_tools/scripts/container_image.list

        # Check downloaded images
        ls -lh /hpc_tools/container_images/
        ```

    2. Verify the container image exists in Pulp. From the OIM:

        ```bash title="Run on: OIM host"
        podman exec -it omnia_core pulp container repository list
        ```

    3. If the image is missing in Pulp, ensure it is listed in `software_config.json` and re-run `local_repo.yml`.

    4. If the image exists in Pulp but the pull fails, verify certificate trust (see [Pulp certificate trust failure](#pulp-certificate-trust-failure-on-compute-nodes)) and re-run the download script:

        ```bash title="Run on: compute node"
        /hpc_tools/scripts/download_container_image.sh
        ```

!!! info

    - [Create Local Repos](../HowTo/Setup/create_local_repos.md) -- Local repository setup guide.
    - [Log Management](../Operations/log_management.md) -- Where to find logs for deeper diagnosis.
    - [Pulp Cleanup](../Operations/pulp_cleanup.md) -- Pulp cleanup procedures.
