# Path B: Full Deployment (Slurm + K8s + Telemetry)

Deploy a production-grade cluster with Slurm job scheduling, a highly
available Kubernetes service cluster, and telemetry. This is the canonical
Omnia deployment that exercises every major subsystem.

### Minimum node requirements -- x86_64 and aarch64

| Role | Functional Group | Architecture | Count | Purpose |
| --- | --- | --- | --- | --- |
| OIM (management) | -- | x86_64 | 1 | Runs `omnia_core` container; hosts OpenCHAMI stack (CoreDHCP, CoreDNS, SMD, BSS, TFTP, iPXE, HAProxy), Pulp (local repo), container registry, MinIO (S3), OpenLDAP (`omnia_auth`), and step-ca; orchestrates all Ansible playbooks |
| Service K8s control plane | `service_kube_control_plane` | x86_64 | 3 | HA Kubernetes control plane with kube-vip VIP failover; runs `etcd`, `kube-apiserver`, `kube-controller-manager`, `kube-scheduler`, CoreDNS, and Calico CNI |
| Service K8s worker node | `service_kube_node` | x86_64 | 1 | Hosts the telemetry stack as K8s pods: Kafka (Strimzi), VictoriaMetrics (vmselect/vminsert/vmstorage), vmagent, iDRAC telemetry receiver, LDMS aggregator/store, NFS subdir provisioner, and MetalLB |
| Slurm control node | `slurm_control_node` | x86_64 | 1 | Runs `slurmctld` (Slurm controller), `slurmdbd` (accounting daemon), MariaDB (job accounting database), and `munge` (authentication); manages NFS-shared Slurm config |
| Slurm compute node | `slurm_node` | aarch64 | 1 | Runs `slurmd` (compute daemon) and `munge`; mounts NFS shares for Slurm config, spool, and logs; includes LDMS telemetry sampler and OpenLDAP client (SSSD) |
| Login / compiler node | `login_compiler_node` | aarch64 | 1 | Runs `slurmd` for job submission (`sbatch`/`srun`); includes UCX, OpenMPI, compilers, NFS mounts (scratch, apps, hpc_tools), LDMS sampler, and OpenLDAP client (SSSD) |

### Minimum node requirements -- x86_64 only

| Role | Functional Group | Architecture | Count | Purpose |
| --- | --- | --- | --- | --- |
| OIM (management) | -- | x86_64 | 1 | Runs `omnia_core` container; hosts OpenCHAMI stack (CoreDHCP, CoreDNS, SMD, BSS, TFTP, iPXE, HAProxy), Pulp (local repo), container registry, MinIO (S3), OpenLDAP (`omnia_auth`), and step-ca; orchestrates all Ansible playbooks |
| Service K8s control plane | `service_kube_control_plane` | x86_64 | 3 | HA Kubernetes control plane with kube-vip VIP failover; runs `etcd`, `kube-apiserver`, `kube-controller-manager`, `kube-scheduler`, CoreDNS, and Calico CNI |
| Service K8s worker node | `service_kube_node` | x86_64 | 1 | Hosts the telemetry stack as K8s pods: Kafka (Strimzi), VictoriaMetrics (vmselect/vminsert/vmstorage), vmagent, iDRAC telemetry receiver, LDMS aggregator/store, NFS subdir provisioner, and MetalLB |
| Slurm control node | `slurm_control_node` | x86_64 | 1 | Runs `slurmctld` (Slurm controller), `slurmdbd` (accounting daemon), MariaDB (job accounting database), and `munge` (authentication); manages NFS-shared Slurm config |
| Slurm compute node | `slurm_node` | x86_64 | 1 | Runs `slurmd` (compute daemon) and `munge`; mounts NFS shares for Slurm config, spool, and logs; includes LDMS telemetry sampler and OpenLDAP client (SSSD) |
| Login / compiler node | `login_compiler_node` | x86_64 | 1 | Runs `slurmd` for job submission (`sbatch`/`srun`); includes UCX, OpenMPI, compilers, NFS mounts (scratch, apps, hpc_tools), LDMS sampler, and OpenLDAP client (SSSD) |

