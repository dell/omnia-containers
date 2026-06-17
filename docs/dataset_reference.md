<!-- Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. -->

# Dataset Reference — `datasets/project_default/`

The `datasets/project_default/` folder contains Omnia deployment input files. These files mirror what the Omnia playbooks expect at `/opt/omnia/input/project_default/` inside the `omnia_core` container.

---

## How Datasets Are Synced

When `sync_dataset_to_core: true` is set in `omnia_test_config.yml` and a `converge` or `test` command runs, the automation:

1. Uses `rsync` over SSH (port 2222) to copy `datasets/<dataset>/` into the container at `/opt/omnia/input/project_default/`
2. Creates a vault key file (`.omnia_config_credentials_key`) if it doesn't exist
3. Encrypts `omnia_config_credentials.yml` using `ansible-vault` (same mechanism as Omnia playbooks)

This is handled by `molecule/shared/tasks/sync_project_default.yml`.

For `verify`-only runs, dataset sync is skipped — the existing files inside the container are used as-is.

---

## How Omnia Uses These Files

Inside the `omnia_core` container, every playbook starts by importing `utils/include_input_dir.yml`, which:

1. Reads `/opt/omnia/input/default.yml` to get the `project_name` (default: `project_default`)
2. Sets `input_project_dir` to `/opt/omnia/input/project_default/`
3. Validates that the project directory exists
4. Loads common variables and metadata

All subsequent playbook roles load their config files from `input_project_dir` using `include_vars`.

### Input File Flow

```
datasets/project_default/          (automation repo — your input files)
        │
        │  rsync via converge.yml (when sync_dataset_to_core: true)
        ▼
/opt/omnia/input/project_default/  (inside omnia_core container)
        │
        │  include_input_dir.yml → sets input_project_dir
        ▼
Omnia playbook roles               (load config via include_vars)
```

### Playbook-to-File Mapping

- `prepare_oim.yml` → reads `software_config.json` to determine which services to deploy (Slurm, K8s, OpenLDAP, etc.)
- `discovery.yml` → reads `discovery_config.yml` for BMC discovery and OME integration settings
- `local_repo.yml` → reads `local_repo_config.yml` and `software_config.json` for package and repository URLs
- `provision.yml` → reads `provision_config.yml`, `build_stream_config.yml`, `network_spec.yml`, and `additional_cloud_init.yml` for node provisioning
- `telemetry.yml` → reads `telemetry_config.yml` and `telemetry_storage_config.yml` for telemetry stack deployment
- `gitlab.yml` → reads `gitlab_config.yml` for GitLab server and pipeline configuration
- `oim_cleanup.yml` → reads `omnia_config.yml` and `storage_config.yml` for cleanup paths

---

## Dataset Files

### software\_config.json

**Consumed by:** `prepare_oim.yml`, `local_repo.yml`, `build_image_*.yml`, `input_validation/`

**Central control file.** Defines the OS type, version, repository mode, and the full software stack to deploy.

| Field | Type | Description |
|-------|------|-------------|
| `cluster_os_type` | string | Target OS (e.g., `rhel`, `rocky`) |
| `cluster_os_version` | string | Target OS version (e.g., `10.0`) |
| `repo_config` | string | Repository sync mode: `always`, `partial`, `never` |
| `softwares` | list | Software components to deploy. Each entry: `name`, optional `version`, `arch` list (`x86_64`/`aarch64`) |
| `service_k8s` | list | Kubernetes service roles (control plane, worker) |
| `slurm_custom` | list | Slurm roles (control node, compute node, login node) |

Example:
```json
{
    "cluster_os_type": "rhel",
    "cluster_os_version": "10.0",
    "repo_config": "always",
    "softwares": [
        {"name": "slurm_custom", "arch": ["x86_64"]},
        {"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]},
        {"name": "openldap", "arch": ["x86_64"]},
        {"name": "openmpi", "version": "5.0.8", "arch": ["x86_64"]}
    ]
}
```

