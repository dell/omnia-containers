# functional_group_config.yml

This optional file configures flexible functional groups. A flexible group is a
node group whose name starts with the mandatory `fg_` prefix. Flexible groups
do not use `omnia_config.yml` or `storage_config.yml`, and Orchestrator does not
install Slurm, Kubernetes, or other category software on them.

When the file is absent, empty, or contains only empty values, Orchestrator
behaves as if no flexible group is configured.

## Location

```text
$OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/functional_group_config.yml
```

The template is staged with the other Orchestrator inputs. Edit it with
`omnia-cli edit orchestrator functional_group_config.yml` or with a text editor.

## Group names

A flexible group name must match the PXE mapping `FUNCTIONAL_GROUP_NAME` exactly
and use this form:

```text
fg_<label>_<os-name>_<os-version>_<architecture>
```

For example, `fg_webserver_rhel_10_2_x86_64`.

| Part | Rule |
|---|---|
| `fg_` | Mandatory prefix. Keys without it are rejected. Predefined groups (`service_kube_*`, `slurm_*`, `login_node_*`, `login_compiler_node_*`, `os_*`) cannot be configured in this file. |
| `<label>` | Letters, digits, `_`, and `-`. |
| `<os-name>_<os-version>` | For example `rhel_10_2`. RHEL 10.0 and 10.2 are the qualified releases. Other values produce a warning and do not stop the run. |
| `<architecture>` | `x86_64` or `aarch64`. A name without a supported architecture suffix is rejected. |

A catalog can contain at most 10 flexible groups. `catalog_validate` reports
functional layers that lack the `fg_` prefix or the platform suffix.

## Structure

```yaml title="File: $OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/functional_group_config.yml"
common:
  boot_kernel_params: ""
  boot_kernel_params_mode: "append"
  cloud_init:
    config_file: ""

groups:
  fg_webserver_rhel_10_2_x86_64:
    boot_kernel_params: "hugepagesz=2M hugepages=1024"
    boot_kernel_params_mode: "append"
    cloud_init:
      config_file: "fg_webserver_cloud_init.yml"
    image_override:
      kernel: ""
      initrd: ""
      rootfs: ""
```

No other keys are accepted at any level.

## Parameters

