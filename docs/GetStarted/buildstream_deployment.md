# Path D: BuildStreaM Automated Deployment

Omnia BuildStreaM provides a comprehensive automation solution for managing infrastructure build workflows. It uses a catalog-driven approach where you define your build requirements in a structured catalog file, and BuildStreaM executes automated pipelines to create and deploy images according to your specifications.

BuildStreaM supports three pipeline types that can be executed through GitLab:

- **Build Pipeline**: Creates diskless images based on catalog specifications. This pipeline is automatically triggered when the catalog is committed, but can also be executed manually.
- **Deploy Pipeline**: Deploys built images to target cluster nodes. This pipeline is automatically triggered when the PXE mapping file is updated, but can also be executed manually.
- **Clean Pipeline**: Removes old Image Groups based on retention policy. This pipeline can be executed only manually.

!!! note

    Complete the [Prerequisites Checklist](prerequisites_checklist.md) before proceeding.

## Step 1 -- Deploy the omnia_core Container

Clone the Omnia artifacts repository, build the container images, and
install the `omnia_core` Podman container on the OIM.

```bash title="Run on: OIM host"
# Clone and build
git clone https://github.com/dell/omnia-artifactory.git -b omnia-container-v2.2.0.0
cd omnia-artifactory
./build_images.sh core omnia_branch=v2.2.0.0 core_tag=2.2
```

```bash title="Run on: OIM host"
# Download and install omnia.sh
wget https://raw.githubusercontent.com/dell/omnia/refs/tags/v2.2.0.0/omnia.sh
chmod +x omnia.sh
./omnia.sh --install
```

When prompted, enter:

- **Shared path**: local file path or NFS share path for Omnia data.
- **Password**: secure alphanumeric password for accessing the Omnia core container.

```bash title="Run on: OIM host"
# Verify the container is running
systemctl status omnia_core
ssh omnia_core
exit
```

For detailed procedures including NFS setup, uninstall, and upgrade options, see [Deploy Omnia Core](../HowTo/Setup/deploy_omnia_core.md).

## Step 2 -- Create the Mapping File

The mapping file associates nodes with their BMC IPs, hostnames, and
functional groups. Manually collect PXE NIC information and define each
node in `pxe_mapping_file.csv`.

```bash title="Run on: OIM host"
ssh omnia_core
vi /opt/omnia/input/project_default/pxe_mapping_file.csv
```

```text title="File: pxe_mapping_file.csv (x86_64)"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_control_node_x86_64,grp0,ABCD12,,slurm-control-node1,a1:b2:c3:d4:e5:f6,172.16.107.52,a2:b3:c4:d5:e6:f7,172.17.107.52,InfiniBand.Slot.7-1,192.168.0.100
slurm_node_x86_64,grp1,ABCD34,ABFL82,slurm-node1,b1:c2:d3:e4:f5:a6,172.16.107.43,b2:c3:d4:e5:f6:a7,172.17.107.43,InfiniBand.Slot.7-1,192.168.0.101
slurm_node_x86_64,grp1,ABFG34,ABKD88,slurm-node2,c1:d2:e3:f4:a5:b6,172.16.107.44,c2:d3:e4:f5:a6:b7,172.17.107.44,InfiniBand.Slot.7-1,192.168.0.102
login_compiler_node_x86_64,grp8,ABCD78,,login-compiler-node1,d1:e2:f3:a4:b5:c6,172.16.107.41,d2:e3:f4:a5:b6:c7,172.17.107.41,InfiniBand.Slot.7-1,192.168.0.103
login_compiler_node_x86_64,grp8,ABFG78,,login-compiler-node2,e1:f2:a3:b4:c5:d6,172.16.107.42,e2:f3:a4:b5:c6:d7,172.17.107.42,InfiniBand.Slot.7-1,192.168.0.104
service_kube_control_plane_x86_64,grp3,ABFG79,,service-kube-control-plane1,f1:a2:b3:c4:d5:e6,172.16.107.53,f2:a3:b4:c5:d6:e7,172.17.107.53,,InfiniBand.Slot.7-1,192.168.0.105
service_kube_control_plane_x86_64,grp4,ABFH78,,service-kube-control-plane2,11:22:33:44:55:66,172.16.107.54,12:23:34:45:56:67,172.17.107.54,,InfiniBand.Slot.7-1,192.168.0.106
service_kube_control_plane_x86_64,grp4,ABFH80,,service-kube-control-plane3,aa:bb:cc:dd:ee:01,172.16.107.55,ab:bc:cd:de:ef:12,172.17.107.55,,InfiniBand.Slot.7-1,192.168.0.107
service_kube_node_x86_64,grp5,ABFL82,,service-kube-node1,33:44:55:66:77:88,172.16.107.56,34:45:56:67:78:89,172.17.107.56,InfiniBand.Slot.7-1,192.168.0.108
service_kube_node_x86_64,grp5,ABKD88,,service-kube-node2,55:66:77:88:99:aa,172.16.107.57,56:67:78:89:aa:bb,172.17.107.57,InfiniBand.Slot.7-1,192.168.0.109
os_x86_64,grp6,ABEF56,,os-node1,77:88:99:aa:bb:cc,172.16.107.60,78:89:aa:bb:cc:dd,172.17.107.60,,
```

