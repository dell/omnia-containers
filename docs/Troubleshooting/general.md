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

    After the Omnia Infrastructure Manager (OIM) and cluster nodes are powered on, one or more of the following conditions may occur:

    - One or more compute nodes remain NotReady, Down, Unknown, or otherwise unavailable
    - Kubernetes nodes do not rejoin the cluster
    - Kubernetes pods remain in Pending, ContainerCreating, CrashLoopBackOff, or Unknown state
    - Slurm nodes remain DOWN, DRAIN, NOT_RESPONDING, or are missing from sinfo
    - Omnia services on the OIM are inactive or failed
    - OpenCHAMI, Pulp, authentication, provisioning, or related Podman containers are not running
    - Compute nodes cannot reach the OIM over the management network
    - NFS-backed directories are unavailable or commands accessing them hang
    - Cluster applications fail because shared storage, DNS, time synchronization, or control-plane services are unavailable

    !!! note

        Do not immediately reprovision an affected node. First determine whether the failure is caused by an unavailable OIM service, network connectivity, shared storage, or a node-local service.

??? note "Cause"

    - The compute nodes were powered on before the OIM became fully operational
    - One or more services associated with omnia.target failed to start
    - An Omnia Podman container stopped or entered an unhealthy state
    - The management interface, routing, DNS, firewall, or VLAN configuration did not recover correctly
    - An NFS server or NFS mount is unavailable
    - Time synchronization has not recovered
    - Kubernetes or Slurm node services failed to start
    - A node retained stale network, mount, or runtime state after the power interruption
    - The node operating system or provisioning state was damaged by an ungraceful shutdown

