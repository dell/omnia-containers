# install_os_config.yml

This file configures the Utils unattended OS installation workflow. The same
file supports ISO creation, kickstart generation, deployment through iDRAC
virtual media, and post-install SSH verification.

The workflow supports `x86_64` and `aarch64` target architectures.

!!! note

    For aarch64 architecture platforms, limited validation has been performed on early access systems.

## Location

```text
$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/install_os_config.yml
```

## ISO and kickstart parameters

| Parameter | Source value | Description |
|---|---|---|
| `source_iso_path` | Empty | Local path to the original distribution ISO; required for build and kickstart-generation modes. |
| `source_iso_checksum` | Empty | Optional SHA-256 checksum for the source ISO. |
| `custom_iso_path` | Empty | NFS URI in `server:/absolute/path/file.iso` format; required for build, Kickstart generation, and deployment modes. |
| `kickstart_delivery_method` | `embedded` | `embedded` or `nfs`. |
| `kickstart_file` | Empty | Optional user-provided kickstart file. |
| `kickstart_template` | `rhel10` | Built-in template used when `kickstart_file` is empty. |

During ISO creation, `custom_iso_path` must meet these requirements:

- The server must be a valid hostname or IPv4 address.
- The NFS path must be absolute and must not contain `..`, wildcards, or shell metacharacters.
- The ISO filename may contain letters, numbers, underscores, hyphens, and periods. It must end with lowercase `.iso` and must not contain `..`.

## Target-node parameters

| Parameter | Source value | Description |
|---|---|---|
| `target_bmc_ip` | Empty | iDRAC/BMC IPv4 address; required for deployment. |
| `target_hostname` | Empty | Hostname assigned by Kickstart; required for a usable generated static-network configuration. |
| `target_admin_ip` | Empty | Admin-network IP assigned by Kickstart and used for SSH verification; required for build, Kickstart generation, and deployment. |
| `target_architecture` | Empty | `x86_64` or `aarch64`; set this explicitly when the source ISO filename does not contain the architecture. |
| `network_device` | Empty | Installation NIC; empty uses the first active link. For a Belton `aarch64` node, use `enP6s3f0np0`. |
| `netmask` | `255.255.255.0` | Target network mask. |
| `gateway` | Empty | Target default gateway. Set this explicitly for a Belton `aarch64` node. |
| `dns_server` | Empty | Target DNS server. |
| `ssh_public_key_path` | Empty | Public key injected into kickstart; empty defaults to `/root/.ssh/id_rsa.pub`. |
| `install_disk` | `sda` | Target installation disk. For a Belton `aarch64` node, use `nvme0n1`. |
| `timezone` | `UTC` | Installed operating-system timezone. |

## Execution controls

| Parameter | Source value | Description |
|---|---|---|
| `rebuild_iso` | `false` | Rebuild the custom ISO when it already exists. Set this to `true` after changing Kickstart-backed configuration. |
| `force_reinstall` | `false` | Reinstall even when the target is reachable over SSH. Set this to `true` only for an intentional reinstall. |
| `ssh_verify_enabled` | `true` | Verify the installed node using SSH. |
| `ssh_verify_retries` | `60` | Multiplier used with `ssh_verify_delay` to calculate the SSH wait timeout. |
| `ssh_verify_delay` | `30` | Initial delay before the SSH check and multiplier used in the total timeout calculation, in seconds. |

## Usage example

```yaml title="File: /opt/omnia/utils/input/project_default/install_os_config.yml"
source_iso_path: "/root/RHEL-10.0-x86_64-dvd.iso"
source_iso_checksum: ""
custom_iso_path: "192.0.2.20:/exports/omnia/RHEL-10.0-x86_64-omnia.iso"

kickstart_delivery_method: embedded
kickstart_file: ""
kickstart_template: rhel10

target_bmc_ip: "192.0.2.101"
target_hostname: "compute-01"
target_admin_ip: "192.0.2.201"
target_architecture: "x86_64"
network_device: ""
netmask: "255.255.255.0"
gateway: "192.0.2.1"
dns_server: "192.0.2.53"
ssh_public_key_path: "/root/.ssh/id_rsa.pub"
install_disk: "sda"
timezone: "UTC"

rebuild_iso: false
force_reinstall: false
ssh_verify_enabled: true
ssh_verify_retries: 60
ssh_verify_delay: 30
```

The credential workflow handles the root and iDRAC credentials separately;
do not store passwords in this file.

## Related documentation

- [Install an OS unattended](../../HowTo/utils/install_os_unattended.md)
- [Utils contract](../domain_contracts/utils_contract.md)
