# Configure Additional Cloud-Init

Omnia allows administrators to inject custom cloud-init directives into the node provisioning pipeline. This enables boot-time customization such as writing configuration files or running setup commands on cluster nodes without modifying platform-managed templates.

## Overview

The additional cloud-init feature supports two scopes:

- **common**: Directives applied to all provisioned nodes.
- **groups**: Directives applied only to nodes belonging to a specific functional group as defined in the PXE mapping file.

Both scopes support the following cloud-init directives:

| Directive | Description |
|-----------|-------------|
| `write_files` | Create or append files on the node at boot time. Each entry must include a `path`. |
| `runcmd` | Run shell commands during the final stage of cloud-init. Each entry must be a string. |

!!! caution

    The following cloud-init keys are prohibited and cause validation to fail if present: `bootcmd`, `network`, `network-config`, `packages`. These keys are platform-managed by Omnia and do not allow overrides.

## Prerequisites

- The [Create Mapping File](../Setup/create_mapping_file.md) procedure is complete.
- The [Configure Credentials](../Setup/configure_credentials.md) procedure is complete.
- The [Configure Inputs](../Setup/configure_inputs.md) procedure is complete.
- The [Prepare OIM](../Setup/prepare_oim.md) procedure is complete (OpenCHAMI and DHCP are running).
- The [Create Local Repos](../Setup/create_local_repos.md) procedure is complete (local Pulp repository is set up with required packages).
- The [Build Cluster Images](../Setup/build_cluster_images.md) procedure is complete.

## Procedure

Step 1: Enable additional cloud-init in provision_config.yml

Edit the provision configuration file:

```bash title="Run on: omnia_core container"
vi /opt/omnia/input/project_default/provision_config.yml
```

Set the `additional_cloud_init_config_file` parameter to the path of your configuration file:

```yaml title="File: /opt/omnia/input/project_default/provision_config.yml"
additional_cloud_init_config_file: "input/additional_cloud_init.yml"
```

To disable additional cloud-init, leave the value empty:

```yaml title="File: /opt/omnia/input/project_default/provision_config.yml"
additional_cloud_init_config_file: ""
```

Step 2: Create the additional cloud-init configuration file

A sample file is provided at `/omnia/input/additional_cloud_init.yml`. Edit this file or create a new one with the following structure:

```yaml title="File: /omnia/input/additional_cloud_init.yml"
---
# Common cloud-init applied to ALL nodes
common:
  write_files:
    - path: /etc/motd
      content: "Welcome to the HPC cluster\n"
      permissions: '0644'
  runcmd:
    - echo "Custom node setup complete" >> /var/log/custom_setup.log

# Per-functional-group cloud-init
groups:
  slurm_node_x86_64:
    runcmd:
      - echo "Slurm compute node initialized" >> /var/log/custom.log
  login_node_x86_64:
    write_files:
      - path: /etc/profile.d/cluster.sh
        content: |
          export CLUSTER_NAME=mycluster
        permissions: '0644'
```

File structure details:

| Key | Type | Description |
|-----|------|-------------|
| `common` | Dictionary | Cloud-init directives applied to all provisioned nodes. |
| `groups` | Dictionary of dictionaries | Each key is a functional group name and must match a `FUNCTIONAL_GROUP_NAME` in the PXE mapping file. Each value contains the cloud-init directives for that group. |

`write_files` entry fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | String | Yes | Absolute path where the file is created on the node. |
| `content` | String | No | Content to write to the file. |
| `permissions` | String | No | File permissions in octal format, for example, `'0644'`. |
| `owner` | String | No | File owner in `user:group` format. |
| `append` | Boolean | No | If `true`, append content to an existing file instead of overwriting. |
| `encoding` | String | No | Content encoding, for example, `base64`. Default is plain text. |

runcmd entries: 
Each entry in the `runcmd` list must be a string. Commands execute during the final stage of cloud-init, after all `write_files` directives are processed.

Step 3: Run the provisioning playbook

```bash title="Run on: omnia_core container"
cd /omnia/provision
ansible-playbook provision.yml
```

