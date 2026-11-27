# Configure Flexible Functional Groups

Flexible functional groups let you provision nodes that do not belong to a
predefined Omnia category. You define the group's boot parameters, boot image,
and cloud-init in `functional_group_config.yml`, and Orchestrator publishes the
configuration for every node mapped to the group.

## Overview

| Topic | Behavior |
|---|---|
| Naming | Every flexible group name starts with `fg_` and ends with the OS and architecture, for example `fg_webserver_rhel_10_2_x86_64`. |
| Configuration | `functional_group_config.yml`. See [functional_group_config.yml](../../Reference/Configuration/functional_group_config.md). |
| Public tag | `manage-functional-group` adds, removes, and configures flexible groups. |
| Also published by | Default (untagged), `provision`, and `execute` runs publish every mapped flexible group. |
| Scope | Orchestrator registers the group and publishes its boot and cloud-init configuration. It does not install Slurm, Kubernetes, or other category software, and it does not PXE boot or reboot nodes. |

!!! note

    Flexible groups do not change predefined groups. You cannot configure a
    predefined group (`service_kube_*`, `slurm_*`, `login_node_*`,
    `login_compiler_node_*`, `os_*`) in `functional_group_config.yml`.

## Prerequisites

- [Discover Nodes](../discovery/discover_nodes.md) is complete. The PXE mapping
  file lists each flexible node with a `FUNCTIONAL_GROUP_NAME` that starts with
  `fg_` and matches the group name in `functional_group_config.yml` exactly.
- OpenCHAMI is deployed. Run the Orchestrator `prepare` and `deploy` phases
  first. See [Deploy OpenCHAMI](deploy_openchami.md).
- A boot image exists for the group. Image Build Manager records it in
  `build_status.yml`, or you set `image_override` for the group. See
  [Build Cluster Images](../image_build_manager/build_images.md).
- The deployment catalog is available. Orchestrator uses `catalog_file_path`
  from `orchestrator_config.yml`, then `CATALOG_FILE_PATH`, then
  `$OMNIA_DATA_PATH/catalog/catalog_rhel.json`.