**Estimated time:** ~4 hours.

!!! note

    Complete the [Prerequisites Checklist](prerequisites_checklist.md)
    before proceeding.

## Step 1 -- Deploy the omnia_core Container

1. **Clone the Omnia Artifactory repository and build the container image**:

    ```bash title="Run on: OIM host"
    git clone https://github.com/dell/omnia-artifactory.git -b omnia-container-v2.2.0.0
    cd omnia-artifactory
    ./build_images.sh core omnia_branch=v2.2.0.0 core_tag=2.2
    ```

2. **Download the `omnia.sh` script**:

    ```bash title="Run on: OIM host"
    wget https://raw.githubusercontent.com/dell/omnia/refs/tags/v2.2.0.0/omnia.sh
    chmod +x omnia.sh
    ```

3. **Install the omnia_core container**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --install
    ```

    When prompted, enter the **shared directory path** (local or NFS) and a
    **secure alphanumeric password** for container access.

4. **Access the omnia_core container**:

    ```bash title="Run on: OIM host"
    ssh omnia_core
    ```

    You will be automatically logged in to the `omnia_core` container.

For detailed prerequisites, tasks performed by `omnia.sh`, and
troubleshooting, see
[Deploy Omnia Core](../HowTo/Setup/deploy_omnia_core.md){target="_blank"}.

## Step 2 -- Create the Mapping File

Omnia supports two methods for creating the PXE mapping file:

- **Manual** -- Collect PXE NIC information and fill in the
  `pxe_mapping_file.csv` manually.
- **OME-based discovery (recommended)** -- Use OpenManage Enterprise (OME)
  to discover cluster nodes and auto-generate the mapping file using
  `discovery.yml`.

### Option A: Fill the PXE mapping file manually

```bash title="Run on: omnia_core container"
vi /opt/omnia/input/project_default/pxe_mapping_file.csv
```

Populate one row per managed node with the required columns
(`FUNCTIONAL_GROUP_NAME`, `GROUP_NAME`, `SERVICE_TAG`, `HOSTNAME`,
`ADMIN_MAC`, `ADMIN_IP`, `BMC_IP`, etc.). For the complete column
reference and sample files, see
[PXE Mapping File Reference](../Reference/SampleFiles/pxe_mapping_file.md){target="_blank"}.

### Option B: Create PXE file using OME

Use the `discovery.yml` playbook to auto-generate the mapping file from
an OME inventory. For detailed instructions including OME prerequisites,
static group setup, and iDRAC hostname conventions, see
[Discover Nodes Using OME](../HowTo/Setup/discover_nodes.md){target="_blank"}.

```bash title="Run on: omnia_core container"
cd /omnia/discovery
ansible-playbook discovery.yml -e "discovery_mechanism=ome"
```

The playbook generates a `bmc_pxe_mapping_file_<timestamp>.csv` in
`/opt/omnia/input/project_default/`. Verify and edit the file as needed.

!!! warning

    For a full deployment, ensure at least **3 rows** use the
    `service_kube_control_plane` functional group and at least **1 row**
    uses `service_kube_node`. HA requires a minimum of 3 control-plane
    nodes.

## Step 3 -- Provide Inputs

For a full deployment, update the following input files in
`/opt/omnia/input/project_default/`:

**Key files for this deployment:**

- [`network_spec.yml`](../Reference/Configuration/network_spec.md){target="_blank"} -- Network CIDRs and interfaces
- [`provision_config.yml`](../Reference/Configuration/provision_config.md){target="_blank"} -- OS provisioning settings
- [`high_availability_config.yml`](../Reference/Configuration/high_availability_config.md){target="_blank"} -- Kubernetes HA virtual IP
- [`telemetry_config.yml`](../Reference/Configuration/telemetry_config.md){target="_blank"} -- Telemetry pipeline configuration
- [`software_config.json`](../Reference/Configuration/software_config.md){target="_blank"} -- Software stack (K8s, Slurm, telemetry components)
- [`local_repo_config.yml`](../Reference/Configuration/local_repo_config.md){target="_blank"} -- Repository mirror settings
- [`storage_config.yml`](../Reference/Configuration/storage_config.md){target="_blank"} -- NFS storage mount configuration
- [`omnia_config.yml`](../Reference/Configuration/omnia_config.md){target="_blank"} -- Slurm and service cluster K8s settings
- [`security_config.yml`](../Reference/Configuration/security_config.md){target="_blank"} -- OpenLDAP authentication settings
- [`discovery_config.yml`](../Reference/Configuration/discovery_config.md){target="_blank"} -- BMC discovery and OME integration

For the full procedure and parameter reference, see
[Configure Inputs](../HowTo/Setup/configure_inputs.md){target="_blank"}.

## Step 4 -- Set Credentials

The credential utility is automatically invoked by `prepare_oim.yml`. It
prompts for passwords interactively and stores them in an Ansible
Vault-encrypted file. For details on which credentials are prompted and
how to manage them, see
[Configure Credentials](../HowTo/Setup/configure_credentials.md){target="_blank"}.

!!! warning

    You will be prompted for a **Vault password** at the start of
    `prepare_oim.yml`. This password encrypts the credential file and is
    required for all subsequent playbook runs. Store it securely -- if
    lost, you must re-run the credential utility.

## Step 5 -- Prepare the OIM

Validates all input files, prompts for credentials, and deploys the OIM
infrastructure containers.

```bash title="Run on: omnia_core container"
cd /omnia/prepare_oim
ansible-playbook prepare_oim.yml
```

For detailed information, see
[Prepare OIM](../HowTo/Setup/prepare_oim.md){target="_blank"}.

### Verification

After `prepare_oim.yml` completes, verify the OIM services on the
**OIM host** (not inside the container):

```bash title="Run on: OIM host"
systemctl is-active omnia.target
```

Expected output: `active`

```bash title="Run on: OIM host"
systemctl list-dependencies omnia.target
```

Expected output:

```text title="Expected output"
omnia.target
● ├─minio.service
● ├─omnia_auth.service
● ├─omnia_core.service
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