The provisioning playbook:

1. Validates the additional cloud-init configuration file (structure, allowed keys, functional group names).
2. Creates SMD groups for common and per-functional-group cloud-init.
3. Renders and registers the cloud-init configurations with the Boot Script Service (BSS).
4. When nodes PXE boot, cloud-init merges: platform defaults → common additional → per-functional-group additional.

### Merge Behavior

Omnia uses the following cloud-init merge strategy:

- **Dictionaries**: `no_replace` — platform-defined values are not overridden by user entries.
- **Lists**: `append` — user entries (`write_files`, `runcmd`) are appended to platform lists.
- **Order**: Platform defaults are applied first, then common additional cloud-init, then per-functional-group additional cloud-init.

This ensures that platform-critical configurations (networking, boot parameters) are not accidentally overridden.

## Verification

The following verifications are performed automatically when `provision.yml` runs. All validation errors are reported in a single pass.

| Check | Description |
|-------|-------------|
| File existence | The specified configuration file must exist. |
| YAML syntax | The file must be valid YAML. |
| Top-level keys | Only `common` and `groups` are allowed at the top level. |
| Prohibited keys | `bootcmd`, `network`, `network-config`, and `packages` are not allowed in any section. |
| Allowed keys | Only `write_files` and `runcmd` are allowed within each section. |
| `write_files` path | Every `write_files` entry must include a `path` field. |
| `runcmd` type | Every `runcmd` entry must be a string. |
| Functional group names | Group names under `groups` must match a `FUNCTIONAL_GROUP_NAME` in the PXE mapping file. |

### Examples

Example 1: Common configuration only

Apply an MOTD banner and a setup script to all nodes:

```yaml title="Example"
common:
  write_files:
    - path: /etc/motd
      content: |
        ========================================
        Dell HPC Cluster - Authorized Users Only
        ========================================
      permissions: '0644'
  runcmd:
    - echo "Node provisioned at $(date)" >> /var/log/provision.log
groups: {}
```

Example 2: Per-functional-group configuration

Run different setup commands on Slurm compute nodes versus login nodes:

```yaml title="Example"
common: {}
groups:
  slurm_node_x86_64:
    runcmd:
      - systemctl enable slurmd
      - echo "Slurm compute node ready" >> /var/log/custom.log
  login_node_x86_64:
    write_files:
      - path: /etc/profile.d/cluster_env.sh
        content: |
          export CLUSTER_NAME=myhpc
          export SCHEDULER=slurm
        permissions: '0644'
    runcmd:
      - echo "Login node ready" >> /var/log/custom.log
```

Example 3: Mixed common and per-group

Apply a common log entry to all nodes, plus additional Slurm-specific commands:

```yaml title="Example"
common:
  runcmd:
    - echo "Cluster node initialized" >> /var/log/custom_setup.log
groups:
  slurm_node_x86_64:
    runcmd:
      - echo "Slurm-specific setup complete" >> /var/log/custom_setup.log
```

In this case, Slurm compute nodes have both the common `runcmd` and the group-specific `runcmd` appended.

## Next Steps

- [Provision Nodes](../Setup/provision_nodes.md) -- Provision the cluster nodes with the updated cloud-init configuration.

## Troubleshooting

- **Custom cloud-init directives not applied on nodes**: Verify that the `additional_cloud_init_config_file` parameter in `provision_config.yml` points to the correct file path, and re-run `provision.yml`.

## Limitations

- Customization granularity is at the functional-group level. Per-node cloud-init customization is not supported.
- Only `write_files` and `runcmd` (config and final stage directives) are supported. Early-boot keys remain platform-managed.
- If a functional group name in the `groups` section does not match any entry in the PXE mapping file, validation fails.

!!! info

    - [Provision Nodes](../Setup/provision_nodes.md) -- Run `provision.yml` to apply cloud-init configurations.
    - [Provision Config](../../Reference/Configuration/provision_config.md) -- `additional_cloud_init_config_file` parameter reference.
    - [Additional Cloud Init Reference](../../Reference/Configuration/additional_cloud_init.md) -- Configuration file reference.