- `boot_kernel_params` is removed from `orchestrator_config.yml`. See
  [Migrate from `boot_kernel_params`](../../Reference/Configuration/functional_group_config.md#migrate-from-boot_kernel_params).

`manage-functional-group` does not require a successful `repo_status.yml`.
Repository, registry, and package configuration for flexible groups is your
responsibility. Use [cloud-init](configure_flexible_group_cloud_init.md) or a
pre-built image.

## Configure the group

1. Open the configuration file:

    ```bash title="Run on: OIM"
    source /etc/profile.d/omnia-env.sh
    vi "$OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/functional_group_config.yml"
    ```

2. Define the group under `groups`:

    ```yaml title="File: functional_group_config.yml"
    common:
      boot_kernel_params_mode: "append"

    groups:
      fg_webserver_rhel_10_2_x86_64:
        boot_kernel_params: "hugepagesz=2M hugepages=1024"
        cloud_init:
          config_file: "fg_webserver_cloud_init.yml"
    ```

3. Map the nodes to the group. In `pxe_mapping_file.csv`, set
   `FUNCTIONAL_GROUP_NAME` to `fg_webserver_rhel_10_2_x86_64` for each node.

4. Validate the inputs:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags validate
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags validate
        ```

## Manage flexible groups

The `manage-functional-group` tag takes its operation from extra variables.

| Variable | Values | Description |
|---|---|---|
| `fg_operation` | `add` (default), `remove`, `configure` | The operation to perform. |
| `fg_target_group` | An exact `fg_` group name | The group to act on. Optional for `add`. Required for `remove` and `configure`. |
| `configure_scope` | `both` (default), `boot`, `cloud_init` | What `configure` publishes. |

### Add a group

`add` creates or reconciles the group in OpenCHAMI, publishes its boot
configuration and its metadata, and registers the mapped nodes. Without
`fg_target_group`, it acts on every `fg_` group in the PXE mapping.

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags manage-functional-group \
      -e fg_operation=add -e fg_target_group=fg_webserver_rhel_10_2_x86_64
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
    ansible-playbook orchestrator.yml --tags manage-functional-group \
      -e fg_operation=add -e fg_target_group=fg_webserver_rhel_10_2_x86_64
    ```

!!! warning

    `add` does not check the previous PXE identity or the workload-scheduler
    state of a node. Before you map a node that is part of a Slurm or
    Kubernetes cluster to a flexible group, remove it from that scheduler. See
    [Replace a node](#replace-a-node).

### Configure a group

`configure` republishes configuration for exactly one group. It does not create
the group, register nodes, or change any scheduler. Choose what to publish with
`configure_scope`:

| Scope | Publishes |
|---|---|
| `boot` | Boot parameters and image only. |
| `cloud_init` | Cloud-init metadata only. |
| `both` | Both. |

```bash title="Run on: OIM"
cd <OMNIA_SOURCE_PATH>/src/main
./omnia.sh --run orchestrator --tags manage-functional-group \
  -e fg_operation=configure -e configure_scope=boot \
  -e fg_target_group=fg_webserver_rhel_10_2_x86_64
```

Nodes use the new configuration the next time they boot. Orchestrator does not
reboot them.

### Remove a group

`remove` deletes the group's metadata, boot configuration, and OpenCHAMI group.
It requires an exact `fg_target_group`.

1. Remove every node of the group from `pxe_mapping_file.csv`, or move them to
   another group. Removal fails while any mapped node remains.
2. Run:

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags manage-functional-group \
      -e fg_operation=remove -e fg_target_group=fg_webserver_rhel_10_2_x86_64
    ```

Orchestrator removes only records that it can prove it owns. If ownership is
missing or ambiguous, the removal stops. After a removal, Orchestrator
recalculates the shared `ssh` and `chrony` groups from the nodes that remain.

## When configuration is published

| Run | Flexible-group publication |
|---|---|
| `manage-functional-group` | Performs the operation you select. |
| Default (no tag) | Publishes all mapped flexible groups. |
| `provision` | Publishes all mapped flexible groups. |
| `execute` | Publishes all mapped flexible groups. |

These lifecycle runs publish idempotently and never remove a group. Removal
happens only through `manage-functional-group` with `fg_operation=remove`. The
predefined categories are provisioned as before, and flexible groups are not
part of the custom catch-all category.

`manage-functional-group` validates the project inputs first, then runs the
OpenCHAMI preamble. It uses the same locks and status reporting as the lifecycle
runs.

## Boundaries

- Orchestrator does not install category software on flexible groups. Provide
  the software in the image or through
  [cloud-init](configure_flexible_group_cloud_init.md).
- Flexible groups do not use `omnia_config.yml`, `storage_config.yml`, or the
  repository status file for publication. `manage-functional-group` does not
  require `repo_status.yml`.
- `manage-functional-group` does not run PXE boot or reboot nodes. To boot nodes,
  use the [PXE boot](configure_pxe_boot.md) procedure.
- `manage-functional-group` cannot be combined with `cleanup` or
  `cleanup_credentials`.
- Not supported: overriding a predefined group, upgrade, migration, rollback,
  and a node that belongs to a flexible group and a predefined group at the same
  time.

## Replace a node

!!! warning

    Before you add a node to a flexible group, remove it from its current
    scheduler (Slurm or Kubernetes) and drain its workload. Orchestrator does
    not check the node's previous group or scheduler state, and it does not
    remove the node from the scheduler for you.

## Verification

- The run ends without a failed task. Each operation works through ordered
  stages (`smd_group`, `bss`, and `metadata`) and records each stage as it is
  verified. A failed run reports the stage that failed, and the failure takes
  priority over any earlier success.
- Inspect the transition journal for the last operation:

    ```bash title="Run on: OIM"
    cat "$OMNIA_DATA_PATH/orchestrator/output/$OMNIA_PROJECT_NAME/.functional_group_journal.json"
    ```

    The journal records the operation, the target group, the completed stages,
    and a terminal result of `succeeded`, `noop`, or `failed`.

- After the nodes boot, confirm the effects of your cloud-init file and kernel
  parameters, for example with `cat /proc/cmdline` on a node.

## Next steps

- [Configure Cloud-Init for Flexible Groups](configure_flexible_group_cloud_init.md)
- [Collect cluster logs](../../Operations/collect_cluster_logs.md)
- [Provision Nodes](provision_nodes.md)

## Troubleshooting

See [Flexible functional group issues](../../Troubleshooting/orchestrator/flexible_functional_groups.md).