??? note "Resolution"

    Perform the following checks in order. Resolve OIM-wide dependencies before troubleshooting individual compute nodes.

    **1. Verify that the OIM is fully operational**

    Log in to the OIM and verify that the operating system has completed startup:

    ```bash title="Run on: OIM host"
    uptime
    systemctl is-system-running
    systemctl --failed --no-pager
    ```

    If `systemctl is-system-running` reports starting, wait for startup jobs to complete and run the command again. If it reports degraded, examine the failed units:

    ```bash title="Run on: OIM host"
    systemctl --failed --no-pager
    ```

    Do not power-cycle the compute nodes again until the required OIM services are operational.

    **2. Verify Omnia services on the OIM**

    Check the Omnia core service and the services associated with omnia.target:

    ```bash title="Run on: OIM host"
    systemctl status omnia_core.service --no-pager
    systemctl list-dependencies omnia.target
    ```

    The Omnia deployment documentation identifies omnia_core.service, pulp.service, omnia_auth.service, and the OpenCHAMI services under openchami.target (smd, bss, cloud-init-server, hydra, acme-deploy) as dependencies that may be present under omnia.target. The exact set depends on the deployed configuration.

    List failed Omnia and OpenCHAMI-related services:

    ```bash title="Run on: OIM host"
    systemctl --failed --no-pager
    systemctl status omnia.target --no-pager
    systemctl status openchami.target --no-pager
    ```

    For each failed service, inspect its journal. For example:

    ```bash title="Run on: OIM host"
    journalctl -u omnia_core.service -b --no-pager
    journalctl -u pulp.service -b --no-pager
    journalctl -u openchami.target -b --no-pager
    ```

    To display recent high-priority errors from the current boot:

    ```bash title="Run on: OIM host"
    journalctl -b -p err..alert --no-pager
    ```

    If a service failed because one of its dependencies was unavailable, correct the dependency first. Then restart only the affected service:

    ```bash title="Run on: OIM host"
    systemctl restart <service_name>
    systemctl status <service_name> --no-pager
    ```

    Replace `<service_name>` with the failed unit displayed by systemctl --failed. Avoid repeatedly restarting omnia.target without first reviewing the failed service logs. Repeated restarts can obscure the original failure and unnecessarily interrupt healthy services.

    **3. Verify Omnia Podman containers**

    List all containers, including containers that exited during startup:

    ```bash title="Run on: OIM host"
    podman ps -a
    ```

    Check a specific container:

    ```bash title="Run on: OIM host"
    podman ps -a --filter name=<container_name>
    podman inspect <container_name> --format 'status={{.State.Status}} exit_code={{.State.ExitCode}} error={{.State.Error}}'
    ```

    View its recent logs:

    ```bash title="Run on: OIM host"
    podman logs --tail 200 <container_name>
    ```

    If the container is managed by a systemd unit, restart the corresponding systemd service rather than starting the container manually:

    ```bash title="Run on: OIM host"
    systemctl restart <service_name>
    systemctl status <service_name> --no-pager
    ```

    Use the container logs and the associated systemd journal to determine whether the failure is related to storage, port binding, certificates, database availability, or another service dependency.

    **4. Verify network recovery between the OIM and compute nodes**

    On the OIM, check the management interfaces, addresses, routes, and NetworkManager state:

    ```bash title="Run on: OIM host"
    ip -brief address
    ip route
    nmcli device status
    nmcli connection show --active
    ```

    Test connectivity to each affected compute node:

    ```bash title="Run on: OIM host"
    ping -c 4 <compute_node_ip>
    ip neigh show <compute_node_ip>
    ```

    If hostnames are used, verify name resolution separately:

    ```bash title="Run on: OIM host"
    getent hosts <compute_node_hostname>
    ping -c 4 <compute_node_hostname>
    ```

    On the affected compute node, test the return path to the OIM:

    ```bash title="Run on: compute node"
    ip -brief address
    ip route
    ping -c 4 <oim_ip>
    getent hosts <oim_hostname>
    ```

    Interpret the results as follows:

    - No management IP address: Check the interface and NetworkManager connection
    - No route to the OIM: Correct the route, VLAN, or gateway configuration
    - IP address works but hostname fails: Investigate DNS or /etc/hosts
    - OIM can reach the node but the node cannot reach the OIM: Check asymmetric routing, firewall rules, bonding, or VLAN configuration
    - Duplicate or stale neighbor entry: Check for an IP address conflict before clearing the entry

    To inspect recent network-service errors:

    ```bash title="Run on: OIM host or compute node"
    journalctl -u NetworkManager -b --no-pager
    ```

    **5. Verify time synchronization**

    Significant clock differences can prevent certificate-based services and distributed cluster components from operating correctly. Run the following command on the OIM and on an affected node:

    ```bash title="Run on: OIM host or compute node"
    timedatectl status
    ```

    If Chrony is used:

    ```bash title="Run on: OIM host or compute node"
    systemctl status chronyd --no-pager
    chronyc tracking
    chronyc sources -v
    ```

    Resolve DNS, routing, or NTP-source connectivity problems before continuing.

    **6. Verify NFS and shared-storage availability**

    On the OIM and affected nodes, list NFS filesystems:

    ```bash title="Run on: OIM host or compute node"
    findmnt -t nfs,nfs4
    ```

    Check a specific expected mount point:

    ```bash title="Run on: OIM host or compute node"
    findmnt <mount_point>
    mountpoint <mount_point>
    timeout 10 ls -la <mount_point>
    ```

    If the mount is absent, examine its configuration:

    ```bash title="Run on: OIM host or compute node"
    grep -E '^[^#].+[[:space:]]nfs4?[[:space:]]' /etc/fstab
    ```

    Test whether the NFS server is reachable:

    ```bash title="Run on: OIM host or compute node"
    ping -c 4 <nfs_server>
    ```

    Where supported, list exported filesystems:

    ```bash title="Run on: OIM host or compute node"
    showmount -e <nfs_server>
    ```

    Review mount-related errors from the current boot:

    ```bash title="Run on: OIM host or compute node"
    journalctl -b --no-pager | grep -Ei 'nfs|mount|rpc|stale|timed out'
    ```

    After confirming that the NFS server and network are available, mount only the affected filesystem:

    ```bash title="Run on: OIM host or compute node"
    mount <mount_point>
    findmnt <mount_point>
    ```

    !!! warning

        Do not use `mount -a` as the first recovery action on a production cluster. It attempts every configured filesystem and can make diagnosis more difficult if multiple remote filesystems are unavailable. If a command against the mount point hangs, investigate the NFS server and network path before restarting workload services.

    **7. Check the cluster manager**

    Use the checks applicable to the cluster manager deployed in the environment.

    *Kubernetes-based cluster*

    From a host with the required Kubernetes configuration:

    ```bash title="Run on: control node"
    kubectl get nodes -o wide
    kubectl get pods -A -o wide
    kubectl get events -A --sort-by=.metadata.creationTimestamp
    ```

    For an affected node:

    ```bash title="Run on: control node"
    kubectl describe node <node_name>
    ```

    Look for conditions such as:

    - Ready=False or Ready=Unknown
    - NetworkUnavailable=True
    - DiskPressure=True
    - MemoryPressure=True
    - Expired certificates or authentication failures
    - Container runtime or CNI initialization failures

    On the affected node, check the node agent and container runtime used by the deployment:

    ```bash title="Run on: compute node"
    systemctl status kubelet --no-pager
    journalctl -u kubelet -b --no-pager
    systemctl status containerd --no-pager
    journalctl -u containerd -b --no-pager
    ```

    If the services are installed but inactive, and their network and storage dependencies are healthy, restart them:

    ```bash title="Run on: compute node"
    systemctl restart containerd
    systemctl restart kubelet
    ```

    Recheck the node:

    ```bash title="Run on: control node"
    kubectl get node <node_name> -o wide
    kubectl describe node <node_name>
    ```

    !!! note

        Do not delete or reprovision the node solely because it temporarily reports NotReady.

    *Slurm-based cluster*

    On the Slurm control node, check cluster and node state:

    ```bash title="Run on: Slurm control node"
    sinfo -R
    sinfo -N -l
    scontrol show nodes
    ```

    On an affected compute node:

    ```bash title="Run on: compute node"
    systemctl status slurmd --no-pager
    journalctl -u slurmd -b --no-pager
    ```

    On the Slurm control node:

    ```bash title="Run on: Slurm control node"
    systemctl status slurmctld --no-pager
    journalctl -u slurmctld -b --no-pager
    ```

    After correcting the underlying network, storage, time, or service problem, restart only the failed Slurm daemon:

    ```bash title="Run on: compute node"
    systemctl restart slurmd
    ```

    If the node is healthy but remains marked DOWN, return it to service from the control node:

    ```bash title="Run on: Slurm control node"
    scontrol update NodeName=<node_name> State=RESUME
    ```

    Then verify:

    ```bash title="Run on: Slurm control node"
    sinfo -N -l
    scontrol show node <node_name>
    ```

    !!! note

        Do not resume a node until slurmd, shared storage, networking, and required accelerators or devices are healthy.

    **8. Reboot only the affected node, if necessary**

    If the OIM, networking, time synchronization, shared storage, and cluster services are healthy but a node still does not recover, perform a controlled reboot of only that node:

    ```bash title="Run on: compute node"
    systemctl reboot
    ```

    After the node returns, verify:

    ```bash title="Run on: compute node"
    systemctl --failed --no-pager
    ip -brief address
    findmnt -t nfs,nfs4
    ```

    Then repeat the Kubernetes or Slurm checks.

    **9. Reprovision only after isolating the failure to the node**

    Reprovision the affected node only when all the following conditions are true:

    - OIM services and containers are healthy
    - The node has working management-network connectivity
    - DNS and time synchronization are operating correctly
    - Required NFS or shared-storage services are available
    - Other nodes with the same configuration have recovered successfully
    - Node-local services continue to fail after a controlled reboot
    - Logs indicate damaged system state, missing configuration, failed provisioning artifacts, or an unrecoverable operating-system problem

    Before reprovisioning, collect diagnostic information:

    ```bash title="Run on: compute node"
    journalctl -b --no-pager > /tmp/current-boot.log
    journalctl -b -1 --no-pager > /tmp/previous-boot.log
    systemctl --failed --no-pager > /tmp/failed-services.log
    ip address show > /tmp/ip-address.log
    ip route show > /tmp/ip-route.log
    findmnt > /tmp/findmnt.log
    ```

    Also save:

    - Output of `podman ps -a` and relevant container logs from the OIM
    - Output of `kubectl describe node <node_name>` for Kubernetes
    - Output of `scontrol show node <node_name>` for Slurm
    - Relevant Omnia and provisioning logs

    This information should be retained for root-cause analysis even if reprovisioning restores the node.

    **Validation**

    The recovery is complete only when all applicable checks succeed:

    ```bash title="Run on: OIM host"
    systemctl --failed --no-pager
    podman ps -a
    ochami smd service status
    ochami bss service status
    ```

    For Kubernetes:

    ```bash title="Run on: control node"
    kubectl get nodes
    kubectl get pods -A
    ```

    For Slurm:

    ```bash title="Run on: Slurm control node"
    sinfo -R
    sinfo -N -l
    ```

    Additionally, verify that:

    - No required OIM service is failed
    - Required Podman containers are running
    - All expected nodes are reachable
    - Shared filesystems are mounted and responsive
    - Cluster nodes have returned to their expected state
    - A representative workload can be submitted and completed successfully

    **Prevention**

    For subsequent planned startup operations:

    - Power on the OIM first
    - Wait until the operating system, omnia.target dependencies, required containers, networking, and shared storage are healthy
    - Power on the control or service nodes, if separate
    - Verify the cluster control plane
    - Power on compute nodes in manageable batches
    - Validate node registration and service health before starting production workloads

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

    Any Omnia playbook (prepare_oim.yml, local_repo.yml, provision.yml, telemetry.yml, upgrade.yml) terminates with a fatal Ansible error before completing. Typical error patterns include:

    - SSH connectivity failures: `UNREACHABLE! => {"msg": "Failed to connect to the host via ssh"}`
    - NFS mount or access errors: `mount.nfs: access denied`, `Stale file handle`, `Input/output error`
    - Package installation failures: `Failed to download metadata for repo`, `Cannot prepare internal mirrorlist`
    - Disk space exhaustion: `No space left on device`, `OSError: [Errno 28]`
    - DNS resolution failures: `Could not resolve host`, `Name or service not known`
    - Podman or container runtime failures: `Error: unable to start container`, `container storage is corrupted`
    - Permission or SELinux denials: `Permission denied`, `avc: denied`
    - Hardware or BMC unreachable: `ipmitool: Unable to establish session`, `Redfish connection refused`

