
# Playbook Reference
The playbooks generate the bootable node images and cloud-init configurations required for provisioning diskless nodes. During the PXE boot process, each node downloads the kernel, initramfs, and root filesystem image from the provisioning infrastructure, while cloud-init applies node-specific configuration such as networking, hostname, SSH keys, and system settings. This enables automated, consistent deployment and stateless operation of the cluster nodes without requiring a locally installed operating system on disk. This page provides a quick-reference table for all Omnia playbooks, including
their purpose, where they run, and what input files they require.

## Playbook summary table

| Playbook | Purpose |
| --- | --- |
| <b>provision/provision.yml</b> | End-to-end orchestration playbook that calls all other playbooks in sequence: validation, OIM preparation, repository setup, discovery, image building, cluster deployment, and telemetry. |
| <b>input_validation/validate_config.yml</b> | Validates all input files (YAML, JSON, CSV) for schema correctness, type checking, range validation, and cross-file consistency. |
| <b>utils/credential_utility/get_config_credentials.yml</b> | Securely creates and updates credential configuration files. Prompts for sensitive credentials (root password, BMC credentials, database passwords, LDAP bind password) and stores them in encrypted vault files. |
| <b>utils/oim_cleanup.yml</b> | Removes all Omnia-deployed services, containers, and configuration from the OIM. Returns the OIM to a pre-Omnia state. Does **not** affect cluster nodes. |
| <b>prepare_oim/prepare_oim.yml</b> | Prepares the OIM: installs Podman, configures networking, deploys the `omnia_core` container, and sets up OpenCHAMI services. |
| <b>local_repo/local_repo.yml</b> | Configures and synchronizes the local Pulp repository mirror on the OIM. Mirrors RHEL, EPEL, CUDA, K8s, and custom repositories. |
| <b>discovery/discovery.yml</b> | Discovers bare-metal nodes via PXE boot and BMC/iDRAC scanning. Registers discovered nodes in OpenCHAMI inventory with hardware details, MAC addresses, and service tags. |
| <b>build_image_x86_64/build_image_x86_64.yml</b> | Builds the provisioning OS image for x86_64 (Intel/AMD) nodes from the RHEL ISO. The image is served via HTTP/iPXE during PXE boot. |
| <b>build_image_aarch64/build_image_aarch64.yml</b> | Builds the provisioning OS image for AArch64 (ARM Grace CPU) nodes. Requires a separate RHEL AArch64 ISO. |
| <b>gitlab/gitlab.yml</b> | Deploys and configures GitLab for the BuildStreaM catalog pipeline on the designated GitLab host. Manages project creation, SSL certificates, and repository settings. |
| <b>gitlab/cleanup_gitlab.yml</b> | Removes GitLab deployment and cleans up related configurations and containers. |
| <b>telemetry/telemetry.yml</b> | Deploys the telemetry pipeline: Kafka, VictoriaMetrics, Grafana, iDRAC telemetry collector, and LDMS samplers. |
| <b>telemetry/telemetry_enable.yml</b> | Enables telemetry collection on cluster nodes without full redeployment. |
| <b>telemetry/telemetry_disable.yml</b> | Disables telemetry collection on cluster nodes. |
| <b>utils/create_container_group.yml</b> | Creates container groups and manages container-related configurations on the OIM. |
| <b>utils/generate_functional_groups.yml</b> | Generates functional group mappings from the PXE mapping file for cluster node organization. |
| <b>utils/set_pxe_boot.yml</b> | Configures PXE boot settings on discovered nodes for provisioning. |
| <b>utils/slurm_config_util.yml</b> | Utility playbook for managing Slurm configuration backups and updates. |
| <b>utils/update_cloud_init_bss.yml</b> | Updates cloud-init configuration on Boot Service Stack (BSS) for node provisioning. |
| <b>utils/external_kafka_connect_details.yml</b> | Retrieves and displays external Kafka connection details for telemetry integration. |
| <b>utils/external_victoria_connect_details.yml</b> | Retrieves and displays external VictoriaMetrics connection details for telemetry integration. |
| <b>utils/delete_migrated_pulp_rpm_repos.yml</b> | Cleans up migrated RPM repositories from Pulp after migration. |
| <b>log_collector/collect.yml</b> | Collects logs from all cluster nodes and the OIM for troubleshooting and diagnostics. |
| <b>rollback/rollback.yml</b> | Rolls back Omnia deployment to a previous state. Restores configurations and removes recent changes. |
| <b>upgrade/prepare_upgrade.yml</b> | Prepares the cluster for an Omnia version upgrade. Validates compatibility and backs up configurations. |
| <b>upgrade/upgrade.yml</b> | Performs the Omnia version upgrade across the OIM and cluster nodes. |

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
