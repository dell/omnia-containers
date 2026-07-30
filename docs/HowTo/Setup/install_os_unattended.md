# Unattended OS Installation via iDRAC

## Overview

Omnia provides unattended OS installation on bare-metal nodes via iDRAC
Virtual Media. The playbook repacks a source ISO with a Kickstart
configuration, mounts it through the iDRAC virtual media interface, and
boots the target node for a fully automated install.

Two playbooks are available:

- **`install_os_arm_node.yml`** -- Orchestrator for aarch64 nodes. Reads
  configuration from `iso_config.yml`, fetches credentials automatically,
  validates ARM-specific parameters, and calls the generic installer.
- **`install_os.yml`** -- Generic installer for any architecture. Requires
  all parameters via extra vars or encrypted credentials file. Used
  directly for x86_64 nodes.

## Prerequisites

- The target node has a Dell iDRAC with Virtual Media support.
- A RHEL 10.x source ISO is pre-placed on the OIM host.
- An NFS share is configured and maps to `/opt/omnia` on the OIM host.
- The OIM host has network connectivity to the target node's BMC/iDRAC IP
  and admin IP.
- The [Deploy Omnia Core](deploy_omnia_core.md) procedure is complete
  (with NFS share option selected during `omnia.sh --install`).
- The [Prepare OIM](prepare_oim.md) procedure is complete.

## Procedure

### Install OS on an aarch64 node

This is the primary method for installing RHEL on an aarch64 build node
before building aarch64 cluster images.

1. **Configure `iso_config.yml`**:

    Edit the ISO configuration file with the aarch64 ISO path and target
    node details:

    ```bash title="Run on: omnia_core container"
    vi /opt/omnia/input/project_default/iso_config.yml
    ```

    Provide the path to the RHEL 10.x aarch64 Server with GUI ISO and
    the target node parameters (BMC IP, admin IP, hostname, static IP).

2. **Run the ARM orchestrator playbook**:

    ```bash title="Run on: omnia_core container"
    cd /omnia/utils/install_os_arm_node
    ansible-playbook install_os_arm_node.yml
    ```

    To use a custom config path:

    ```bash title="Run on: omnia_core container"
    ansible-playbook install_os_arm_node.yml \
      -e "iso_config_path=/custom/path/iso_config.yml"
    ```

The playbook performs the following steps automatically:

1. Validates that no upgrade is in progress.
2. Loads and validates `iso_config.yml`.
3. Fetches BMC and OS credentials via the Omnia credential utility.
4. Validates ARM-specific configuration and fetches target parameters.
5. Calls the generic `install_os.yml` to repack the ISO with a Kickstart
   configuration and deliver it via iDRAC Virtual Media.

!!! note

    The ARM orchestrator uses `provision_password` from the Omnia
    credential store as the OS root password. This is the same password
    configured during the [Configure Credentials](configure_credentials.md)
    procedure.

### Install OS on an x86_64 node

For x86_64 nodes, call the generic `install_os.yml` playbook directly
with all required parameters as extra vars.

1. **Run the install playbook**:

    ```bash title="Run on: omnia_core container"
    cd /omnia/utils/install_os
    ansible-playbook install_os.yml \
      -e "iso_source_path=/path/to/rhel10-x86_64.iso" \
      -e "target_bmc_ip=<idrac_ip>" \
      -e "target_node_ip=<admin_ip>" \
      -e "iso_nfs_share=<nfs_share_path>" \
      -e "os_root_password=<root_password>" \
      -e "ks_ssh_public_key='$(cat ~/.ssh/id_rsa.pub)'" \
      -e "ks_hostname=<hostname>" \
      -e "ks_static_ip=<static_ip>"
    ```

    Alternatively, use an encrypted credentials file:

    ```bash title="Run on: omnia_core container"
    ansible-playbook install_os.yml \
      -e "iso_source_path=/path/to/rhel10-x86_64.iso" \
      -e "target_bmc_ip=<idrac_ip>" \
      -e "target_node_ip=<admin_ip>" \
      -e "iso_nfs_share=<nfs_share_path>" \
      -e "ks_ssh_public_key='$(cat ~/.ssh/id_rsa.pub)'" \
      -e "ks_hostname=<hostname>" \
      -e "ks_static_ip=<static_ip>" \
      -e "encrypted_credentials_file=/opt/omnia/input/project_default/os_install_credentials.yml" \
      -e "vault_password_file=/opt/omnia/input/project_default/.os_install_credentials_key"
    ```

