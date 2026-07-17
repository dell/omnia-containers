# Provisioning Issues

Issues related to PXE booting, node discovery, cloud-init configuration, and the `discovery.yml` playbook.

## PXE Boot Failures

### Node Hangs at `nm-wait-online-initrd.service`

???+ note "Symptom"

    Node hangs during boot at the `nm-wait-online-initrd.service` stage.

??? note "Cause"

    IP address conflict with an old node.

??? note "Resolution"

    1. Ensure the old node is powered off or disconnected.
    2. Verify the IP address is unused on the network.
    3. Re-run `provision.yml`.

### PXE Boot Timeout (TFTP/Service Timeout)

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

### Target Server Unreachable After PXE Boot

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

### Root Login Fails After Provisioning

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

### Connecting directly to OpenCHAMI

???+ note "Symptom"

    Unable to issue OpenCHAMI commands. Error includes:

    - `Environment variable OIM_ACCESS_TOKEN unset for reading token for cluster "oim"`
    
??? note "Cause"

    - `OIM_ACCESS_TOKEN` environment variable has not been set.

??? note "Resolution"

    1. Set the `OIM_ACCESS_TOKEN`:

        ```export OIM_ACCESS_TOKEN=$(sudo bash -lc 'gen_access_token')
        ```

    2. Retry the OpenCHAMI command.

## Cloud-Init Issues

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

## Boot Issues on Provisioned Nodes


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

        ```bash title="Run on: compute node"
        cat /var/log/cloud-init-output.log
        ```


    2. Review the provisioning log on the OIM:

        ```bash title="Run on: omnia_core"
        cat /opt/omnia/log/provision.log
        ```


    3. If cloud-init completed with errors, re-run `provision.yml` after
       fixing the root cause.

    4. If the hostname or root password is not configured because cloud-init
       was not loaded in time, wait 5 minutes and retry provisioning the
       node. If the issue persists, redeploy the cluster after running the
       `oim_cleanup.yml` playbook.


## IP Route Conflict After Provisioning


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

        ```bash title="Run on: compute node"
        ip route show
        ```


    2. Delete the conflicting admin route or adjust route priority:

        ```bash title="Run on: compute node"
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
