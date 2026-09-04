# Path A: Slurm Quick Start

Deploy a Slurm HPC cluster using Omnia. This is the fastest path to a working Omnia environment and the recommended starting point for first-time users. testing

**What you will build:**

| Role | Functional Group | Purpose |
| --- | --- | --- |
| OIM (management) | -- | Runs the omnia.sh CLI; orchestrates the deployment. Does **not** join the Slurm cluster. |
| Head node | `slurm_control_node_x86_64` | Runs `slurmctld` (Slurm controller) and `slurmdbd` (accounting database). x86_64 only. |
| Compute node(s) | `slurm_node_x86_64` / `slurm_node_aarch64` | Run `slurmd`; execute jobs submitted to the cluster. |
| Login node | `login_node_x86_64` / `login_node_aarch64` | User-facing SSH gateway for job submission. |
| Login/compiler node | `login_compiler_node_x86_64` / `login_compiler_node_aarch64` | Login gateway with compiler toolchains for building applications. |

!!! note
    This tutorial assumes you have completed every item on the
    [Prerequisites Checklist](prerequisites_checklist.md). If you have not, stop here and finish that first.

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
Create `pxe_mapping_file.csv` manually with your hardware information.

**Option B: OME-based Discovery (Recommended)**
Use OpenManage Enterprise (OME) to auto-generate the mapping file.

```bash
./omnia.sh --run discovery --tags execute
```

**For detailed discovery procedures, see:** [Discover Nodes Using OME](../HowTo/discovery/discover_nodes.md)

---

## Step 3: Configure Input Files

Configure the input files that define your cluster's network, provisioning, and storage settings.

**Required Input Files for SLURM:**
- `network_spec.yml` - Network CIDRs, interfaces, and IP ranges
- `provision_config.yml` - OS provisioning and PXE settings  
- `software_config.json` - Software stack selections (must include `slurm_custom`)
- `omnia_config.yml` - Slurm cluster configuration
- `storage_config.yml` - NFS storage mount configuration
- `local_repo_config.yml` - Repository mirror settings
- `telemetry_config.yml` - Telemetry and monitoring settings
- `security_config.yml` - OpenLDAP authentication settings

**SLURM-specific requirement:** The `slurm_custom` entry is mandatory in `software_config.json`.

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

Configure boot scripts, cloud-init, and prepare nodes for Slurm deployment using the orchestrator domain.

```bash
./omnia.sh --run orchestrator --tags execute
```

**For provisioning details, see:** [Provision Nodes](../HowTo/orchestrator/provision_nodes.md)

---

## Step 8: PXE Boot Nodes

Boot all Slurm-related nodes via PXE to load their OS images and complete provisioning.

**Option 1: Manual PXE Boot**
Configure each node to boot from the network via iDRAC or BIOS settings.

**Option 2: Automated PXE Boot**
```bash
./omnia.sh --run orchestrator --tags pxe_boot
```

**For PXE boot procedures, see:** [Provision Nodes](../HowTo/orchestrator/provision_nodes.md)

---

## Step 9: Verify Cluster

Verify that the Slurm cluster is operational after all nodes have booted and cloud-init has completed.

```bash
# On Slurm controller node
systemctl status slurmctld
sinfo

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

---

## Next Steps

After completing the SLURM deployment:
- Configure GPU support: [Slurm with GPU](../HowTo/Configure/slurm_with_gpu.md)
- Install NVIDIA HPC SDK: [NVIDIA HPC SDK Setup](../HowTo/Configure/setup_nvhpc_sdk.md)
- Customize Slurm configuration: [Configure Slurm](../HowTo/Configure/configure_slurm.md)

!!! info
    - [Set Up Slurm](../HowTo/orchestrator/deploy_slurm.md) -- Detailed Slurm setup guide
    - [Full Deployment](full_deployment.md) -- Add K8s to this Slurm deployment
    - [Prerequisites Checklist](prerequisites_checklist.md) -- Master checklist
    - [Slurm Troubleshooting](../Troubleshooting/orchestrator.md) -- Troubleshoot Slurm issues