```bash title="Run on: OIM host"
podman ps --format "table {{.Names}}\t{{.Status}}"
```

Expected output:

```text title="Expected output"
NAMES               STATUS
bss                 Up 30 hours
cloud-init-server   Up 30 hours
coresmd-coredhcp    Up 30 hours
coresmd-coredns     Up 30 hours
haproxy             Up 30 hours
hydra               Up 30 hours
minio-server        Up 7 days
omnia_auth          Up 7 days
omnia_core          Up 8 days
opaal               Up 30 hours
opaal-idp           Up 30 hours
postgres            Up 30 hours
pulp                Up 7 days
registry            Up 7 days
smd                 Up 30 hours
step-ca             Up 30 hours
```

!!! note

    - The `minio-server` container will **not** be present if you configured
      PowerScale as the S3 endpoint (`s3_configurations.provider: "powerscale"`)
      in `storage_config.yml`.
    - The `omnia_auth` container will **not** be present if `openldap` is
      not included in `software_config.json`.

## Step 6 -- Create Local Repositories

Downloads all required RPM packages, container images, tarballs, and pip
modules into Pulp for air-gapped provisioning. Packages are downloaded
for both x86_64 and aarch64 architectures based on `software_config.json`.

```bash title="Run on: omnia_core container"
cd /omnia/local_repo
ansible-playbook local_repo.yml
```

!!! note

    Expect **45--90 minutes** depending on network speed. Total download
    size is typically **20--40 GB**.

