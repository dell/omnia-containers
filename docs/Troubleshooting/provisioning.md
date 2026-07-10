# Provisioning Issues

Issues related to PXE booting, node discovery, cloud-init configuration, the `discovery.yml` playbook, and local repository (Pulp) operations.

## PXE boot failures

### Node hangs at `nm-wait-online-initrd.service`

???+ note "Symptom"

    Node hangs during boot at the `nm-wait-online-initrd.service` stage.

??? note "Cause"

    IP address conflict with an old node.

??? note "Resolution"

    1. Ensure the old node is powered off or disconnected.
    2. Verify the IP address is unused on the network.
    3. Re-run `provision.yml`.

### PXE boot timeout (TFTP/service timeout)

???+ note "Symptom"

    PXE boot process times out with TFTP or service timeout errors:

    ```text title="Expected output"
    PXE-E32: TFTP open timeout
    PXE-T02: TFTP packet timeout
    ```

??? note "Cause"

    - PXE NIC not configured in BIOS.
    - Extra NIC interfering with the boot process.
    - Multiple PXE servers on the same network.

??? note "Resolution"

    1. Configure BIOS: navigate to **Network Settings > PXE Device** and assign the correct active NIC.
    2. Remove or disable any extra NIC until after boot completion.
    3. Verify no rogue PXE/DHCP servers exist on the admin network.

### Target server unreachable after PXE boot

???+ note "Symptom"

    Target server becomes unreachable after PXE boot completes.

??? note "Cause"

    - POST errors on the target server.
    - F1 hardware prompts blocking boot.
    - Boot stalls due to hardware issues.

??? note "Resolution"

    1. Log in to iDRAC and check console output.
    2. Clear errors or disable POST prompts.
    3. Hard reboot the server.
    4. Disable PXE temporarily if needed to bypass boot loops.

### Root login fails after provisioning

???+ note "Symptom"

    Unable to log in as root via SSH. Error messages include:

    - `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!`
    - `Permission denied (publickey,gssapi-keyex,gssapi-with-mic)`
    - `ssh: connect to host <ip> port 22: Connection refused`

??? note "Cause"

    - Outdated SSH key in `~/.ssh/known_hosts`.
    - cloud-init not rendered on the target node.

??? note "Resolution"

    1. Remove the stale SSH key:

        ```bash title="Run on: OIM host"
        ssh-keygen -R <hostname>
        ```

    2. Retry login or reprovision the node.

## cloud-init issues

???+ note "Symptom"

    Nodes boot the OS successfully but post-boot configuration fails. The node is accessible via console but network settings, hostname, or SSH keys are not configured correctly.

??? note "Cause"

    - The cloud-init data source is not configured.
    - The cloud-init configuration file has syntax errors.
    - The cloud-init service was disabled or removed from the OS image.

??? note "Resolution"

    1. Check cloud-init status on the affected node:

        ```bash title="Run on: compute node"
        cloud-init status --long
        ```

    2. Review cloud-init logs:

        ```bash title="Run on: compute node"
        cat /var/log/cloud-init.log
        cat /var/log/cloud-init-output.log
        ```

    3. If cloud-init was disabled, re-enable it:

        ```bash title="Run on: compute node"
        systemctl enable cloud-init
        cloud-init clean
        reboot
        ```

## Local repository and Pulp issues

### `local_repo.yml` download failures

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

### Failure when re-run multiple times

???+ note "Symptom"

    The `local_repo.yml` playbook fails when re-run multiple times in quick succession.

??? note "Cause"

    Pulp container resource saturation.

??? note "Resolution"

    Allow the system to idle approximately 1 hour before re-running.

### Pulp reset password failed

???+ note "Symptom"

    Pulp reset password operation fails during `prepare_oim.yml` execution.

??? note "Cause"

    - NFS Storage Export Configuration (PowerScale): Missing or incorrect settings for `nfsv4-no-names`, `nfsv4-no-domain`, `nfsv4-no-domain-uids`, and `nfsv4-allow-numeric-ids`.
    - Inconsistent UID and GID mappings between NFS server and client.
    - Missing `no_root_squash` option in NFS export configuration.
    - NFS server connectivity issues or firewall blocking ports 2049, 111, and 20048.

??? note "Resolution"

    Verify the NFS export configurations and settings mentioned above, then re-run the `prepare_oim.yml` playbook.

### EPEL repository instability

???+ note "Symptom"

    EPEL repository is unstable or unavailable during package installation.

??? note "Cause"

    EPEL repository server issues or network connectivity problems.

??? note "Resolution"

    - If no packages depend on EPEL, remove the EPEL URL from the configuration.
    - If required, wait for repository stability or host EPEL packages locally.

### Intermittent local repository sync failure due to non-persistent iptables rules

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

### Connectivity issues

???+ note "Symptom"

    The `local_repo.yml` playbook fails with connectivity errors.

??? note "Cause"

    The OIM was unable to reach a required online resource due to a network glitch.

??? note "Resolution"

    Verify all connectivity and re-run the playbook.

### Software installation fails with checksum error

???+ note "Symptom"

    Software installation fails with a checksum error.

??? note "Cause"

    A local repository for the software has not been configured by the `local_repo.yml` playbook.

??? note "Resolution"

    1. Re-run the `local_repo.yml` playbook with proper inputs to download the software package to the Pulp repository.
    2. Once the local repository has been configured successfully, re-run the failed installation script.

## Boot issues on provisioned nodes


???+ note "Symptom"

    A provisioned node fails to boot correctly, or post-boot configuration
    (hostname, network, SSH keys) is incomplete or missing.

??? note "Cause"

    - cloud-init failed during the boot process.
    - The node's boot image was not built correctly.
    - Network configuration conflicts prevent the node from reaching the OIM.
    - cloud-init is not properly loaded on the target servers during provisioning. For more information, see [Inconsistent cloud-init behavior with multiple node group configurations](https://github.com/OpenCHAMI/cloud-init/issues/89).

??? note "Resolution"

    1. Check the cloud-init output log on the affected node:

       ```bash
       cat /var/log/cloud-init-output.log
       ```


    2. Review the provisioning log on the OIM:

       ```bash
       cat /opt/omnia/log/provision.log
       ```


    3. If cloud-init completed with errors, re-run `provision.yml` after
       fixing the root cause.

    4. If the hostname or root password is not configured because cloud-init
       was not loaded in time, wait 5 minutes and retry provisioning the
       node. If the issue persists, redeploy the cluster after running the
       `oim_cleanup.yml` playbook.


## IP route conflict after provisioning


???+ note "Symptom"

    After provisioning, nodes lose connectivity on the admin network or
    cannot reach the OIM, while the public/internet NIC works (or vice
    versa).

??? note "Cause"

    An IP route conflict exists between the admin network and an
    additional NIC (for example, an internet-facing NIC). Both NICs may
    have overlapping default routes.

??? note "Resolution"

    1. List current routes on the affected node:

       ```bash
       ip route show
       ```


    2. Delete the conflicting admin route or adjust route priority:

       ```bash
       # Delete conflicting route
       ip route del <conflicting_route>

       # Or set metric to prioritize one route over another
       ip route add <network> via <gateway> dev <nic> metric <priority>
       ```


    3. To make the change persistent, update the network configuration
       files for the appropriate NIC.


!!! info

    - [Discover Nodes](../HowTo/Setup/discover_nodes.md) -- Full node discovery procedure.
    - [PXE Boot Playbook](../HowTo/Setup/configure_pxe_boot.md) -- PXE boot configuration guide.
    - [Log Management](../Operations/log_management.md) -- Log locations for deeper diagnosis.
