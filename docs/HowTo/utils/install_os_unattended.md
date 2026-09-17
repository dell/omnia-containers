# Unattended OS Installation via iDRAC Virtual Media

## Overview

The utils `install_os` workflow installs RHEL on one bare-metal node through
iDRAC Virtual Media. It validates the installation configuration, collects and
encrypts credentials, creates a custom ISO with Kickstart, attaches that ISO to
the target BMC, power-cycles the server, and optionally verifies SSH access to
the installed operating system.

The same workflow supports `x86_64` and `aarch64`. The target architecture can
be configured explicitly or detected from the source ISO filename.

Set `target_architecture` explicitly for repeatable builds. Automatic detection
requires the source ISO filename to contain `x86_64` or `aarch64`.

!!! note

    The workflow installs one server at a time. For multiple servers, update
    the target-node values and run the workflow separately for each server.

!!! warning

    The generated Kickstart clears and repartitions the configured
    `install_disk`. Confirm the BMC address, operating-system address, and disk
    name before starting the deployment.

## Prerequisites

- Complete the [OIM setup](../main/setup_oim.md) and initialize the utils
  module.
- Confirm that the target server and iDRAC version are supported. See the
  [Servers](../../Reference/SupportMatrix/servers.md) and
  [Software Compatibility Matrix](../../Reference/software_compatibility_matrix.md).
- Place a RHEL 10 source ISO on a filesystem accessible to the OIM.
- Provide an NFS destination in `server:/export/path/file.iso` format. The OIM
  must be able to mount the export, and the target BMC must be able to access it.
- Configure the target server for UEFI boot. The workflow requests a one-time
  boot from the virtual CD presented through iDRAC.
- Configure the target node's BIOS boot order so that `Remote File Share 1`
  and `Remote File Share 2` (Virtual Media) are the first and second boot
  priorities, respectively, ahead of the hard drive. This is required for the
  server to boot from the mounted ISO during installation.
- For a Belton `aarch64` node, ensure that `Virtual Network File` is available
  in the UEFI boot sequence. This option may appear only after virtual media is
  connected during the installation workflow. Disable the other UEFI boot
  options when required so that `Virtual Network File` is selected first.
- Ensure the OIM can reach the target BMC through HTTPS and the installed node
  through SSH.
- Ensure the target BMC supports the Redfish operations used by the iDRAC
  virtual-media modules.
- Reserve the administrative IP address that Kickstart will assign to the
  installed node. Ensure that it is reachable from the OIM.
- Identify the target installation disk and network interface. Device names
  vary by server model and architecture; verify them on equivalent hardware or
  through the server inventory before starting the installation.
- Create the SSH public key configured by `ssh_public_key_path`. The default is
  `/root/.ssh/id_rsa.pub`.

The first installation run prompts for `bmc_username`, `bmc_password`, and
`os_root_password`. The workflow stores them in an Ansible Vault-encrypted
`install_os_credentials.yml` file in the utils project input directory.

!!! note

    Enter the OS root password as plain text at the protected prompt. The
    workflow hashes it before adding it to the generated Kickstart file; do not
    pre-hash the password.

## Procedure

### Install the operating system

1. Initialize the Utils module so that its input templates and dependencies are
   available:

    ```bash title="Run from: <omnia-repository>/src/main"
    ./omnia.sh -i utils
    ```

    If the shared Omnia environment has not been created, run `./omnia.sh -s`
    first.

2. Edit the staged configuration:

    ```bash title="Run on: OIM host"
    vi <OMNIA_DATA_PATH>/utils/input/<project>/install_os_config.yml
    ```

    Replace `<project>` with the value of `OMNIA_PROJECT_NAME`.

