
# Playbook Reference
The playbooks generate the bootable node images and cloud-init configurations required for provisioning diskless nodes. During the PXE boot process, each node downloads the kernel, initramfs, and root filesystem image from the provisioning infrastructure, while cloud-init applies node-specific configuration such as networking, hostname, SSH keys, and system settings. This enables automated, consistent deployment and stateless operation of the cluster nodes without requiring a locally installed operating system on disk. This page provides a quick-reference table for all Omnia playbooks, including
their purpose, where they run, and what input files they require.

## Playbook summary table

| Playbook | Purpose |
| --- | --- |
| <b>provision/provision.yml</b> | Validates provision inputs and images, configures OIM/CoreDNS name resolution, provisions nodes via OpenCHAMI (BSS and cloud-init), and deploys mount, Kubernetes, Slurm, OpenLDAP, and telemetry configuration on the provisioned cluster nodes. |
| <b>input_validation/validate_config.yml</b> | Validates RHEL subscription status and repository URLs, then runs the `validate_input` role to perform schema and cross-file (L1/L2) validation of all Omnia input files, scoped by the tags of the calling playbook. |
| <b>utils/credential_utility/get_config_credentials.yml</b> | Creates and updates the encrypted `omnia_config_credentials.yml` file, prompting for any mandatory or conditional credentials (root password, BMC credentials, database passwords, LDAP bind password) that are missing. |
| <b>utils/oim_cleanup.yml</b> | Removes all Omnia-deployed containers, services, and configuration from the OIM (and, with the `credentials` tag, Omnia credential files), returning the OIM to a pre-Omnia state. Does **not** affect cluster nodes. |
| <b>prepare_oim/prepare_oim.yml</b> | Validates inputs and credentials, then deploys the `omnia_core`, Pulp, OpenLDAP, and OpenCHAMI containers on the OIM, configures the Pulp registry (HTTP/HTTPS), and installs required OIM packages and services. |
| <b>local_repo/local_repo.yml</b> | Validates the Pulp container and network configuration, then downloads and mirrors the software packages/images listed in `software_config.json` into the Pulp container on the OIM for air-gapped cluster installation. |
| <b>discovery/discovery.yml</b> | Discovers bare-metal nodes via the specified `discovery_mechanism` and registers them using Dell OpenManage Enterprise (OME) as the discovery source. |
| <b>build_image_x86_64/build_image_x86_64.yml</b> | Fetches required packages and builds the OpenCHAMI-based provisioning OS image for x86_64 functional groups, using BuildStream prerequisites when `enable_build_stream` is set. |
| <b>build_image_aarch64/build_image_aarch64.yml</b> | Prepares the aarch64 admin node, fetches required packages, and builds the OpenCHAMI-based provisioning OS image for aarch64 functional groups. |
| <b>gitlab/gitlab.yml</b> | Bootstraps passwordless SSH and deploys a hosted GitLab CE instance on the designated `gitlab_server` host for the BuildStreaM catalog pipeline, after validating OIM and provision prerequisites. |
| <b>gitlab/cleanup_gitlab.yml</b> | Removes the GitLab installation, packages, and directories from the `gitlab_server` host, then verifies that GitLab packages, directories, and processes are fully removed. |
| <b>telemetry/telemetry.yml</b> | Validates telemetry inputs, then deploys the telemetry pod stack on the service Kubernetes cluster and enables iDRAC telemetry collection. |
| <b>telemetry/telemetry_enable.yml</b> | Selectively re-enables a previously disabled telemetry source (for example, `--tags powerscale`) by scaling the corresponding Kubernetes workloads back up. |
| <b>telemetry/telemetry_disable.yml</b> | Selectively disables a telemetry source (for example, `--tags powerscale`) by scaling down its Kubernetes workloads while leaving storage components (VictoriaMetrics, VictoriaLogs) running. |
| <b>utils/create_container_group.yml</b> | Creates the Ansible `oim` inventory group used by other playbooks to target the Omnia Infrastructure Manager over SSH. |
| <b>utils/generate_functional_groups.yml</b> | Generates the functional group configuration from the PXE mapping file, used to organize cluster nodes by role for provisioning and image builds. |
| <b>utils/set_pxe_boot.yml</b> | Sets the boot source override on discovered nodes via the iDRAC Redfish API, reboots them to PXE, and (for BuildStreaM) verifies cloud-init phone-home completion and uploads results to GitLab. |
| <b>utils/slurm_config_util.yml</b> | Utility playbook that identifies the Slurm controller from the node inventory and runs Slurm configuration backup, cleanup, or rollback tasks (selected via `config_backup`, `slurm_cleanup`, or `config_rollback` tags). |
| <b>utils/update_cloud_init_bss.yml</b> | Updates the BSS boot parameters and/or cloud-init configuration for a specified functional group using pre-rendered YAML files on the OIM. Callable standalone or imported by upgrade/rollback flows. |
| <b>utils/external_kafka_connect_details.yml</b> | Resolves the service Kubernetes control-plane VIP from `high_availability_config.yml` and displays the external Kafka connection details for telemetry integration. |
| <b>utils/external_victoria_connect_details.yml</b> | Resolves the service Kubernetes control-plane VIP from `high_availability_config.yml` and displays the external VictoriaMetrics connection details for telemetry integration. |
| <b>utils/delete_migrated_pulp_rpm_repos.yml</b> | Deletes old- or new-format RPM repositories in Pulp (`-e repo_format=old\|new`) after a repo-name migration or rollback, and regenerates `/etc/yum.repos.d/pulp.repo` from the remaining distributions. |
| <b>log_collector/collect.yml</b> | Collects Kubernetes, Slurm controller, Slurm node, and login node logs across the cluster, then bundles them into a single archive with a summary for troubleshooting and diagnostics. |
| <b>rollback/rollback.yml</b> | Rolls back Slurm, Kubernetes/telemetry, BuildStreaM, and OIM (in that order) to the previous Omnia version recorded in `oim_metadata.yml`, tracking progress in `rollback_manifest.yml`. Fails if an upgrade is in progress. |
| <b>upgrade/prepare_upgrade.yml</b> | Run after `omnia.sh --upgrade`: transforms 2.1.0.0 input files to the 2.2.0.1 format, restores and re-encrypts credentials from backup, and displays a summary of migrated files and new fields requiring review before running `upgrade.yml`. |
| <b>upgrade/upgrade.yml</b> | Tag-based upgrade orchestrator that upgrades OIM, BuildStreaM, local repo, build images, provisioning, Kubernetes, telemetry, and Slurm (in dependency order) after operator approval, tracking progress in `upgrade_manifest.yml`. |