### Variable reference

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `iso_source_path` | Yes | -- | Path to the source ISO on the OIM host. |
| `target_bmc_ip` | Yes | -- | BMC/iDRAC IP address of the target node. |
| `target_node_ip` | Yes | -- | Admin IP address of the target node (used for verification). |
| `iso_nfs_share` | Yes | -- | NFS share path that maps to `/opt/omnia`. |
| `os_root_password` | Yes | -- | Root password for the installed OS (hashed internally to SHA-512). |
| `ks_ssh_public_key` | Yes | -- | SSH public key to inject into the installed OS. |
| `ks_hostname` | Yes | -- | Hostname assigned to the installed node. |
| `ks_static_ip` | Yes | -- | Static IP address assigned to the installed node. |
| `iso_config_path` | No | `/opt/omnia/input/project_default/iso_config.yml` | Path to `iso_config.yml` (ARM orchestrator only). |
| `iso_source_checksum` | No | -- | SHA-256 checksum for source ISO verification. |
| `iso_target_directory` | No | `/opt/omnia/iso_output` | Output directory for the repacked ISO. |
| `kickstart_file` | No | -- | Path to a user-provided Kickstart file. Overrides template-based generation. |
| `kickstart_template` | No | `rhel10` | Jinja2 template name used for Kickstart generation. |
| `ks_install_disk` | No | auto-detect | Target disk for OS installation. |
| `force_reinstall` | No | `false` | Proceed with installation even if the target node is already reachable. |
| `silent_install` | No | `false` | Suppress all interactive prompts (generic playbook only). |
| `rebuild_iso` | No | `false` | Force ISO rebuild even if a repacked ISO already exists. |

!!! warning

    The playbook erases all data on the target node's install disk. Confirm
    the target BMC IP and hostname before proceeding.

!!! note

    The `os_root_password` is hashed to SHA-512 internally by the playbook.
    Do not pre-hash the password.

## Verification

1. **Verify the node is reachable after installation**:

    ```bash title="Run on: omnia_core container"
    ssh <target_node_ip>
    ```

2. **Verify the correct OS was installed**:

    ```bash title="Run on: target node"
    cat /etc/os-release
    uname -m
    ```

## Next Steps

- [Build Cluster Images](build_cluster_images.md) -- Build aarch64 or
  x86_64 diskless images using the installed node.
- [Prepare aarch64 Node](prepare_aarch64_node.md) -- Use this playbook to
  install RHEL on an aarch64 build host before image building.

## Troubleshooting

- **`iso_config.yml` not found**: Verify the file exists at the default
  path `/opt/omnia/input/project_default/iso_config.yml` or provide a
  custom path via `-e "iso_config_path=/path/to/iso_config.yml"`.
- **ARM validation fails**: Confirm the source ISO is a RHEL 10.x
  aarch64 Server with GUI ISO and all target node details in
  `iso_config.yml` are correct.
- **Playbook fails with "Missing mandatory parameters"**: Verify all
  required variables are provided via extra vars, encrypted credentials
  file, or `iso_config.yml`. Run with `-v` for detailed output.
- **ISO validation fails**: Confirm the ISO path is correct and the file
  is not corrupted. If `iso_source_checksum` is provided, verify it
  matches the SHA-256 checksum of the source ISO.
- **iDRAC Virtual Media mount fails**: Verify BMC/iDRAC credentials are
  correct and the iDRAC firmware supports Virtual Media. Check network
  connectivity between the OIM host and the target BMC IP.
- **Target node does not boot from virtual media**: Confirm BIOS boot
  order includes virtual media. Verify the iDRAC Virtual Media service
  is enabled.
- **Installation completes but node is unreachable**: Check that
  `ks_static_ip` and `ks_hostname` are correct and that the admin network
  is configured. Verify firewall rules on the installed node.