### network\_spec.yml

**Consumed by:** `prepare_oim.yml`, `discovery.yml`, `provision.yml`, `local_repo.yml`

Defines network topology for the OIM and cluster nodes.

| Section | Description |
|---------|-------------|
| `admin_network` | OIM NIC name, subnet, netmask, primary OIM admin IP, BMC IP, DHCP dynamic range, DNS servers, NTP servers |
| `ib_network` | InfiniBand subnet and netmask |
| `additional_subnets` | Optional multi-RAC PXE subnets with router and dynamic range per subnet |

### provision\_config.yml

**Consumed by:** `provision.yml`

| Field | Description |
|-------|-------------|
| `pxe_mapping_file_path` | Path to PXE mapping CSV inside the container |
| `language` | OS locale (e.g., `en_US.UTF-8`) |
| `default_lease_time` | DHCP lease time in seconds |
| `dns_enabled` | Whether to configure DNS on provisioned nodes |
| `kernel_version_override` | Override kernel version for provisioned nodes |
| `additional_cloud_init_config_file` | Path to custom cloud-init config file |

### additional\_cloud\_init.yml

**Consumed by:** `provision.yml` (referenced via `provision_config.yml`)

Custom cloud-init configuration for stateless node provisioning. Allows injecting additional files and commands into provisioned nodes.

| Section | Description |
|---------|-------------|
| `common` | Applied to ALL nodes. Supports `write_files` and `runcmd` keys. |
| `groups` | Per-functional-group overrides keyed by group name (must match `pxe_mapping_file.csv`). Supports `write_files` and `runcmd`. |

**Prohibited keys** (validation will fail): `bootcmd`, `network`, `network-config`, `packages` — these are platform-managed.

**Merge behavior:** Platform defaults take precedence (`merge_how: no_replace`). User entries are appended. Group entries merge after common entries.

Example:
```yaml
common:
  write_files:
    - path: /etc/motd
      content: "Welcome to the HPC cluster\n"
      permissions: '0644'
  runcmd:
    - echo "Custom setup complete" >> /var/log/custom_setup.log

groups:
  slurm_node_x86_64:
    runcmd:
      - echo "Slurm node setup" >> /var/log/custom.log
```

### discovery\_config.yml

**Consumed by:** `discovery.yml`

| Field | Description |
|-------|-------------|
| `enable_bmc_discovery` | Toggle BMC-based node discovery (`true`/`false`) |
| `ome_ip` | OpenManage Enterprise IP for OME-based discovery |

### omnia\_config.yml

**Consumed by:** `provision.yml`, `oim_cleanup.yml`

| Section | Description |
|---------|-------------|
| `slurm_cluster` | Cluster name, NFS storage name |
| `service_k8s_cluster` | Cluster name, deployment toggle, etcd config, CNI, pod IP ranges, NFS storage name, CRI-O storage size, CSI PowerScale paths |

### omnia\_config\_credentials.yml

**Consumed by:** `prepare_oim.yml`, `provision.yml`, `gitlab.yml` (via `credential_utility/`)

Ansible-vault encrypted credentials for cluster node access, container registry, and service accounts. **Auto-encrypted during dataset sync** using a randomly generated vault key stored in `.omnia_config_credentials_key`.

### telemetry\_config.yml

**Consumed by:** `telemetry.yml`

Telemetry source configuration with per-source enable/disable and collection target settings:

| Source | Metrics | Collection Targets |
|--------|---------|-------------------|
| `idrac` | Temperature, power, fan, storage, CPU/memory errors | `victoria_metrics`, `kafka` |
| `ldms` | CPU, memory, network, disk from compute nodes | `kafka` |
| `dcgm` | GPU temperature, utilization, memory, ECC, power | (default) |
| `powerscale` | Dell PowerScale storage metrics and logs | `victoria_metrics`, `victoria_logs` |

