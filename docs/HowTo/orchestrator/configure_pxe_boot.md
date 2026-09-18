# Configure PXE Boot

## Overview

Orchestrator uses Dell iDRAC to set mapped servers to a PXE-compatible boot
target, restart them, and optionally verify that each node completed a fresh
boot and cloud-init after the current PXE operation. The workflow reads nodes from
`pxe_mapping_file.csv`; it does not use a separate Ansible inventory.

Every direct PXE run without a `pxeboot_inventory` override selects all rows in
the active mapping. To restrict an operation to selected nodes, provide a
custom CSV through `pxeboot_inventory`. When BuildStreaM is enabled and supplies
a job ID, its retry workflow can generate this filtered inventory and exclude
nodes already recorded as successful.

By default, `orchestrator_config.yml` enables PXE boot. The optional
`set_pxe_boot_config.yml` file controls restart behavior, the boot-source
override, and node-registration timing.

!!! caution

    The PXE workflow can restart running servers. Stop workloads and save
    required data before you run it. With the shipped defaults, every selected
    server is force restarted and its network-boot override remains
    `continuous` until it is changed.

## Prerequisites

- Complete the `provision` phase in [Provision Nodes](provision_nodes.md) so
  boot and cloud-init configurations exist in OpenCHAMI.
- Ensure the configured Repository Manager `repo_status.yml` exists, reports
  `overall_status: success`, and references an existing Pulp server
  certificate. The default is the active project's Repository Manager output;
  use `repo_manager_output_path` in `orchestrator_config.yml` when the status
  file is stored elsewhere.
- Ensure the active project's Orchestrator `pxe_mapping_file.csv` retains the
  `SERVICE_TAG`, `HOSTNAME`, `ADMIN_IP`, and `BMC_IP` columns. Every PXE target
  requires nonempty `HOSTNAME`, `ADMIN_IP`, and `BMC_IP` values;
  `SERVICE_TAG` may be empty.
- Configure Orchestrator credentials so the encrypted credential file contains
  `bmc_username` and `bmc_password`.
- Ensure the OIM can reach each iDRAC address and each server can reach the OIM
  provisioning network.
- Ensure the provisioned OS image includes `cloud-init`. The `provision`
  phase embeds the OIM public key into generated cloud-init; passwordless
  root SSH to the node's admin IP is expected only after the node boots.
- Ensure `/proc/uptime` is available after the target OS starts.
- Enable PXE or UEFI HTTP boot in the server firmware and NIC firmware.

## Procedure

1. Confirm that PXE boot is enabled in the active project's Orchestrator
   `orchestrator_config.yml`:

    ```yaml
    enable_pxe_boot: true
    ```

2. Optionally edit `set_pxe_boot_config.yml` in the same project input
   directory. The following values are the shipped defaults:

    ```yaml
    enable_node_registration: true
    node_registration_pause_minutes: 3
    node_registration_retries: 120
    node_registration_delay: 15
    restart_host: true
    force_restart: true
    boot_source_override_enabled: continuous
    boot_source_override_target: pxe
    ```

    Set `boot_source_override_target` to `uefi_http` when that is the boot
    method configured on the servers. Set `boot_source_override_enabled` to
    `once` when the override should apply only to the next boot. The default,
    `continuous`, keeps selecting the configured network boot target
    on later restarts until the iDRAC override is changed.

    For backward compatibility, Orchestrator accepts the legacy
    `enable_phone_home` and `phone_home_*` variable names but emits a
    deprecation warning. Use only the `node_registration_*` names in new
    configurations.

3. Run the Orchestrator PXE workflow from the Omnia source checkout:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags pxeboot
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags pxeboot
        ```

    To retry only selected nodes, provide a CSV with the same mapping columns:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags pxeboot \
          -e pxeboot_inventory=/path/to/retry_mapping.csv
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags pxeboot \
          -e pxeboot_inventory=/path/to/retry_mapping.csv
        ```

## Verification

- When `enable_pxe_boot: false`, a standalone `--tags pxeboot` run skips the
  entire PXE import and does not refresh `pxeboot_status.yml`,
  `orchestrator_status.yml`, or `failed_nodes.json`. During an untagged or
  `execute` run, provisioning refreshes `orchestrator_status.yml` with the PXE
  phase set to `not_run`, but it does not refresh `pxeboot_status.yml` or
  `failed_nodes.json`. Existing PXE-specific files may therefore describe an
  earlier run; do not use them as evidence for the skipped PXE phase.
- Confirm that the play recap reports no failed hosts.
- Review `pxeboot_status.yml`, `orchestrator_status.yml`, and
  `failed_nodes.json` in the active project's Orchestrator output directory.
  `pxeboot_status.yml` contains every target node; a successful run contains
  an empty `failed_nodes` list in `failed_nodes.json`.
- When node-registration verification is enabled, confirm that every
  successfully restarted node is reachable through passwordless root SSH, has
  a boot time newer than the start of the PXE operation, and reports `done`
  from `cloud-init status --long`. The workflow derives the boot time from
  `/proc/uptime`; it does not use a Metadata Service phone-home callback.

## Next steps

- [Verify the cluster](../../Operations/verify_cluster.md) after the nodes have
  booted.
- Use [Add Nodes](../../Operations/add_nodes.md) for later additions to the mapping.

## Troubleshooting

- **Credentials are missing**: Run the Orchestrator `credentials` or `prepare`
  workflow, then retry `pxeboot`.
- **No BMC hosts are found**: Confirm that `BMC_IP` is populated in the mapping
  CSV.
- **Node registration times out**: Verify passwordless root SSH from the OIM to
  the node's admin IP. Check `/proc/uptime` and run
  `cloud-init status --long` on the node. Increase
  `node_registration_retries` or `node_registration_delay` only when
  cloud-init is still running. Nodes that fail the iDRAC restart phase are
  excluded from node-registration polling and remain listed in
  `failed_nodes.json`.
- **iDRAC rejects the boot override**: Confirm the requested boot target is
  enabled in firmware and supported by the installed iDRAC firmware and
  license.
- **A retry should not wait for node registration**: Run the PXE workflow with
  `-e enable_node_registration=false`.