3. Configure the source ISO, NFS destination, and target node. For example:

    ```yaml title="File: <OMNIA_DATA_PATH>/utils/input/<project>/install_os_config.yml"
    source_iso_path: "/opt/omnia/iso/RHEL-10.0-x86_64-dvd.iso"
    source_iso_checksum: ""
    custom_iso_path: "192.0.2.10:/exports/omnia/RHEL-10.0-x86_64-omnia.iso"

    kickstart_delivery_method: embedded
    kickstart_file: ""
    kickstart_template: rhel10

    target_bmc_ip: "192.0.2.21"
    target_hostname: "compute-01"
    target_admin_ip: "192.0.2.31"
    target_architecture: "x86_64"

    network_device: "eno1"
    netmask: "255.255.255.0"
    gateway: "192.0.2.1"
    dns_server: "192.0.2.2"
    ssh_public_key_path: "/root/.ssh/id_rsa.pub"
    install_disk: "sda"
    timezone: "UTC"

    rebuild_iso: false
    force_reinstall: false
    ssh_verify_enabled: true
    ssh_verify_retries: 60
    ssh_verify_delay: 30
    ```

    The ISO creation workflow validates `custom_iso_path` before accessing the
    NFS share. Use a valid hostname or IPv4 address, an absolute NFS path, and
    an ISO filename containing only letters, numbers, underscores, hyphens,
    and periods. The filename must end with lowercase `.iso`. Do not include
    `..`, wildcards, or shell metacharacters.

    Replace the example addresses and paths with values for the deployment.

    For an `aarch64` target, use an `aarch64` source ISO and custom ISO name,
    and set the architecture explicitly. The remaining parameters use the same
    workflow and must match the target hardware and network:

    ```yaml title="AArch64-specific values"
    source_iso_path: "/opt/omnia/iso/RHEL-10.0-aarch64-dvd.iso"
    custom_iso_path: "192.0.2.10:/exports/omnia/RHEL-10.0-aarch64-omnia.iso"
    target_architecture: "aarch64"
    ```

    For a Belton `aarch64` node, also configure these platform-specific
    values:

    ```yaml title="Belton-specific values"
    gateway: "<gateway>"
    network_device: "enP6s3f0np0"
    install_disk: "nvme0n1"
    ```

    These values override the general workflow defaults. Set
    `rebuild_iso: true` after changing any Kickstart-backed value. Set
    `force_reinstall: true` only when intentionally reinstalling a node on
    which an operating system is already installed.

    !!! important

        Do not copy the example `network_device` or `install_disk` values
        without verifying them on the target platform. If you change a
        Kickstart-backed setting after the custom ISO has been created, set
        `rebuild_iso: true` for the next run. Set `force_reinstall: true` only
        when intentionally reimaging a node that is already reachable through
        SSH.

4. Run the complete workflow:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run utils --tags install_os
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/utils
        ansible-playbook playbooks/utils.yml --tags install_os
        ```

    Respond to the credential prompts on the first run. Later runs reuse the
    encrypted credential file unless it is removed by the installation cleanup
    workflow.

The workflow performs the following operations:

1. Validates the fields required for ISO build and deployment.
2. Loads or collects the BMC and OS root credentials and injects the OIM public
   key into Kickstart.
3. Verifies the source ISO and its SHA-256 checksum when one is supplied.
4. Installs required ISO tools when they are absent.
5. Creates the custom ISO unless it already exists and `rebuild_iso` is false.
6. Attaches the NFS-hosted ISO through iDRAC Virtual Media and requests a
   one-time virtual-CD boot.
7. Power-cycles the node and, when enabled, waits for SSH to become available.
8. Writes installation and utils status files for the active project.

The deployment stage attempts to eject existing virtual media before mounting
the custom ISO and ejects it again after installation. If the server does not
boot from the ISO, inspect the iDRAC Virtual Media and boot settings for stale
media or an unsupported virtual-CD boot target.

### Run individual build or deployment stages

For troubleshooting or controlled operation, run an individual stage through
the Utils domain launcher:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags generate_ks
    ./omnia.sh --run utils --tags build_iso
    ./omnia.sh --run utils --tags deploy
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils
    ansible-playbook playbooks/utils.yml --tags generate_ks
    ansible-playbook playbooks/utils.yml --tags build_iso
    ansible-playbook playbooks/utils.yml --tags deploy
    ```

Use the stage that matches the required operation:

| Tag | When to use it |
| --- | --- |
| `generate_ks` | Generate the Kickstart file for review or troubleshooting without building an ISO or deploying it to a server. |
| `build_iso` | Build the custom ISO without attaching it to the target server or starting the OS installation. Use this option to prepare the ISO for a later deployment. If the ISO already exists and must be replaced, set `rebuild_iso: true`. |
| `deploy` | Reuse an existing ISO and install the operating system without rebuilding the ISO. The ISO specified in `custom_iso_path` is used for the operating system installation. |

The same stages can be invoked directly from the utils collection after
activating the Omnia environment:

```bash title="Run on: OIM host"
ansible-playbook playbooks/install_os.yml --tags credentials
ansible-playbook playbooks/install_os.yml --tags generate_ks
ansible-playbook playbooks/install_os.yml --tags build_iso
ansible-playbook playbooks/install_os.yml --tags deploy
```

`credentials` collects credentials only, `generate_ks` writes the Kickstart
file without building an ISO, `build_iso` builds the custom media, and `deploy`
uses an existing custom ISO.

The `build_iso` and `deploy` stages write `install_os_status.yml`. The
`credentials` and `generate_ks` stages do not write that installation status
file.