For x86_64 and aarch64 mixed clusters:

```text title="File: pxe_mapping_file.csv (x86_64 and aarch64)"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_control_node_x86_64,grp0,ABCD12,,slurm-control-node1,a1:b2:c3:d4:e5:f6,172.16.107.52,a2:b3:c4:d5:e6:f7,172.17.107.52,InfiniBand.Slot.7-1,192.168.0.100
slurm_node_aarch64,grp1,ABCD34,ABFL82,slurm-node1,b1:c2:d3:e4:f5:a6,172.16.107.43,b2:c3:d4:e5:f6:a7,172.17.107.43,InfiniBand.Slot.7-2,192.168.0.101
slurm_node_aarch64,grp2,ABFG34,ABKD88,slurm-node2,c1:d2:e3:f4:a5:b6,172.16.107.44,c2:d3:e4:f5:a6:b7,172.17.107.44,NIC.InfiniBand.1-3,192.168.0.102
login_compiler_node_aarch64,grp8,ABCD78,,login-compiler-node1,d1:e2:f3:a4:b5:c6,172.16.107.41,d2:e3:f4:a5:b6:c7,172.17.107.41,InfiniBand.PCIe.Slot.8-1,192.168.0.103
login_node_aarch64,grp9,ABFG78,,login-node1,e1:f2:a3:b4:c5:d6,172.16.107.42,e2:f3:a4:b5:c6:d7,172.17.107.42,NIC.InfiniBand.1-1,192.168.0.104
service_kube_control_plane_x86_64,grp3,ABFG79,,service-kube-control-plane1,f1:a2:b3:c4:d5:e6,172.16.107.53,f2:a3:b4:c5:d6:e7,172.17.107.53,,
service_kube_control_plane_x86_64,grp4,ABFH78,,service-kube-control-plane2,11:22:33:44:55:66,172.16.107.54,12:23:34:45:56:67,172.17.107.54,,
service_kube_control_plane_x86_64,grp4,ABFH80,,service-kube-control-plane3,aa:bb:cc:dd:ee:01,172.16.107.55,ab:bc:cd:de:ef:12,172.17.107.55,,
service_kube_node_x86_64,grp5,ABFL82,,service-kube-node1,33:44:55:66:77:88,172.16.107.56,34:45:56:67:78:89,172.17.107.56,,
service_kube_node_x86_64,grp5,ABKD88,,service-kube-node2,55:66:77:88:99:aa,172.16.107.57,56:67:78:89:aa:bb,172.17.107.57,,
os_x86_64,grp6,ABEF56,,os-node1,77:88:99:aa:bb:cc,172.16.107.60,78:89:aa:bb:cc:dd,172.17.107.60,,
os_aarch64,grp7,ABEF78,,os-node2,99:aa:bb:cc:dd:ee,172.16.107.61,9a:ab:bc:cd:de:ef,172.17.107.61,,
```

!!! warning

    Replace all placeholder values with your actual hardware values.
    All fields are mandatory. The header fields are case-sensitive.

!!! note

    Ensure that nodes belonging to the same group have the same parent. In the mapping file, node entries with the same `GROUP_NAME` must have the same parent specified in the `PARENT_SERVICE_TAG` column.

!!! note

    The IP addresses and service tags provided in the mapping file are not validated by Omnia. Ensure that correct IP addresses and service tags are provided. Incorrect values can cause unexpected failures. The hostnames should not contain the domain name of the nodes.

!!! note

    The ADMIN_MAC and BMC_MAC addresses provided in `pxe_mapping_file.csv` should refer to the PXE NIC and BMC NIC on the target nodes respectively. Target servers should be configured to boot in PXE mode with the appropriate NIC as the first boot device.

For detailed information about the mapping file format and field descriptions, see [PXE Mapping File](../Reference/SampleFiles/pxe_mapping_file.md).

**Supported functional groups:**

| Functional Group | Layer | Description |
| --- | --- | --- |
| `slurm_control_node_x86_64` | Management | Slurm head node |
| `slurm_node_x86_64` | Compute | Slurm compute node (x86_64) |
| `slurm_node_aarch64` | Compute | Slurm compute node (aarch64) |
| `service_kube_control_plane_x86_64` | Management | K8s control plane for service cluster |
| `service_kube_node_x86_64` | Management | K8s worker node for service cluster |
| `login_node_x86_64` | Management | Login node (x86_64) |
| `login_node_aarch64` | Management | Login node (aarch64) |
| `login_compiler_node_x86_64` | Management | Login and compiler node (x86_64) |
| `login_compiler_node_aarch64` | Management | Login and compiler node (aarch64) |
| `os_x86_64` | Compute | Minimal OS baseline (x86_64) |
| `os_aarch64` | Compute | Minimal OS baseline (aarch64) |

