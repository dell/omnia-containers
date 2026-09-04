# Path C: Full Deployment (Slurm + K8s + Telemetry)

Deploy a production-grade cluster with Slurm job scheduling, a highly available Kubernetes service cluster, and telemetry. This is the canonical Omnia deployment that exercises every major subsystem.

**What you will build:**

| Role | Functional Group | Count | Purpose |
| --- | --- | --- | --- |
| OIM (management) | -- | 1 | Runs the omnia.sh CLI; orchestrates the deployment. |
| K8s control plane | `service_kube_control_plane_x86_64` | 3 | HA Kubernetes control plane (`kube-apiserver`, `etcd`, `kube-scheduler`, `kube-controller-manager`). |
| K8s worker node | `service_kube_node_x86_64` | 1 | Runs the telemetry stack: iDRAC collector, LDMS aggregator, Kafka, VictoriaMetrics. |
| Slurm control node | `slurm_control_node_x86_64` | 1 | Runs `slurmctld` (Slurm controller), `slurmdbd` (accounting), and MariaDB. |
| Slurm compute node(s) | `slurm_node_x86_64` / `slurm_node_aarch64` | 1+ | Run `slurmd`; execute jobs submitted to the cluster. |
| Login / compiler node | `login_compiler_node_x86_64` / `login_compiler_node_aarch64` | 1 | User-facing SSH gateway with compiler toolchains for job submission and building applications. |

**Estimated time:** ~4 hours.

!!! note
    Complete the [Prerequisites Checklist](prerequisites_checklist.md) before proceeding.

## Step 1: Deploy omnia.sh

Download and install the `omnia.sh` script for domain-based execution.

```bash
# Download omnia.sh
wget https://raw.githubusercontent.com/dell/omnia/refs/tags/v2.3.0.0/omnia.sh
chmod +x omnia.sh

# Configure omnia.env
vi omnia.env

# Install and validate
./omnia.sh --validate
./omnia.sh --install
```

**For detailed setup instructions, see:** [Prepare OIM guide](../HowTo/main/setup_oim.md)

---

## Step 2: Create PXE Mapping File

Choose one method to create the PXE mapping file for your cluster nodes.

**Option A: Manual PXE Mapping**
Create `pxe_mapping_file.csv` manually with your hardware information. For full deployment, ensure at least **3 rows** use the `service_kube_control_plane` functional group and at least **1 row** uses `service_kube_node` for HA requirements.

**Option B: OME-based Discovery (Recommended)**
Use OpenManage Enterprise (OME) to auto-generate the mapping file.

```bash
./omnia.sh --run discovery --tags execute
```

**For detailed discovery procedures, see:** [Discover Nodes Using OME](../HowTo/discovery/discover_nodes.md)

---

## Step 3: Configure Input Files

Configure the input files that define your cluster's network, provisioning, telemetry, and storage settings.

**Required Input Files for Full Deployment:**
- `network_spec.yml` - Network CIDRs, interfaces, and IP ranges
- `provision_config.yml` - OS provisioning and PXE settings
- `high_availability_config.yml` - Kubernetes HA virtual IP configuration
- `telemetry_config.yml` - Telemetry sources, bridges, and sinks
- `telemetry_storage_config.yml` - Telemetry storage resources and retention
- `software_config.json` - Software stack (K8s, Slurm, telemetry components)
- `local_repo_config.yml` - Repository mirror settings
- `storage_config.yml` - NFS storage mount configuration
- `omnia_config.yml` - Slurm and service cluster K8s settings
- `security_config.yml` - OpenLDAP authentication settings
- `discovery_config.yml` - BMC discovery and OME integration
- `build_stream_config.yml` - Build Stream CI/CD pipeline settings (optional)
- `additional_cloud_init.yml` - Custom cloud-init scripts (optional)

**For input configuration details, see:** [Configure Inputs guide](../HowTo/main/configure_inputs.md)

---

## Step 4: Prepare OIM Infrastructure

Deploy the OIM infrastructure including OpenCHAMI provisioning stack, Pulp local repository, container registry, MinIO S3 storage, OpenLDAP authentication, and step-ca certificate authority.

```bash
./omnia.sh -s
```

**For OIM preparation details, see:** [Prepare OIM guide](../HowTo/main/setup_oim.md)

---

## Step 5: Create Local Repositories

