# Configure Inputs

Configure Omnia's input files to define your cluster topology, software stack,
and deployment preferences. Input files are YAML and JSON located at
`/opt/omnia/input/project_default/` inside the `omnia_core` container.

## Overview

Before running any provisioning or deployment playbook, you must:

1. Copy example templates from `/omnia/examples/` to the working input directory.
2. Edit each file to match your environment.
3. Optionally run `validate_config.yml` to catch configuration errors early.

The key input files are:

- `software_config.json` -- Software stacks to deploy.
- `network_spec.yml` -- Admin, IB, and additional subnet configuration.
- `provision_config.yml` -- Provisioning parameters (PXE mapping, language, DHCP lease).
- `omnia_config.yml` -- Cluster-level configuration (Slurm, K8s, CSI drivers).
- `storage_config.yml` -- NFS, VAST, and other storage mount definitions (referenced by `omnia_config.yml`).


## Prerequisites

- The [Deploy Omnia Core](deploy_omnia_core.md) procedure is complete and `omnia_core` is
  running.
- You have planned your network topology (IP ranges, subnets).
- You know which software stacks you want to deploy (Slurm, Kubernetes,
  telemetry, etc.).


## Procedure
**1. Enter the omnia_core container**:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```


**2. Copy the example templates** to the input directory:

   ```bash title="Run on: omnia_core container"
   cp /omnia/examples/pxe_mapping_file.csv /opt/omnia/input/project_default/
   cp /omnia/examples/software_config_template/template_rhel_10.0_x86-64_software_config.json \
     /opt/omnia/input/project_default/software_config.json
   ```

!!! note

      Back up any previously customized files before copying. The `software_config_template/` directory contains architecture-specific templates (`x86-64` and `multi_arch`).

**3. Edit the software configuration**:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/software_config.json
   ```
   Example `software_config.json`:

```json title="File: /opt/omnia/input/project_default/software_config.json"
{
    "cluster_os_type": "rhel",
    "cluster_os_version": "10.0",
    "repo_config": "partial",
    "softwares": [
        {"name": "default_packages", "arch": ["x86_64", "aarch64"]},
        {"name": "admin_debug_packages", "arch": ["x86_64", "aarch64"]},
        {"name": "openldap", "arch": ["x86_64", "aarch64"]},
        {"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]},
        {"name": "slurm_custom", "arch": ["x86_64", "aarch64"]},
        {"name": "csi_driver_powerscale", "version": "v2.17.0", "arch": ["x86_64"]},
        {"name": "ldms", "arch": ["x86_64", "aarch64"]},
        {"name": "additional_packages", "arch": ["x86_64", "aarch64"]}
    ],
    "slurm_custom": [
        {"name": "slurm_control_node"},
        {"name": "slurm_node"},
        {"name": "login_node"},
        {"name": "login_compiler_node"}
    ],
    "service_k8s": [
        {"name": "service_kube_control_plane_first"},
        {"name": "service_kube_control_plane"},
        {"name": "service_kube_node"}
    ],
    "additional_packages": [
        {"name": "service_kube_control_plane_first"},
        {"name": "service_kube_control_plane"},
        {"name": "service_kube_node"},
        {"name": "slurm_control_node"},
        {"name": "slurm_node"},
        {"name": "login_node"},
        {"name": "login_compiler_node"},
        {"name": "os"}
    ]
}
```

!!! tip

      Each software entry requires `name` and `arch`. The `version` field is optional. Use `["x86_64", "aarch64"]` for multi-architecture deployments, or `["x86_64"]` for x86-only.

**4. Edit the network specification**:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/network_spec.yml
   ```


   Example `network_spec.yml`:

```yaml title="File: /opt/omnia/input/project_default/network_spec.yml"
---
Networks:
- admin_network:
    oim_nic_name: "eno1"
    subnet: "172.16.0.0"
    netmask_bits: "24"
    primary_oim_admin_ip: "172.16.107.254"
    primary_oim_bmc_ip: ""
    dynamic_range: "172.16.107.201-172.16.107.250"
    dns: []
    ntp_servers: []
    additional_subnets: []

- ib_network:
    subnet: "192.168.0.0"
    netmask_bits: "24"
    dns: []

- additional_subnets:
    - subnet: "10.40.1.0"
      netmask_bits: "24"
      router: "10.40.1.1"
      dynamic_range: "10.40.1.100-10.40.1.200"
```

!!! note

      The top-level `Networks:` key is mandatory. The `admin_network` section is required. The `ib_network` and `additional_subnets` sections are optional.


**5. Edit the provision configuration**:

```bash title="Run on: omnia_core container"
vi /opt/omnia/input/project_default/provision_config.yml
```
Example `provision_config.yml`:

```yaml title="File: /opt/omnia/input/project_default/provision_config.yml"
---
pxe_mapping_file_path: "/opt/omnia/input/project_default/pxe_mapping_file.csv"
language: "en_US.UTF-8"
default_lease_time: "86400"
dns_enabled: false
kernel_version_override: ""
additional_cloud_init_config_file: ""
```


**6. Edit the Omnia configuration** (for Slurm/K8s parameters):

```bash title="Run on: omnia_core container"
vi /opt/omnia/input/project_default/omnia_config.yml
```
   
Example `omnia_config.yml`:

```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
---
slurm_cluster:
  - cluster_name: slurm_cluster
    nfs_storage_name: nfs_slurm
    vast_storage_name: vast_storage

service_k8s_cluster:
  - cluster_name: service_cluster
    deployment: true
    etcd_on_local_disk: false
    k8s_cni: "calico"
    pod_external_ip_range: "172.16.107.170-172.16.107.200"
    k8s_service_addresses: "10.233.0.0/18"
    k8s_pod_network_cidr: "10.233.64.0/18"
    nfs_storage_name: "nfs_k8s"
    k8s_crio_storage_size: "20G"
    csi_powerscale_driver_secret_file_path: ""
    csi_powerscale_driver_values_file_path: ""
```

**(Optional) Run the input validator** to check your configuration:

```bash title="Run on: omnia_core container"
cd /omnia
ansible-playbook input_validation/validate_config.yml
```

The validator checks for missing required fields, IP address format and range
conflicts, valid software names, and consistent network configuration.


## Verification

**List all input files** and confirm they are populated:

```bash title="Run on: omnia_core container"
ls -la /opt/omnia/input/project_default/
```

**Review the software configuration**:

```bash title="Run on: omnia_core container"
cat /opt/omnia/input/project_default/software_config.json | python3 -m json.tool
```

## Next Steps

- [Configure Credentials](configure_credentials.md) -- Set up encrypted credentials for provisioning.
- [Prepare Oim](prepare_oim.md) -- Prepare OIM services (OpenCHAMI, Pulp, etc.).


## Troubleshooting

**validate_config.yml fails with "missing required field"**

Open the indicated file and ensure all required fields are present. Refer to
the templates in `/omnia/examples/software_config_template/` and the source
input files in `/omnia/input/` for the complete list of required fields.

**validate_config.yml fails with "JSON syntax error in software_config.json"**

Validate JSON syntax:

```bash title="Run on: omnia_core container"
python3 -m json.tool /opt/omnia/input/project_default/software_config.json
```

**validate_config.yml fails with "Network range overlap"**

Ensure `admin_network`, `ib_network`, and `additional_subnets` use different subnets.
Static and dynamic ranges within each network must not overlap.