For detailed information, see
[Create Local Repos](../HowTo/Setup/create_local_repos.md){target="_blank"}.

### Verification

After `local_repo.yml` completes, verify all software components were
downloaded successfully:

**x86_64:**

```bash title="Run on: omnia_core container"
cat /opt/omnia/log/local_repo/rhel/10.0/x86_64/software.csv
```

Expected output:

```text title="Expected output"
name,status
default_packages,success
admin_debug_packages,success
openldap,success
service_k8s,success
slurm_custom,success
csi_driver_powerscale,success
```

**aarch64** (if aarch64 nodes are in the PXE mapping file):

```bash title="Run on: omnia_core container"
cat /opt/omnia/log/local_repo/rhel/10.0/aarch64/software.csv
```

Expected output:

```text title="Expected output"
name,status
default_packages,success
admin_debug_packages,success
openldap,success
slurm_custom,success
```

All entries must show `success`.

## Step 7 -- Build Node Images

### 7.1 Build x86_64 images

Builds compute images for all x86_64 functional groups defined in the
PXE mapping file and uploads them to the S3 bucket.

```bash title="Run on: omnia_core container"
cd /omnia/build_image_x86_64
ansible-playbook build_image_x86_64.yml
```

### 7.2 Build aarch64 images (if applicable)

Builds compute images for all aarch64 functional groups defined in the
PXE mapping file and uploads them to the S3 bucket.

!!! note

    Before running this playbook, the aarch64 node must be prepared with
    RHEL 10 installed and an inventory file created. For prerequisites
    and setup instructions, see
    [Preparing aarch64 Node](../Reference/Configuration/prepare_aarch64_node.md){target="_blank"}.

```bash title="Run on: omnia_core container"
cd /omnia/build_image_aarch64
ansible-playbook build_image_aarch64.yml -i <inventory_file>
```

### Verification

Verify the built images are uploaded to the S3 bucket:

```bash title="Run on: OIM host"
s3cmd ls -Hr s3://boot-images
```

Expected output (showing two functional groups as example):

```text title="Expected output"
2026-06-26 11:42    78M  s3://boot-images/efi-images/slurm_control_node_x86_64/rhel-slurm_control_node_x86_64_omnia_2.2.0.0/initramfs-6.12.0-55.82.1.el10_0.x86_64.img
2026-06-26 11:42    15M  s3://boot-images/efi-images/slurm_control_node_x86_64/rhel-slurm_control_node_x86_64_omnia_2.2.0.0/vmlinuz-6.12.0-55.82.1.el10_0.x86_64
2026-06-26 11:42  1449M  s3://boot-images/slurm_control_node_x86_64/rhel-slurm_control_node_x86_64_omnia_2.2.0.0/rhel10.0-rhel-slurm_control_node_x86_64_omnia_2.2.0.0-10.0
2026-06-26 11:43    78M  s3://boot-images/efi-images/slurm_node_x86_64/rhel-slurm_node_x86_64_omnia_2.2.0.0/initramfs-6.12.0-55.82.1.el10_0.x86_64.img
2026-06-26 11:43    15M  s3://boot-images/efi-images/slurm_node_x86_64/rhel-slurm_node_x86_64_omnia_2.2.0.0/vmlinuz-6.12.0-55.82.1.el10_0.x86_64
2026-06-26 11:44  1430M  s3://boot-images/slurm_node_x86_64/rhel-slurm_node_x86_64_omnia_2.2.0.0/rhel10.0-rhel-slurm_node_x86_64_omnia_2.2.0.0-10.0
...
```

Each functional group in the PXE mapping file should have **3 images**:

- `initramfs-<kernel_version>.img` -- Initial RAM filesystem
- `vmlinuz-<kernel_version>` -- Linux kernel
- `rhel<version>-<functional_group>-<omnia_version>` -- OS root filesystem image

## Step 8 -- Set PXE Boot