## Execution order

The individual playbooks are to be executed in this order:

| Step | Playbook | Description |
| --- | --- | --- |
| 1 | <b>prepare_oim/prepare_oim.yml</b> | Prepare the OIM (Podman, networking, OpenCHAMI). |
| 2 | <b>local_repo/local_repo.yml</b> | Synchronize local repository mirror. |
| 3 | <b>build_image_x86_64/build_image_x86_64.yml</b> | Build x86_64 provisioning image. |
| 4 | <b>build_image_aarch64/build_image_aarch64.yml</b> | Build AArch64 provisioning image (if ARM nodes present). |
| 5 | <b>provision/provision.yml</b> | Deploy Slurm, K8s and Telemetry. |

## How to run

All playbooks are executed from within the `omnia_core` container on the OIM:

```bash title="Run on: OIM host"
# SSH into the omnia_core container
ssh omnia_core

# or

# Execute directly in the container
podman exec -it omnia_core /bin/bash
```

```bash title="Run on: omnia_core container"
# Navigate to the omnia directory
cd /omnia

# Run a specific playbook
ansible-playbook <playbook_name>.yml

# Run with verbose output
ansible-playbook <playbook_name>.yml -vv

# Run with a specific inventory (if not using default)
ansible-playbook <playbook_name>.yml -i <absolute or relative path to inventory file>
```

!!! note

   - The playbooks are to be executed in the specified order as per the execution order table.

!!! info

    - [Provision Config](../Configuration/provision_config.md) -- Provisioning parameters.
    - [Omnia Config](../Configuration/omnia_config.md) -- Cluster deployment
      parameters.
    - [PXE Mapping File](../SampleFiles/pxe_mapping_file.md) -- PXE mapping CSV format.
