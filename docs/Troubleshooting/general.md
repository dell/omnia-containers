
# General Issues


Common issues that affect the OIM, SSH connectivity, containers, and Ansible
Vault operations.

## Hostname changes after OIM reboot


???+ note "Symptom"

    After rebooting the OIM, the hostname reverts to `localhost` or a different
    value, causing Ansible playbooks and service connections to fail.

??? note "Cause"

    The OIM's hostname was set temporarily with `hostnamectl` but not persisted
    in `/etc/hostname`, or a DHCP-assigned hostname overrides the static
    setting on boot.

??? note "Resolution"

    1. Set the hostname permanently:

       ```bash
       hostnamectl set-hostname oim.example.com
       ```


    2. Verify it persisted in `/etc/hostname`:

       ```bash
       cat /etc/hostname
       ```


    3. Ensure the hostname is also in `/etc/hosts`:

       ```text
       127.0.0.1   localhost
       <oim_ip>    oim.example.com oim
       ```


    4. If DHCP is overriding the hostname, configure the DHCP client to preserve
       the static hostname by adding the following to
       `/etc/NetworkManager/conf.d/90-hostname.conf`:

       ```ini
       [main]
       hostname-mode=none
       ```


## SSH key mismatches


???+ note "Symptom"

    SSH connections from the OIM to cluster nodes fail with:

    ```text
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    @    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    ```


??? note "Cause"

    The target node was re-provisioned or re-imaged, generating new SSH host
    keys that conflict with the cached keys in `~/.ssh/known_hosts` on the
    OIM.

??? note "Resolution"

    1. Remove the stale key for the affected host:

       ```bash
       ssh-keygen -R <node_hostname_or_ip>
       ```


    2. Reconnect to accept the new key:

       ```bash
       ssh <node_hostname_or_ip>
       ```


    3. To prevent this issue across bulk re-provisions, clear all known_hosts
       entries for cluster nodes:

       ```bash
       # Remove entries for a range of IPs
       for i in $(seq 101 110); do
           ssh-keygen -R 10.5.0.$i
       done
       ```


## Container startup failures


???+ note "Symptom"

    One or more Podman containers fail to start after an OIM reboot, or
    `podman ps` shows containers in `Exited` or `Error` state.

??? note "Cause"

    Possible causes include:

    - The Podman service (`podman.socket`) did not start.
    - Containers were not configured to auto-restart.
    - Disk space exhaustion prevents container layer extraction.
    - Port conflicts with another service.

??? note "Resolution"

    1. Check the container status and error message:

       ```bash
       podman ps -a
       podman logs <container_name>
       ```


    2. Attempt a manual restart:

       ```bash
       podman start <container_name>
       ```


    3. If disk space is the issue:

       ```bash
       df -h /
       podman system prune --force
       ```


    4. If a port conflict is reported, identify the conflicting process:

       ```bash
       ss -tlnp | grep <port_number>
       ```


    5. If containers consistently fail after reboot, verify that Podman pods
       have auto-start enabled:

       ```bash
       podman generate systemd --name <pod_name> --files
       systemctl enable pod-<pod_name>.service
       ```


## `ssh omnia_core` fails after `sudo`


???+ note "Symptom"

    Running `ssh omnia_core` as a non-root user (or after `sudo su`) returns
    a connection error or permission denied:

    ```text
    Permission denied (publickey).
    ```


??? note "Cause"

    The `omnia_core` container is configured with SSH keys for the `root`
    user. When you use `sudo su` to become root, the SSH agent and key
    environment may not be inherited.

??? note "Resolution"

    Log in as `root` directly instead of using `sudo`:

    ```bash
    # Instead of:
    sudo su
    ssh omnia_core    # <-- fails

    # Do this:
    ssh root@<oim_ip>
    ssh omnia_core    # <-- works
    ```


    Alternatively, explicitly specify the SSH key:

    ```bash
    ssh -i /root/.ssh/id_rsa omnia_core
    ```


## Ansible Vault encrypted file issues


???+ note "Symptom"

    Ansible playbooks fail with:

    ```text
    ERROR! Attempting to decrypt but no vault secrets found
    ```


    Or you cannot view the contents of encrypted credential files.

??? note "Cause"

    The vault password was not provided when running the playbook, or the
    vault password file path is incorrect.

??? note "Resolution"

    1. **View an encrypted file** without editing:

       ```bash
       ansible-vault view input/credentials.yml
       ```


    2. **Edit an encrypted file:**

       ```bash
       ansible-vault edit input/credentials.yml
       ```


    3. **Run a playbook with vault password prompt:**

       ```bash
       ansible-playbook playbooks/omnia.yml --ask-vault-pass
       ```


    4. **Run a playbook with a vault password file:**

       ```bash
       ansible-playbook playbooks/omnia.yml --vault-password-file /root/.vault_pass
       ```


    5. If you have forgotten the vault password, you will need to recreate the
       credentials file. There is no way to recover an AES-256 encrypted vault
       without the original password:

       ```bash
       # Back up the old file
       cp input/credentials.yml input/credentials.yml.bak

       # Create a new encrypted file
       ansible-vault create input/credentials.yml
       ```


!!! info

    - [Log Management](../Operations/log_management.md) -- Where to find logs for deeper
      diagnosis.
    - [Oim Cleanup](../Operations/oim_cleanup.md) -- Full OIM reset if issues persist.