Set the `pxe_mapping_file_path` variable in `provision_config.yml` to point to this file.

## Step 3 -- Provide Inputs and Prepare the OIM

Update the input configuration files and run `prepare_oim.yml` to deploy
BuildStreaM containers and services on the OIM.

```bash title="Run on: OIM host"
ssh omnia_core
ls /opt/omnia/input/project_default/
```

**Key files for this deployment:**

- [`build_stream_config.yml`](../Reference/Configuration/build_stream_config.md) -- BuildStreaM pipeline configuration

    ```yaml
    # Sample configuration
    enable_build_stream: true
    build_stream_host_ip: 192.168.1.10
    build_stream_port: 8010
    aarch64_inventory_host_ip: ""
    ```

- [`gitlab_config.yml`](../Reference/Configuration/gitlab_config.md) -- GitLab configuration

    ```yaml
    # Sample configuration
    gitlab_host: 192.168.1.100
    gitlab_project_name: omnia-catalog
    gitlab_project_visibility: private
    gitlab_default_branch: main
    gitlab_https_port: 443
    gitlab_min_storage_gb: 20
    gitlab_min_cpu_cores: 2
    ```

- [`network_spec.yml`](../Reference/Configuration/network_spec.md) -- Network CIDRs and interfaces

    ```yaml
    # Sample configuration
    Networks:
    - admin_network:
        oim_nic_name: eno1
        subnet: 192.168.1.0
        netmask_bits: "24"
        primary_oim_admin_ip: "192.168.1.10"
        primary_oim_bmc_ip: ""
        dynamic_range: "192.168.1.100-192.168.1.200"
        dns: []
        ntp_servers: []
    - ib_network:
        subnet: 10.0.1.0
        netmask_bits: "24"
        dns: []
    ```

- [`provision_config.yml`](../Reference/Configuration/provision_config.md) -- OS provisioning settings

    ```yaml
    # Sample configuration
    pxe_mapping_file_path: /opt/omnia/input/project_default/pxe_mapping_file.csv
    language: en_US.UTF-8
    default_lease_time: 86400
    dns_enabled: false
    ```

- [`high_availability_config.yml`](../Reference/Configuration/high_availability_config.md) -- Kubernetes HA virtual IP

    ```yaml
    # Sample configuration
    k8s_vip: 192.168.1.250
    k8s_vip_interface: eno1
    ```

- [`omnia_config.yml`](../Reference/Configuration/omnia_config.md) -- Omnia cluster settings

    ```yaml
    # Sample configuration
    service_cluster_enabled: true
    slurm_enabled: true
    ```

- [`local_repo_config.yml`](../Reference/Configuration/local_repo_config.md) -- Repository mirror settings

    ```yaml
    # Sample configuration
    local_repo_enabled: true
    local_repo_path: /opt/omnia/local_repo
    ```

- [`storage_config.yml`](../Reference/Configuration/storage_config.md) -- NFS storage mount configuration

    ```yaml
    # Sample configuration
    nfs_enabled: true
    nfs_server: 192.168.1.10
    nfs_path: /opt/omnia
    ```

- [`security_config.yml`](../Reference/Configuration/security_config.md) -- Authentication settings

    ```yaml
    # Sample configuration
    auth_type: freeipa
    realm: CLUSTER.LOCAL
    directory_domain: cluster.local
    admin_user: admin
    ```

- [`telemetry_config.yml`](../Reference/Configuration/telemetry_config.md) -- Telemetry pipeline configuration

    ```yaml
    # Sample configuration
    idrac_telemetry_enabled: true
    idrac_telemetry_collection_type: victoria
    victoria_deployment_mode: cluster
    ```

- [`user_registry_credential.yml`](../Reference/Configuration/user_registry_credential.md) -- User registry credentials

    ```yaml
    # Sample configuration
    registry_url: https://registry.example.com
    registry_username: admin
    registry_password: your_password
    ```

Edit each file as needed. Then run the prepare playbook:

```bash title="Run on: omnia_core container"
cd /omnia/prepare_oim
ansible-playbook prepare_oim.yml
```

```bash title="Run on: OIM host"
# Verify services are running
systemctl list-dependencies omnia.target
systemctl status omnia_build_stream.service
systemctl status omnia_postgres.service
systemctl status playbook_watcher.service
```

