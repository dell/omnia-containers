# Unattended OS Installation via iDRAC Virtual Media

## Overview

Omnia provides unattended OS installation on bare-metal nodes via iDRAC
Virtual Media. The playbook builds a custom ISO with an NFS-based Kickstart
reference, mounts it through the iDRAC virtual media interface, and boots
the target node for a fully automated install. The ISO is reusable across
multiple installations and only rebuilt when configuration changes.

!!! note

    Installations can be performed one server at a time. Run the playbook
    for each target node sequentially.


!!! info

    To manually install RHEL on an aarch64 build host before image building,
    refer to the [Prepare aarch64 Node](prepare_aarch64_node.md) procedure.

The `install_os_arm_node.yml` orchestrator reads configuration from
`iso_config.yml`, fetches credentials from `omnia_config_credentials.yml`,
and drives the OS installation end-to-end.

## Prerequisites

- The target node is a Dell PowerEdge server with iDRAC 9 or later.
- A RHEL 10.x source ISO (Server with GUI) is available inside the
  `omnia_core` container at `/opt/omnia/`.
- An NFS share is configured and maps to `/opt/omnia`. The NFS server
  must be accessible from both the OIM and the target node's iDRAC.
- BMC network connectivity exists from the OIM to the target node's iDRAC.
- The [Deploy Omnia Core](deploy_omnia_core.md) procedure is complete
  (with NFS share option selected during `omnia.sh --install`).
- The [Configure Credentials](configure_credentials.md) procedure is
  complete. The `omnia_config_credentials.yml` file must contain:

    ```yaml title="File: /opt/omnia/input/project_default/omnia_config_credentials.yml"
    bmc_username: "<idrac_username>"
    bmc_password: "<idrac_password>"
    provision_password: "<os_root_password>"
    ```

- **iDRAC Boot Order Configuration**: The target node's BIOS boot order must have **Remote File Share 1** and **Remote File Share 2** (Virtual Media) configured as the first and second boot priorities, respectively, before hard drive boot. This is critical for the server to boot from the mounted ISO during installation.

- **Virtual Media Cleanup**: All existing virtual media must be disconnected from the iDRAC before starting the installation to prevent boot conflicts. Verify no ISOs are currently mounted via the iDRAC web console or use the eject command in the playbook.

## Procedure

### Install OS on an aarch64 node

This is the primary method for installing RHEL on an aarch64 build node
before building aarch64 cluster images.

1. **Place the source ISO inside the container**:

    ```bash title="Run on: OIM host"
    cp RHEL-10.0-*-aarch64-dvd1.iso <oim_shared_path>/omnia
    ```

    Verify the ISO is accessible:

    ```bash title="Run on: omnia_core container"
    ls -lh /opt/omnia/*.iso
    ```

2. **Configure `iso_config.yml`**:

    Edit the input file:

    ```bash title="Run on: omnia_core container"
    vi /opt/omnia/input/project_default/iso_config.yml
    ```

    ```yaml title="File: /opt/omnia/input/project_default/iso_config.yml"
    iso_source_path: "/opt/omnia/RHEL-10.0-20250410.6-aarch64-dvd1.iso"
    iso_target_directory: "/opt/omnia/iso_output"
    target_bmc_ip: "100.10.11.12"
    hostname: "os-node2"
    target_node_ip: "172.10.5.28"

    # Optional: Force rebuild
    rebuild_iso: false
    ```

3. **Run the ARM orchestrator playbook**:

    ```bash title="Run on: omnia_core container"
    cd /omnia/utils/install_os_arm_node
    ansible-playbook install_os_arm_node.yml
    ```

    To use a custom config path:

    ```bash title="Run on: omnia_core container"
    ansible-playbook install_os_arm_node.yml \
      -e "iso_config_path=/custom/path/iso_config.yml"
    ```

    To suppress interactive prompts:

    ```bash title="Run on: omnia_core container"
    ansible-playbook install_os_arm_node.yml \
      -e "silent_install=true"
    ```

The playbook performs the following steps automatically:

1. Validates that no upgrade is in progress.
2. Loads and validates `iso_config.yml`.
3. Fetches BMC and OS credentials from `omnia_config_credentials.yml`.
4. Validates target node parameters (`target_bmc_ip`, `hostname`, `target_node_ip`) from `iso_config.yml`.
5. Builds a custom ISO with NFS Kickstart reference (if not already built).
6. Mounts the ISO via iDRAC Virtual Media, sets boot override to virtual
   CD-ROM, and power-cycles the node.
7. Waits for OS installation to complete and verifies SSH connectivity.

!!! note

    The ARM orchestrator uses `provision_password` from
    `omnia_config_credentials.yml` as the OS root password. This is the
    same password configured during the
    [Configure Credentials](configure_credentials.md) procedure.