Download all required RPM packages, container images, and tarballs into Pulp based on `software_config.json` for air-gapped provisioning.

```bash
./omnia.sh --run repo_manager --tags execute
```

**For repository management details, see:** [Create Local Repos](../HowTo/repo_manager/configure_repos.md)

---

## Step 6: Build Node Images

Build diskless OS images for each functional group in the PXE mapping file and upload them to MinIO (S3) for PXE boot delivery.

```bash
# Build x86_64 images
./omnia.sh --run image_build_manager --tags execute
```

**For image building details, see:** [Build Images](../HowTo/image_build_manager/build_images.md)

---

## Step 7: Provision Nodes

Configure boot scripts, cloud-init, and prepare nodes for K8s and Slurm deployment using the orchestrator domain.

```bash
./omnia.sh --run orchestrator --tags execute
```

**For provisioning details, see:** [Provision Nodes](../HowTo/orchestrator/provision_nodes.md)

---

## Step 8: PXE Boot Nodes

Boot all cluster nodes (K8s and Slurm) via PXE to load their OS images and complete provisioning.

**Option 1: Manual PXE Boot**
Configure each node to boot from the network via iDRAC or BIOS settings.

**Option 2: Automated PXE Boot**
```bash
cd /omnia/utils
ansible-playbook set_pxe_boot.yml
```

**For PXE boot procedures, see:** [Provision Nodes](../HowTo/orchestrator/provision_nodes.md)

---

## Step 9: Deploy Telemetry (Optional)

Deploy the telemetry stack for monitoring and metrics collection. This step is required only when `idrac: metrics_enabled` is set to `true` in `telemetry_config.yml`.

```bash
./omnia.sh --run telemetry --tags execute
```

**For telemetry deployment details, see:** [Telemetry Setup](../HowTo/Telemetry/setup_telemetry.md)

---

## Step 10: Verify Clusters

Verify that both Kubernetes and Slurm clusters are operational after all nodes have booted and cloud-init has completed.

```bash
# Verify Kubernetes cluster
ssh kcp1 'kubectl get nodes'

# Verify Slurm cluster
ssh scnode 'sinfo'

# Test job submission
srun -N 1 hostname
```

**For cluster verification details, see:** [Verify Cluster guide](../Operations/verify_cluster.md)

---

## Domain Reference Summary

| Domain | Purpose | HowTo Guide |
|--------|---------|-------------|
| **main** | omnia.sh setup and CLI | [Prepare OIM](../HowTo/main/setup_oim.md) |
| **discovery** | PXE mapping generation | [Discover Nodes Using OME](../HowTo/discovery/discover_nodes.md) |
| **repo_manager** | Local repository creation | [Create Local Repos](../HowTo/repo_manager/configure_repos.md) |
| **image_build_manager** | OS image building | [Build Images](../HowTo/image_build_manager/build_images.md) |
| **orchestrator** | Node provisioning and PXE boot | [Provision Nodes](../HowTo/orchestrator/provision_nodes.md) |
| **telemetry** | Monitoring and metrics collection | [Telemetry Setup](../HowTo/Telemetry/setup_telemetry.md) |

---

## Next Steps

After completing the full deployment:
- Configure GPU support: [Slurm with GPU](../HowTo/Configure/slurm_with_gpu.md)
- Customize Slurm configuration: [Configure Slurm](../HowTo/Configure/configure_slurm.md)
- Enable additional telemetry sources: [Telemetry Setup](../HowTo/Telemetry/setup_telemetry.md)
- Deploy PowerScale CSI driver: [Deploy PowerScale CSI](../HowTo/Configure/deploy_powerscale_csi.md)
- Enable Build Stream for GitOps: [Build Stream Deployment](buildstream_deployment.md)

!!! info
    - [Set Up Slurm](../HowTo/orchestrator/deploy_slurm.md) -- Detailed Slurm setup guide
    - [Telemetry Setup](../HowTo/Telemetry/setup_telemetry.md) -- Telemetry sources and configuration
    - [Prerequisites Checklist](prerequisites_checklist.md) -- Master checklist
    - [Slurm Troubleshooting](../Troubleshooting/orchestrator.md) -- Troubleshoot Slurm issues
    - [Telemetry Troubleshooting](../Troubleshooting/telemetry.md) -- Troubleshoot telemetry issues