??? note "Cause"

    Omnia playbooks depend on a healthy OIM operating environment. Common root causes include:

    - **Network**: Management NIC is down or misconfigured, VLAN or routing changed, firewall blocking required ports (SSH 22, Pulp 2225, S3, OpenCHAMI 8443), DNS unavailable
    - **Storage**: NFS server unreachable, NFS export changed or deleted, local disk full (/opt/omnia, /var/lib/containers, /var/lib/pulp), inode exhaustion
    - **Hardware**: Node powered off, BMC credentials changed, RAID degraded, NIC link down, GPU hardware failure
    - **Certificates**: TLS certificates expired (Pulp, OpenCHAMI, telemetry), system clock drift causing certificate validation failures
    - **Container runtime**: Podman storage corrupted after unclean shutdown, container images pruned or missing

??? note "Resolution"

    Run diagnostics on the OIM to isolate the failure domain:

    ```bash title="Run on: OIM host"
    # Check system health
    systemctl is-system-running
    systemctl --failed --no-pager

    # Check disk space (OIM critical paths)
    df -h /opt/omnia /var/lib/containers /var/lib/pulp /tmp

    # Check NFS availability
    findmnt -t nfs,nfs4
    showmount -e <nfs_server_ip>

    # Check network to compute nodes
    ping -c 2 <compute_node_ip>
    ip -brief address
    nmcli device status

    # Check DNS
    getent hosts <compute_node_hostname>
    getent hosts <oim_hostname>

    # Check Omnia containers
    podman ps -a --format "{{.Names}} {{.Status}}"

    # Check Omnia services
    systemctl status omnia.target --no-pager
    systemctl status openchami.target --no-pager

    # Check Pulp
    curl -sk https://localhost:2225/pulp/api/v3/status/ | head

    # Check clock (certificate-sensitive services fail with clock drift)
    timedatectl status

    # Check recent errors
    journalctl -b -p err..alert --no-pager | tail -50
    ```

    Resolve the identified failure domain:

    - **Network issues**: Restore connectivity, verify interface configuration, check firewall rules (`firewall-cmd --list-all`), verify DNS, and ensure management NIC is up with correct IP.
    - **Storage issues**: Free disk space (prune old container images with `podman image prune -a`, remove stale logs), restore NFS mounts (`mount <mount_point>`), verify NFS export permissions.
    - **Hardware issues**: Verify BMC reachability (`ipmitool -I lanplus -H <bmc_ip> -U <user> -P <pass> chassis status`), power-cycle affected node, replace failed hardware.
    - **Certificate issues**: Renew OpenCHAMI certificates (`sudo openchami-certificate-update update <hostname>.<domain>`), restart affected services, correct system clock.
    - **Container runtime issues**: If Podman storage is corrupted, reset with `podman system reset` (destructive — requires re-running prepare_oim.yml).

    After resolving the root cause, re-run only the failed playbook. Do not re-run the entire stack if only one playbook failed.

    **Tip**: Increase Ansible verbosity (`-vvv`) when re-running to capture detailed error output for root-cause analysis.