### `iso_config.yml` parameter reference

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `target_bmc_ip` | Yes | -- | Target node BMC/iDRAC IP address. |
| `hostname` | Yes | -- | Hostname for the installed node. |
| `target_node_ip` | Yes | -- | Target node OS IP address to set. |
| `iso_source_path` | Yes | -- | Path to the source ISO inside the container. |
| `iso_target_directory` | No | `/opt/omnia/iso_output` | Output directory for the custom ISO. |
| `nfs_share_path` | No | Auto-detected | NFS share in `server:/path` format. Auto-detected from the `/opt/omnia` mount if omitted. |
| `netmask` | No | `255.255.255.0` | Network mask for Kickstart configuration. |
| `gateway` | No | -- | Default gateway for the installed node. |
| `dns` | No | -- | DNS server for the installed node. |
| `install_disk` | No | Auto-detect | Target disk device (e.g., `sda`, `nvme0n1`). |
| `rebuild_iso` | No | `false` | Force ISO rebuild even if a custom ISO already exists. |
| `force_reinstall` | No | `false` | Proceed with installation even if the target node is already reachable. |
| `silent_install` | No | `false` | Suppress all interactive prompts. |
| `kickstart_file` | No | -- | Path to a user-provided Kickstart file. Overrides template-based generation. |
| `iso_source_checksum` | No | -- | SHA-256 checksum for source ISO verification. |
| `embed_kickstart` | No | `true` | Embed Kickstart file in ISO (`true`) or host on NFS share (`false`). |
| `network_device` | No | `link` (auto-detect) | Network interface name for static IP configuration. |


!!! warning

    The playbook erases all data on the target node's install disk. Confirm
    the target BMC IP and hostname before proceeding.

!!! note

    The `os_root_password` is hashed to SHA-512 internally by the playbook.
    Do not pre-hash the password.

## Verification

1. **Verify the custom ISO was built**:

    ```bash title="Run on: omnia_core container"
    ls -lh /opt/omnia/iso_output/
    ```

2. **Verify the node is reachable after installation**:

    ```bash title="Run on: omnia_core container"
    ssh <target_node_ip>
    ```

3. **Verify the correct OS and architecture**:

    ```bash title="Run on: target node"
    cat /etc/redhat-release
    uname -m
    ```

4. **Verify network configuration**:

    ```bash title="Run on: target node"
    hostname
    ip addr show
    ip route show default
    ```

## Next Steps

- [Build Cluster Images](build_cluster_images.md) -- Build aarch64 diskless
  images using the installed node.


## Troubleshooting

- **`iso_config.yml` not found**:

    ```text
    FATAL: iso_config.yml not found at '/opt/omnia/input/project_default/iso_config.yml'
    ```

    Copy the template from `/omnia/utils/install_os_arm_node/input/iso_config.yml`
    or provide a custom path via `-e "iso_config_path=/path/to/iso_config.yml"`.

- **NFS share not accessible**:

    ```text
    FATAL: NFS share path not available. Cannot auto-detect NFS mount for /opt/omnia
    ```

    Verify the NFS mount inside the container with `mount | grep /opt/omnia`.
    Alternatively, specify `nfs_share_path` manually in `iso_config.yml` using
    the `server:/path` format (e.g., `192.168.1.100:/mnt/nfs/omnia`).

- **Invalid NFS share path format**:

    ```text
    FATAL: Invalid nfs_share_path format. Expected 'server:/path'
    ```

    Provide the NFS share in `server:/path` format. Both the server IP and
    the export path are required (e.g., `192.168.1.100:/mnt/nfs/omnia`).

- **iDRAC authentication failed**:

    ```text
    FAILED: iDRAC NOT reachable at <bmc_ip> (HTTP 401)
    ```

    Verify credentials in `omnia_config_credentials.yml` with
    `ansible-vault view`. Check that the BMC IP is reachable with
    `ping <bmc_ip>` and the iDRAC user has administrator privileges.

- **ISO rebuild fails with xorriso error**:

    ```text
    xorriso : FAILURE : -indev differs from -outdev and -outdev media holds non-zero data
    ```

    Set `rebuild_iso: true` in `iso_config.yml` or manually remove the
    existing ISO from `/opt/omnia/iso_output/`.

- **Target node does not boot from virtual media**: Confirm BIOS boot
  order includes virtual media. Verify the iDRAC Virtual Media service
  is enabled in iDRAC settings.

- **SSH verification fails after installation**:

    ```text
    FAILED: SSH to <target_node_ip> failed after installation
    ```

    Verify the node is powered on, the `target_node_ip` in `iso_config.yml`
    is correct, and network connectivity exists. Manually SSH with
    `ssh root@<target_node_ip>` using the `provision_password`.

- **`provision_password` is not defined**:

    ```text
    FATAL: provision_password is not defined
    ```

    Verify `omnia_config_credentials.yml` contains `bmc_username`,
    `bmc_password`, and `provision_password`. Re-encrypt if needed with
    `ansible-vault encrypt`.

- **Static IP not assigned after installation**:

    ```text
    Node installed but has DHCP IP instead of static IP
    ```

    Verify `network_device` is set correctly in `iso_config.yml`. Check the generated Kickstart file at `/opt/omnia/iso_output/kickstart.cfg` to confirm it contains `--device=eno1` (or your specified device) instead of `--device=link`. If incorrect, update `iso_config.yml` with the correct interface name, set `rebuild_iso: true`, and re-run the playbook.

    To identify the correct network device name, check similar nodes in your cluster with `ip link show` or refer to the Dell PowerEdge documentation for your server model.

- **Server boots from hard drive instead of ISO**:

    ```text
    Installation does not start; server boots to existing OS or BIOS
    ```

    Verify the iDRAC BIOS boot order has **Remote File Share 1** and **Remote File Share 2** (Virtual Media) as the first and second boot priorities. Access iDRAC web console → System → BIOS Settings → Boot Settings and configure the boot order. Save changes and reboot the server.

    Disconnect all existing virtual media from the iDRAC before running the playbook. Access iDRAC web console → Console/Media → Virtual Media and eject/disconnect any mounted ISOs. Alternatively, the playbook will attempt to eject existing media automatically, but manual cleanup is recommended.
