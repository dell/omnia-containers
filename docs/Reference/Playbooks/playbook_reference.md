
# Playbook Reference


This page provides a quick-reference table for all Omnia playbooks, including
their purpose, where they run, and what input files they require.

## Playbook summary table


| Playbook | Purpose | Run Location | Key Inputs |
| --- | --- | --- | --- |
| `omnia_startup.yml` | End-to-end orchestration playbook that calls all other playbooks in sequence: validation, OIM preparation, repository setup, discovery, image building, cluster deployment, and telemetry. | OIM | All configuration files under `/opt/omnia/input/project_default/`. |
| `input_validator.yml` | Validates all input files (YAML, JSON, CSV) for schema correctness, type checking, range validation, and cross-file consistency. | OIM | `provision_config.yml`, `network_spec.yml`, `omnia_config.yml`, `software_config.json`, `pxe_mapping.csv`, and all other config files. |
| `credentials_utility.yml` | Securely sets and stores sensitive credentials (root password, BMC credentials, database passwords, LDAP bind password) in an Ansible vault. | OIM | Interactive prompts. No input file required. |
| `prepare_oim.yml` | Prepares the OIM: installs Podman, configures networking, deploys the `omnia_core` container, and sets up OpenCHAMI services. | OIM | `provision_config.yml`, `network_spec.yml`. |
| `local_repo.yml` | Configures and synchronizes the local Pulp repository mirror on the OIM. Mirrors RHEL, EPEL, CUDA, K8s, and custom repositories. | OIM | `local_repo_config.yml`. |
| `discovery.yml` | Discovers bare-metal nodes via PXE boot and BMC/iDRAC scanning. Registers discovered nodes in OpenCHAMI inventory with hardware details, MAC addresses, and service tags. | OIM | `provision_config.yml`, `network_spec.yml`, `pxe_mapping.csv`. |
| `build_image_x86_64.yml` | Builds the provisioning OS image for x86_64 (Intel/AMD) nodes from the RHEL ISO. The image is served via HTTP/iPXE during PXE boot. | OIM | `provision_config.yml` (`iso_file_path`), `software_config.json`. |
| `build_image_aarch64.yml` | Builds the provisioning OS image for AArch64 (ARM Grace CPU) nodes. Requires a separate RHEL AArch64 ISO. | OIM | `provision_config.yml` (`iso_file_path` for AArch64), `software_config.json`. |
| `omnia.yml` | Main cluster deployment playbook. Installs and configures Slurm, Kubernetes, GPU drivers, storage mounts, and authentication on all cluster nodes based on their assigned roles. | OIM | `omnia_config.yml`, `software_config.json`, `storage_config.yml`, `security_config.yml`, `ha_config.yml`. |
| `telemetry.yml` | Deploys the telemetry pipeline: Kafka, VictoriaMetrics, Grafana, iDRAC telemetry collector, and LDMS samplers. | OIM | `telemetry_config.yml`, `omnia_config.yml`. |
| `auth.yml` | Deploys and configures centralized authentication services (OpenLDAP or FreeIPA) on the designated auth server node. | OIM | `security_config.yml`. |
| `oim_cleanup.yml` | Removes all Omnia-deployed services, containers, and configuration from the OIM. Returns the OIM to a pre-Omnia state. Does **not** affect cluster nodes. | OIM | None. Operates on OIM state only. |
| `add_node.yml` | Adds new nodes to an existing cluster without redeploying existing nodes. Discovers, provisions, and configures the new nodes based on updated PXE mapping and software config. | OIM | `pxe_mapping.csv` (updated with new nodes), `software_config.json`, `omnia_config.yml`. |
| `remove_node.yml` | Gracefully removes nodes from the cluster. Drains Slurm jobs or K8s pods, then decommissions the node from the scheduler/cluster. | OIM | Node hostname or IP (specified as extra var or in updated mapping). |

## Execution order (omnia_startup.yml)


When running the all-in-one `omnia_startup.yml` playbook, the individual
playbooks execute in this order:

| Step | Playbook | Description |
| --- | --- | --- |
| 1 | `input_validator.yml` | Validate all configuration files before proceeding. |
| 2 | `prepare_oim.yml` | Prepare the OIM (Podman, networking, OpenCHAMI). |
| 3 | `local_repo.yml` | Synchronize local repository mirror. |
| 4 | `discovery.yml` | Discover and register bare-metal nodes. |
| 5 | `build_image_x86_64.yml` | Build x86_64 provisioning image. |
| 6 | `build_image_aarch64.yml` | Build AArch64 provisioning image (if ARM nodes present). |
| 7 | `omnia.yml` | Deploy Slurm, K8s, GPU, storage, and auth. |
| 8 | `telemetry.yml` | Deploy telemetry pipeline (if enabled). |

## How to run


All playbooks are executed from within the `omnia_core` container on the OIM:

```bash title="Run on: OIM host"
# Enter the omnia_core container
podman exec -it omnia_core bash

# Run a specific playbook
ansible-playbook /opt/omnia/playbooks/<playbook_name>.yml

# Run with verbose output
ansible-playbook /opt/omnia/playbooks/<playbook_name>.yml -vv

# Run with a specific inventory (if not using default)
ansible-playbook /opt/omnia/playbooks/<playbook_name>.yml -i /opt/omnia/inventory
```


!!! note

    - Always run `input_validator.yml` (or `omnia_startup.yml`, which calls
      it first) before any other playbook to catch configuration errors early.
    - `credentials_utility.yml` is interactive and must be run manually
      before the first deployment to set passwords.

!!! info

    - [Provision Config](../Configuration/provision_config.md) -- Provisioning parameters.
    - [Omnia Config](../Configuration/omnia_config.md) -- Cluster deployment
      parameters.
    - [Pxe Mapping File](../SampleFiles/pxe_mapping_file.md) -- PXE mapping CSV format.