### telemetry\_storage\_config.yml

**Consumed by:** `telemetry.yml`

VictoriaMetrics cluster sizing — replicas and resource limits for `vmstorage`, `vminsert`, `vmselect`, `vmagent`, and Kafka resource allocations.

### storage\_config.yml

**Consumed by:** `provision.yml`, `oim_cleanup.yml`

| Section | Description |
|---------|-------------|
| `mounts` | NFS mount definitions — source, mount point, options, functional group prefix, mount-on-OIM flag |
| `mount_params` | Mount parameter presets: `nfs_default`, `vast_rdma`, `vast_tcp` |
| `s3_configurations` | S3 provider and endpoint URL (e.g., MinIO) |

### local\_repo\_config.yml

**Consumed by:** `local_repo.yml`

RPM repository URLs per architecture:

| Field | Description |
|-------|-------------|
| `user_registry` | Container registry URL |
| `user_repo_url_x86_64` / `user_repo_url_aarch64` | User-defined RPM repos per arch |
| `rhel_os_url_x86_64` / `rhel_os_url_aarch64` | RHEL base OS repo URLs |
| `omnia_repo_url_rhel_x86_64` / `omnia_repo_url_rhel_aarch64` | Omnia-required repos (Docker, EPEL, K8s, CRI-O, DOCA, CUDA, NVIDIA HPC SDK) |
| `additional_repos_x86_64` / `additional_repos_aarch64` | Extra repos per arch |

Each entry: `{ url, gpgkey, sslcacert, sslclientkey, sslclientcert, name }`.

### security\_config.yml

**Consumed by:** `prepare_oim.yml`

| Field | Description |
|-------|-------------|
| `ldap_connection_type` | LDAP connection type: `TLS` or `SSL` |

### high\_availability\_config.yml

**Consumed by:** `provision.yml`

| Field | Description |
|-------|-------------|
| `service_k8s_cluster_ha` | List of HA-enabled K8s clusters with `enable_k8s_ha` and `virtual_ip_address` |

### gitlab\_config.yml

**Consumed by:** `gitlab.yml`

| Field | Description |
|-------|-------------|
| `gitlab_host` | GitLab server IP address |
| `gitlab_project_name` | Default project name |
| `gitlab_project_visibility` | Project visibility (`private`/`public`) |
| `gitlab_https_port` | HTTPS port |
| `gitlab_min_storage_gb` / `gitlab_min_memory_gb` / `gitlab_min_cpu_cores` | Resource minimums |
| `gitlab_puma_workers` | Puma web server workers |
| `gitlab_sidekiq_concurrency` | Sidekiq background job concurrency |

### build\_stream\_config.yml

**Consumed by:** `provision.yml`, `build_stream/`

| Field | Description |
|-------|-------------|
| `enable_build_stream` | Toggle BuildStream CI/CD (`true`/`false`) |
| `build_stream_host_ip` | BuildStream server IP |
| `build_stream_port` | BuildStream API port |
| `aarch64_inventory_host_ip` | aarch64 build host IP (optional) |

### user\_registry\_credential.yml

**Consumed by:** `local_repo.yml`

Container registry authentication credentials for pulling images during local repo sync.

### pxe\_mapping\_file.csv

**Consumed by:** `discovery.yml`, `provision.yml`

Node-to-network mapping CSV. Used by OpenCHAMI for PXE boot and node assignment.

Required columns: `HOSTNAME`, `ADMIN_IP`, `BMC_IP`, `ADMIN_MAC`, `FUNCTIONAL_GROUP`

### config/\<arch\>/\<os\>/\<version\>/*.json

**Consumed by:** `local_repo.yml`, `build_image_*.yml`

Per-architecture, per-OS package lists. Each JSON file corresponds to a software name from `software_config.json` and defines the RPM packages, container images, and files to sync for that component.

Example path: `config/x86_64/rhel/10.0/slurm_custom.json`