### `install_os_config.yml` parameter reference

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `source_iso_path` | Build and Kickstart generation | -- | Local path to the source ISO. |
| `source_iso_checksum` | No | Empty | Optional SHA-256 checksum for the source ISO. |
| `custom_iso_path` | Build, Kickstart generation, and deployment | -- | NFS URI for the custom ISO and generated artifacts in `server:/path/file.iso` format. |
| `kickstart_delivery_method` | No | `embedded` | Use `embedded` or `nfs` Kickstart delivery. |
| `kickstart_file` | No | Empty | Optional user-provided Kickstart file. Missing root password and SSH-key directives are injected. |
| `kickstart_template` | No | `rhel10` | Built-in Kickstart template name. |
| `target_bmc_ip` | Deployment | -- | Target BMC/iDRAC IP address. |
| `target_hostname` | Build and Kickstart generation | -- | Hostname written by Kickstart. The current validator does not reject an empty value, but the generated static-network configuration requires one. |
| `target_admin_ip` | Build, Kickstart generation, and deployment | -- | Static OS address written by Kickstart and used as the post-install SSH-verification target. |
| `target_architecture` | No | Detected from ISO name | `x86_64` or `aarch64`. Set it explicitly when the ISO filename does not contain the architecture. |
| `network_device` | No | First active link | Network interface used by Kickstart. For a Belton `aarch64` node, use `enP6s3f0np0`. |
| `netmask` | No | `255.255.255.0` | Static network mask. |
| `gateway` | No | Empty | Static default gateway. Set this explicitly for a Belton `aarch64` node. |
| `dns_server` | No | Empty | DNS server used by Kickstart. |
| `ssh_public_key_path` | No | `/root/.ssh/id_rsa.pub` | Public key injected for root SSH access. |
| `install_disk` | No | `sda` | Disk erased and used for installation. For a Belton `aarch64` node, use `nvme0n1`. |
| `timezone` | No | `UTC` | Installed-system timezone. |
| `rebuild_iso` | No | `false` | Rebuild an existing custom ISO. Set this to `true` after changing Kickstart-backed configuration. |
| `force_reinstall` | No | `false` | Continue when the target OS address already accepts SSH. Set this to `true` only when intentionally reinstalling a node. |
| `ssh_verify_enabled` | No | `true` | Verify SSH after the BMC deployment operation. |
| `ssh_verify_retries` | No | `60` | Multiplier used with `ssh_verify_delay` to calculate the SSH wait timeout. |
| `ssh_verify_delay` | No | `30` | Initial delay in seconds before checking SSH; also used to calculate the total timeout. |

## Verification

1. Confirm that the custom ISO, `kickstart.ks`, and
   `install_os_manifest.yml` exist at the NFS destination directory.

2. Review the generated project status:

    ```bash title="Run on: OIM host"
    cat "$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/install_os_status.yml"
    ```

3. When SSH verification is enabled, connect to the installed node:

    ```bash title="Run on: OIM host"
    ssh root@<target_admin_ip>
    ```

4. Verify the operating system and architecture:

    ```bash title="Run on: target node"
    cat /etc/redhat-release
    uname -m
    ```

## Next steps

- [Build Cluster Images](../image_build_manager/build_images.md) -- Use the
  installed node where required by the image-building workflow.
- [Clean up Utils](cleanup_utils.md) -- Remove temporary installation
  artifacts or reset the stored installation credentials.

## Troubleshooting

- **`install_os_config.yml` is not found**: Run `./omnia.sh -i utils` and edit
  the staged file under `<OMNIA_DATA_PATH>/utils/input/<project>/`.
- **The source ISO is rejected**: Confirm `source_iso_path` exists and that
  `source_iso_checksum`, when configured, is the correct SHA-256 value.
- **The custom ISO path is rejected or cannot be resolved**: Confirm
  `custom_iso_path` uses `server:/absolute/path/file.iso` format, satisfies the
  filename and path restrictions above, and identifies an NFS export mountable
  from the OIM.
- **Architecture detection fails**: Set `target_architecture` explicitly to
  `x86_64` or `aarch64`; do not rely on detection when the ISO filename omits
  the architecture.
- **The target does not boot from the custom ISO**: Confirm that the server is
  configured for UEFI boot and that iDRAC Virtual Media is enabled. In the
  iDRAC console, disconnect any stale virtual media and confirm that a virtual
  CD is available as a one-time boot target.
- **The installed node does not use the expected static IP**: Verify
  `network_device`, `target_admin_ip`, `netmask`, `gateway`, and `dns_server`.
  Rebuild the custom ISO after correcting any Kickstart-backed value.
- **The target is already reachable**: Leave `force_reinstall: false` to protect
  an installed node, or set it to `true` only after confirming that the target
  may be reimaged.
- **SSH verification times out**: Verify the configured administrative IP,
  network interface, gateway, and firewall path. Increase
  `ssh_verify_retries` or `ssh_verify_delay` when installation requires longer.