Sets the PXE boot order on all target nodes via iDRAC Redfish and
reboots them for network provisioning.

```bash title="Run on: omnia_core container"
cd /omnia/utils
ansible-playbook set_pxe_boot.yml
```

For detailed information, see
[PXE Boot Nodes](../HowTo/Setup/pxe_boot_nodes.md){target="_blank"}.

### Verification

After `set_pxe_boot.yml` completes, verify that cloud-init has finished
on all provisioned nodes:

```bash title="Run on: omnia_core container"
ssh <node_hostname> 'cloud-init status'
```

Expected output:

```text title="Expected output"
status: done
```

All nodes should report `status: done`. Run this command for each node
in the PXE mapping file to confirm provisioning is complete.

## Step 9 -- Deploy Telemetry

Deploys the telemetry pipeline as Kubernetes pods on the service cluster.

```bash title="Run on: omnia_core container"
cd /omnia/telemetry
ansible-playbook telemetry.yml
```

For detailed information, see
[Setup Telemetry](../HowTo/Telemetry/setup_telemetry.md){target="_blank"}.

## Step 10 -- Verify the Telemetry Pipeline

```bash title="Run on: omnia_core container"
ssh kcp1 'kubectl get pods -n telemetry'
```

Expected output (all pods `Running`):

```text title="Expected output"
NAME                                           READY   STATUS    RESTARTS   AGE
bridge-bridge-798f595c5b-pt94w                 1/1     Running   0          29h
idrac-telemetry-0                              5/5     Running   2          29h
kafka-broker-0                                 1/1     Running   0          29h
kafka-broker-1                                 1/1     Running   0          29h
kafka-broker-2                                 1/1     Running   0          29h
kafka-controller-3                             1/1     Running   0          29h
kafka-controller-4                             1/1     Running   0          29h
kafka-controller-5                             1/1     Running   0          29h
kafka-entity-operator-bcd75596c-h5f4f          2/2     Running   0          29h
nersc-ldms-aggr-0                              1/1     Running   0          29h
nersc-ldms-store-slurm-cluster-0               1/1     Running   0          29h
strimzi-cluster-operator-7c889c4cff-2fqjl      1/1     Running   0          29h
victoria-metrics-operator-6bf4d7cc6d-9gl8v     1/1     Running   0          29h
vmagent-vmagent-587b6d476f-hl2zp               2/2     Running   0          29h
vmagent-vmagent-587b6d476f-xgddh               2/2     Running   0          29h
vminsert-victoria-cluster-65b6bb84cb-5g85d     1/1     Running   0          29h
vminsert-victoria-cluster-65b6bb84cb-m6f4s     1/1     Running   0          29h
vmselect-victoria-cluster-0                    1/1     Running   0          29h
vmselect-victoria-cluster-1                    1/1     Running   0          29h
vmstorage-victoria-cluster-0                   1/1     Running   0          29h
vmstorage-victoria-cluster-1                   1/1     Running   0          29h
vmstorage-victoria-cluster-2                   1/1     Running   0          29h
```

## What's Next?

Your production cluster is fully operational with Slurm scheduling,
Kubernetes service cluster, and telemetry monitoring. Consider these
enhancements:

- **Scale out compute nodes** -- Add more `slurm_node` entries to the PXE
  mapping file, re-run `provision.yml`.
- **Add GPU support** -- Edit `software_config.json` to include NVIDIA
  drivers and CUDA toolkit.
- **Enable BuildStreaM for GitOps** -- See
  [BuildStreaM Deployment](buildstream_deployment.md) (Path D) to layer
  CI/CD automation on top of this deployment.

!!! info

    - [Slurm Quickstart](slurm_quickstart.md) -- Simplified 4-node Slurm deployment
    - [K8S Telemetry Only](k8s_telemetry_only.md) -- Telemetry without Slurm
    - [Prerequisites Checklist](prerequisites_checklist.md) -- Master checklist
