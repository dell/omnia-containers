# Flexible Functional Group Issues

Use this page when validation, `manage-functional-group`, or log collection
fails for a flexible (`fg_`) functional group. For the procedures, see
[Configure Flexible Functional Groups](../../HowTo/orchestrator/configure_flexible_functional_groups.md).

## Input validation rejects the group

Run `./omnia.sh --run orchestrator --tags validate` and read the first
`functional_group_config` message.

| Message contains | Cause | Fix |
|---|---|---|
| `is not a flexible functional group` | The key under `groups` lacks the `fg_` prefix. | Rename the group to `fg_<label>_<os-name>_<os-version>_<architecture>`. Configure predefined groups in `omnia_config.yml` and `storage_config.yml`. |
| `is not a functional group in the PXE mapping` | The key does not exactly match a `FUNCTIONAL_GROUP_NAME` in `pxe_mapping_file.csv`. | Copy the name from the mapping file. |
| `must end with one of the supported architecture suffixes` | The name does not end in `x86_64` or `aarch64`. | Add the architecture suffix in the mapping file and the configuration. |
| `image_override must be empty or contain exactly kernel, initrd, and rootfs` | The override is partial or has other keys. | Set all three keys, or remove `image_override`. |
| `must be an object key relative to the image-storage endpoint` | An image value has a scheme, a leading `/`, or `..`. | Use a relative object key. |
| `orchestrator_config.yml contains 'boot_kernel_params', which has been removed` | `boot_kernel_params` is still set in `orchestrator_config.yml`. | Follow [Migrate from `boot_kernel_params`](../../Reference/Configuration/functional_group_config.md#migrate-from-boot_kernel_params). |
| An unexpected property | A key is outside the file schema, or `boot_kernel_params` is still present in `orchestrator_config.yml`. | Remove the key. |

For cloud-init file errors (missing file, outside the input directory, empty,
vaulted, disallowed directive, credential-like content), see
[Cloud-init file](../../Reference/Configuration/functional_group_config.md#cloud-init-file).

## Kernel parameter reports

Orchestrator reports protected parameters, such as `root`, `ip`, `console`,
`selinux`, and `apparmor`, and tokens that are not valid kernel parameters.
Remove the parameter from `boot_kernel_params`. You are responsible for the
parameters you set. With `boot_kernel_params_mode: "override"`, the optional
Omnia defaults are dropped, so confirm that the nodes still boot. If they do not,
switch to `append` and run `manage-functional-group` with `fg_operation=configure`
and `configure_scope=boot`.

## Operation stops before any change

| Message contains | Cause | Fix |
|---|---|---|
| `Unsupported fg_operation` | `fg_operation` is not `add`, `remove`, or `configure`. | Correct the value. |
| `Unsupported configure_scope` | The scope is not `both`, `boot`, or `cloud_init`. | Correct the value. |
| `is not an fg_-prefixed functional group in the active PXE mapping` | `fg_target_group` does not name a mapped flexible group. | Check the name and the mapping file. |
| `Configure operation requires exactly one target group` | `fg_operation=configure` ran without `fg_target_group`, or with an unknown group. | Set `fg_target_group`. |
| `Remove requires an exact target group name starting with 'fg_'` | `fg_target_group` is missing for `remove`. | Set `fg_target_group`. |
| `Cannot remove flexible group ... node(s) are still mapped` | Nodes of the group remain in `pxe_mapping_file.csv`. | Remove or reassign every node, then retry. |
| `ownership evidence is missing or ambiguous` | Orchestrator cannot prove that it owns the records of the group. | Do not delete the records by hand. Collect logs and contact support. |

## Another operation holds the lock

Only one flexible-group operation runs for a project at a time. A message that
starts with `Project lock is currently held by active process` means another run
is active. Wait for it to finish.

If the message starts with `Non-terminal lock detected from inactive process`, or
the journal reports an unfinished operation, an earlier run stopped before it
finished.

1. Inspect the state files in the project output directory:

    ```bash title="Run on: OIM"
    output_dir="$OMNIA_DATA_PATH/orchestrator/output/$OMNIA_PROJECT_NAME"
    cat "$output_dir/.functional_group_mutation.lock"
    cat "$output_dir/.functional_group_journal.json"
    ```

2. Confirm that the process in the lock file is no longer running.
3. Repeat the same operation with recovery enabled:

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags manage-functional-group \
      -e fg_operation=<operation> -e fg_target_group=<fg_group_name> \
      -e fg_force_recovery=true
    ```

Do not delete the lock or the journal by hand.

## A run fails partway

A failed operation records the failed stage (`smd_group`, `bss`, or `metadata`)
in the journal, marks the operation `failed`, and releases the lock.

1. Read the error message of the failed task and correct the cause, for example
   an unreachable image object or an invalid cloud-init file.
2. Run the same operation again. Operations are idempotent.
3. If the error continues, collect logs before you change anything else. See
   [Collect cluster logs](../../Operations/collect_cluster_logs.md).

A failure in a flexible group does not remove an earlier success from the
history, but the current status reports the failure.

## Nodes do not pick up the change

`manage-functional-group` publishes configuration only. It does not boot or
reboot nodes. Reboot or re-provision the nodes of the group so that they fetch the
new boot and cloud-init configuration.

## An image override is ignored

If any of the three override objects is not reachable at the image-storage
endpoint, Orchestrator prints a warning and uses the Image Build Manager image.
Confirm the object keys and that the objects exist in the storage listed in
`build_status.yml`.

## Logs are missing for a flexible group

Log collection selects nodes through `collect_pxe.yml`, and the log folder name is
the group label. Add the group to `collect_pxe.yml` with its full name, for
example `fg_webserver_rhel_10_2_x86_64`. You cannot define custom log paths in
`functional_group_config.yml`. See
[Collect cluster logs](../../Operations/collect_cluster_logs.md#flexible-functional-groups).

## Related topics

- [functional_group_config.yml](../../Reference/Configuration/functional_group_config.md)
- [Configure Cloud-Init for Flexible Groups](../../HowTo/orchestrator/configure_flexible_group_cloud_init.md)