```text title="Expected output"
omnia.target
● ├─minio.service
● ├─omnia_auth.service
● ├─omnia_build_stream.service
● ├─omnia_core.service
● ├─omnia_postgres.service
● ├─playbook_watcher.service
● ├─pulp.service
● ├─registry.service
● ├─network-online.target
● │ └─NetworkManager-wait-online.service
● └─openchami.target
●   ├─acme-deploy.service
●   ├─acme-register.service
●   ├─bss-init.service
●   ├─bss.service
●   ├─cloud-init-server.service
●   ├─coresmd-coredhcp.service
●   ├─coresmd-coredns.service
●   ├─haproxy.service
●   ├─hydra-gen-jwks.service
●   ├─hydra-migrate.service
●   ├─hydra.service
●   ├─opaal-idp.service
●   ├─opaal.service
●   ├─openchami-cert-trust.service
●   ├─postgres.service
●   ├─smd-init.service
●   ├─smd.service
●   └─step-ca.service
```

A green circle indicates the service is running.

## Step 4 -- Deploy GitLab

Deploy GitLab as the CI/CD automation engine for BuildStreaM pipelines.

```bash title="Run on: omnia_core container"
# Update GitLab configuration
vi /opt/omnia/input/project_default/gitlab_config.yml

# Deploy GitLab
cd /omnia/gitlab
ansible-playbook gitlab.yml
```

When prompted, enter and note the GitLab password.

After installation, verify access at `https://<gitlab_host>:<gitlab_https_port>/root/<gitlab_project_name>`.

Verify the runner status: **Settings** → **CI/CD** → **Runners** → green status indicator.

For detailed GitLab deployment procedures, see [Deploy GitLab](../HowTo/BuildStreaM/deploy_gitlab.md).

## Step 5 -- Execute Build Pipeline

Update the catalog and trigger the build pipeline to create diskless images.

1. Go to `https://<gitlab_host>:<gitlab_https_port>/root/<gitlab_project_name>`.

2. Navigate to **Code** → **Repository** and edit `catalog_rhel.json` with your build requirements.

3. Commit the changes to automatically trigger the build pipeline.

4. Monitor the pipeline in **Build** → **Pipelines**. The build pipeline has four stages: **parse-catalog** → **generate-input-files** → **create-local-repository** → **build-image**.

5. Verify all stages show green checkmarks.

For manual pipeline execution, advanced catalog configuration, and troubleshooting, see [Execute Build Pipeline](../HowTo/BuildStreaM/execute_build_pipeline.md).

## Step 6 -- Execute Deploy Pipeline

Deploy the built images to cluster nodes.

1. Go to the GitLab project URL.

2. Update the `pxe_mapping_file.csv` in the `input/` folder and commit the changes to trigger the deploy pipeline.

3. In the deploy pipeline, select the image from the `select_image` stage and click **Play**.

4. Click **Play** on the `deploy` stage.

5. Monitor the pipeline. The deploy pipeline has three stages: **deploy** → **restart** → **validate**.

6. Verify all stages complete successfully.

For manual pipeline execution, handling partial failures, and adding new nodes, see [Execute Deploy Pipeline](../HowTo/BuildStreaM/execute_deploy_pipeline.md).

## Step 7 -- Initialize and Verify Telemetry

Initialize telemetry services and verify data collection.

```bash title="Run on: omnia_core container"
cd /omnia/telemetry
ansible-playbook telemetry.yml
```

```bash title="Run on: Service Kubernetes Control plane"
# Verify telemetry pods
kubectl get pods -n telemetry

# Verify telemetry services
kubectl get svc -n telemetry
```

Access the VictoriaLogs query interface to validate log collection:

```text title="VictoriaLogs query interface URL"
https://<external vlselect loadbalancer IP>:9471/select/vmui
```

Access the VMUI to validate metrics collection:

```text title="VMUI URL"
https://<external vmselect loadbalancer IP>:8481/select/0/vmui
```

For detailed telemetry verification including Kafka message validation, TLS connectivity tests, and database access, see [Initialize Telemetry](../HowTo/BuildStreaM/initialize_telemetry.md).

## What's next

- [Execute Build Pipeline](../HowTo/BuildStreaM/execute_build_pipeline.md) -- Detailed build pipeline operations
- [Execute Deploy Pipeline](../HowTo/BuildStreaM/execute_deploy_pipeline.md) -- Detailed deploy pipeline operations
- [Initialize Telemetry](../HowTo/BuildStreaM/initialize_telemetry.md) -- Detailed telemetry setup and verification
- [Cleanup Operations](../HowTo/BuildStreaM/cleanup_operations.md) -- Remove old Image Groups
- [Retry Pipelines](../HowTo/BuildStreaM/retry_pipelines.md) -- Retry failed pipeline operations
- [BuildStreaM Troubleshooting](../Troubleshooting/buildstream.md) -- Diagnose and resolve issues
