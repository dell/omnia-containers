# Configure Cloud-Init for Flexible Groups

Use `cloud_init.config_file` in `functional_group_config.yml` to customize the
nodes of a flexible functional group at first boot. Flexible groups do not
receive category software, so use this file, or a pre-built image, to supply the
repositories and software that the group needs.

## Predefined and flexible cloud-init compared

| Item | Predefined groups | Flexible groups |
|---|---|---|
| Where you set it | `additional_cloud_init_config_file` in `orchestrator_config.yml` | `cloud_init.config_file` in `functional_group_config.yml` |
| Scope | `common` (all predefined groups) and `groups.<name>` sections in one file | One file per scope: `common` for all flexible groups, or `groups.<fg_name>` for one group |
| Directives | `write_files`, `runcmd` | `write_files`, `runcmd` |
| Rejected directives | `bootcmd`, `network`, `network-config`, `packages` | Any key other than `write_files` and `runcmd` |
| `write_files` entry | `path` required | `path` and `content` required |
| File location | Absolute path | Relative to the project input directory, or absolute; must resolve inside the project input directory |
| Credentials | Not allowed | Credential-like content is rejected |

`additional_cloud_init_config_file` applies only to predefined groups. For
`fg_` groups, use `functional_group_config.yml`.

## Procedure

1. Copy the reference template next to the project inputs and edit it:

    ```bash title="Run on: OIM"
    source /etc/profile.d/omnia-env.sh
    input_dir="$OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME"
    cp "$input_dir/functional_group_cloud_init_template.yml" \
       "$input_dir/fg_webserver_cloud_init.yml"
    vi "$input_dir/fg_webserver_cloud_init.yml"
    ```

2. Reference the file from the group:

    ```yaml title="File: functional_group_config.yml"
    groups:
      fg_webserver_rhel_10_2_x86_64:
        cloud_init:
          config_file: "fg_webserver_cloud_init.yml"
    ```

    To apply one file to every flexible group, set `common.cloud_init.config_file`
    instead. A group-level value takes priority over the `common` value.

3. Validate and publish:

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags validate
    ./omnia.sh --run orchestrator --tags manage-functional-group \
      -e fg_operation=configure -e configure_scope=cloud_init \
      -e fg_target_group=fg_webserver_rhel_10_2_x86_64
    ```

    Use `fg_operation=add` the first time you publish a group. See
    [Configure Flexible Functional Groups](configure_flexible_functional_groups.md).

## Sample cloud-init file

```yaml title="File: fg_webserver_cloud_init.yml"
---
write_files:
  - path: /etc/sysctl.d/99-webserver-tuning.conf
    content: |
      vm.swappiness=10
      net.ipv4.tcp_keepalive_time=600
    owner: root:root
    permissions: "0644"

  - path: /etc/webserver/app.conf
    content: |
      APP_ENV=production
      APP_LOG_LEVEL=info
    owner: root:root
    permissions: "0644"

runcmd:
  - sysctl --system
  - systemctl enable --now <service-name>
  - echo "fg_webserver setup completed" >> /var/log/fg-setup.log
```

`write_files` entries use these fields:

| Field | Required | Description |
|---|---|---|
| `path` | Yes | Absolute path of the file on the node. |
| `content` | Yes | File content as a string. |
| `owner` | No | `user:group`. Default `root:root`. |
| `permissions` | No | Octal mode, for example `"0644"`. Default `"0644"`. |
| `append` | No | `true` appends to an existing file. Default `false`. |

## Air-gapped variant

Use this variant when nodes reach packages only through the local Pulp mirror
on the OIM. It trusts the Pulp certificate and points the node's package manager
at the mirror before installing software.

```yaml title="File: fg_webserver_cloud_init_airgap.yml"
---
write_files:
  - path: /etc/pki/ca-trust/source/anchors/omnia-pulp-ca.crt
    content: |
      -----BEGIN CERTIFICATE-----
      <contents of the public Pulp certificate>
      -----END CERTIFICATE-----
    owner: root:root
    permissions: "0644"

  - path: /etc/yum.repos.d/omnia-local.repo
    content: |
      [omnia-local]
      name=Omnia local mirror
      baseurl=https://<pulp-host>:<pulp-port>/<repository-path>
      enabled=1
      gpgcheck=1
      sslcacert=/etc/pki/ca-trust/source/anchors/omnia-pulp-ca.crt
    owner: root:root
    permissions: "0644"

runcmd:
  - update-ca-trust extract
  - dnf clean all
  - dnf install -y <package-name>
```

- Copy only the public certificate. The certificate path and the repository
  addresses are recorded in the Repository Manager output
  (`repo_status.yml`). Do not copy private keys or credentials into the file.
- Replace the placeholders in angle brackets with values from your Pulp
  deployment. Do not hard-code the Omnia data path.
- Orchestrator treats the file as data and does not expand variables in it.

## Order of customization

- Within a file, `write_files` entries are created first, and `runcmd`
  commands then run in the order you list them. Put commands that depend on
  earlier ones after them.
- Orchestrator selects one file for each group: the group value when set,
  otherwise the `common` value. Files are not merged.
- Boot parameters are separate from cloud-init. See
  [Kernel parameters](../../Reference/Configuration/functional_group_config.md#kernel-parameters).

## Repositories and packages

- Orchestrator does not configure repositories or install packages for flexible
  groups. It also does not read `repo_status.yml` for them.
- `packages` and `bootcmd` are not accepted. Install software with `dnf` from
  `runcmd`, or include it in the image.
- Make sure each repository you configure is reachable from the node. For an
  air-gapped cluster, use the Pulp mirror as shown above.

## Verification

After the nodes boot, check the cloud-init result and the effect of your file:

```bash title="Run on: flexible node"
cloud-init status --long
cat /var/log/cloud-init-output.log
```

## Limitations

- Only `write_files` and `runcmd` are supported.
- Customization applies per group, not per node.
- Credential-like content in the file is rejected.

## Related topics

- [functional_group_config.yml](../../Reference/Configuration/functional_group_config.md)
- [Configure Additional Cloud-Init](configure_additional_cloud_init.md)