| Parameter | Scope | Type | Default | Description |
|---|---|---|---|---|
| `boot_kernel_params` | `common`, `groups.<name>` | string | `""` | Additional kernel command-line parameters. Separate parameters with spaces. Each token must be `key` or `key=value`; see [Kernel parameters](#kernel-parameters). |
| `boot_kernel_params_mode` | `common`, `groups.<name>` | `append` or `override` | `append` | How `boot_kernel_params` combines with the platform parameters. |
| `cloud_init.config_file` | `common`, `groups.<name>` | string | `""` | Path to a cloud-init file for the group. See [Cloud-init file](#cloud-init-file). |
| `image_override` | `groups.<name>` only | mapping | not set | Boot image to use instead of the Image Build Manager image. See [Image override](#image-override). |

### Precedence

Orchestrator resolves each setting separately, and the first non-empty value
wins:

1. `groups.<fg_name>` for the exact group.
2. `common`.
3. The Omnia default (`append` for `boot_kernel_params_mode`; empty for the rest).

An empty value does not override a value from a lower-priority scope.

### Kernel parameters

Orchestrator builds the boot parameters from three parts, in this order:
optional Omnia defaults, platform parameters, and your parameters. The kernel
honors the last occurrence of a parameter.

| Mode | Behavior |
|---|---|
| `append` | Your parameters are added after the optional Omnia defaults and the platform parameters. |
| `override` | The optional Omnia defaults are dropped and replaced by your parameters. Platform parameters are always kept. |

The platform parameters are the boot image location (`root=live:`), `ip=dhcp`,
`rd.live.image`, `rd.live.ram`, `rd.neednet`, the `console` settings, and the
metadata-service parameters. The optional Omnia defaults are `nomodeset`, `ro`,
the `rd.driver.blacklist` and `modprobe.blacklist` driver lists, `libata.force`,
`rd.luks=0`, `rd.md=0`, `rd.dm=0`, `selinux=0`, `apparmor=0`, and `ip6=off`.

!!! warning

    With `override`, the nodes boot without `selinux=0`, `apparmor=0`, `ip6=off`,
    and the driver blacklists unless you list them. You are responsible for the
    kernel parameters you set.

Orchestrator checks every token. These parameters are protected because the
platform manages them, and you must not set them:
`root`, `ip`, `ip6`, `rd.live.image`, `rd.live.ram`, `rd.neednet`, `console`,
`ds`, `selinux`, `apparmor`, `netroot`, `bootdev`, `initrd`, `BOOT_IMAGE`,
`inst.repo`, and `inst.stage2`. Tokens with quotes, backslashes, control
characters, or characters outside letters, digits, and `. _ - , : ; / @ + % =`
are also reported.

#### Migrate from `boot_kernel_params`

The global `boot_kernel_params` setting is removed from `orchestrator_config.yml`.
A non-empty value there fails input validation, and the key is no longer part of
the file schema, so delete the line.

1. Copy the value of `boot_kernel_params` from `orchestrator_config.yml`.
2. Delete the `boot_kernel_params` line from `orchestrator_config.yml`.
3. For flexible groups, put the value under `common.boot_kernel_params` to apply
   it to every flexible group, or under `groups.<fg_name>.boot_kernel_params`
   for one group.
4. Keep `boot_kernel_params_mode: "append"` unless you must replace the optional
   Omnia defaults.

Predefined groups no longer receive custom kernel parameters, because
`functional_group_config.yml` accepts only `fg_` groups.

### Cloud-init file

`cloud_init.config_file` points to a YAML file with these rules:

- Only `write_files` and `runcmd` are allowed. Any other top-level key, such as
  `packages` or `bootcmd`, is rejected.
- Every `write_files` entry needs `path` and `content`. Every `runcmd` entry is
  a string.
- The path is either relative to the project input directory or absolute, and
  it must resolve inside the project input directory (including through
  symbolic links). The file must exist, must not be empty, and must not be
  Ansible Vault encrypted.
- Content that looks like a credential (for example `password:`, `token=`,
  `api_key:`, `secret:`, or `private_key`) is rejected. Do not place secrets in
  the file.
- The file is treated as data. Orchestrator does not evaluate it as Jinja.
- If the path names an architecture (`x86_64` or `aarch64`), it must match the
  group architecture.

See [Configure Cloud-Init for Flexible Groups](../../HowTo/orchestrator/configure_flexible_group_cloud_init.md)
for a sample and the air-gapped variant. A reference template is staged next to
the inputs as `functional_group_cloud_init_template.yml`.

### Image override

By default, a flexible group boots the image that Image Build Manager records for
it in `build_status.yml`. Set `image_override` on a group to boot a different
image. The override is all or nothing:

| Key | Description |
|---|---|
| `kernel` | Object key of the kernel in the image storage. |
| `initrd` | Object key of the initrd in the image storage. |
| `rootfs` | Object key of the root file system image. |

- Set all three keys or none. A partial override is rejected.
- Each value is an object key relative to the image-storage endpoint: letters,
  digits, `.`, `_`, `-`, `/`; no scheme, no leading `/`, and no `..`.
- A value that names an architecture must match the group architecture.
- Before publication, Orchestrator checks that each object is reachable at the
  image-storage endpoint from `build_status.yml`. If an object is not reachable,
  Orchestrator warns and uses the Image Build Manager image instead.

## Validation

Input validation runs before any node is changed. It reports:

- A key outside the schema, or a value of the wrong type.
- A group key without the `fg_` prefix, without a supported architecture suffix,
  or not present in `pxe_mapping_file.csv`.
- An invalid `boot_kernel_params_mode`.
- An unreadable, empty, vaulted, or out-of-boundary cloud-init file, a
  disallowed directive, or credential-like content.
- An incomplete or unsafe `image_override`.
- A non-empty `boot_kernel_params` left in `orchestrator_config.yml`.

## Predefined and flexible groups compared

| Item | Predefined groups | Flexible groups |
|---|---|---|
| Name | Fixed prefixes: `service_kube_`, `slurm_`, `login_node_`, `login_compiler_node_`, `os_` | `fg_<label>_<os-name>_<os-version>_<architecture>` |
| Configured in | `omnia_config.yml`, `storage_config.yml`, `additional_cloud_init.yml` | `functional_group_config.yml` |
| Category software (Slurm, Kubernetes, and so on) | Installed by Orchestrator | Not installed; you supply it in the image or through cloud-init |
| Cloud-init file | `additional_cloud_init_config_file`: `common` and `groups` sections | `cloud_init.config_file`: one file per scope, `common` or group |
| Cloud-init directives | `write_files` and `runcmd` only | `write_files` and `runcmd` only |
| `write_files` entry | `path` required; `content` optional | `path` and `content` required |
| Kernel parameters | Platform parameters only | `boot_kernel_params` with `append` or `override` |
| Image | Image Build Manager image | Image Build Manager image, or `image_override` |
| Lifecycle | `provision`, `execute` | `manage-functional-group`; also published by default, `provision`, and `execute` runs |
| `repo_status.yml` | Required | Not required by `manage-functional-group` |

## Related configuration

- [Configure Flexible Functional Groups](../../HowTo/orchestrator/configure_flexible_functional_groups.md)
- [Configure Cloud-Init for Flexible Groups](../../HowTo/orchestrator/configure_flexible_group_cloud_init.md)
- [orchestrator_config.yml](orchestrator_config.md)
- [Additional cloud-init](additional_cloud_init.md)
- [PXE mapping file](../SampleFiles/pxe_mapping_file.md)
