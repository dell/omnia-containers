# Omnia Automation GitLab CI/CD Pipeline

## Overview

This directory contains a **multi-cluster** GitLab CI/CD pipeline that automates Omnia deployments across one or more HPC/AI clusters in parallel. Each cluster gets its own configuration dataset, SSH credentials, and independent pipeline execution - all driven from a single `.gitlab-ci.yml` file.

For a **single-cluster** setup, define one cluster in `pipeline/clusters/` and one entry in the pipeline matrix.

---

## Directory Structure

```
pipeline/
├── .gitlab-ci.yml                      # Pipeline definition (single file)
├── README.md                           # This file
├── generate_multi_cluster_datasets.py  # Per-cluster dataset generator
├── install_gitlab_cicd.py              # GitLab installation + CI/CD setup
├── requirements_gitlab_install.txt     # Python deps for install_gitlab_cicd.py
├── send_email.py                       # Email notification script
├── gitlab_admin_credentials.yml        # GitLab admin creds (ansible-vault encrypted)
└── clusters/                           # Cluster connection configurations
    ├── cluster1/
    │   ├── cluster.env
    │   └── credentials.yml
    ├── cluster2/
    │   ├── cluster.env
    │   └── credentials.yml
    └── cluster3/
        ├── cluster.env
        └── credentials.yml
```

Related directories at the repository root:

```
omnia-artifactory/
├── omnia_test_config.yml               # Global/shared automation config
├── omnia_test_credentials.yml          # Credentials template (for local runs)
├── datasets/                           # Generated & template datasets
│   ├── templates/                      # Jinja2 templates
│   ├── project_default/                # Default configuration set
│   ├── cluster1_config/                # Generated per-cluster datasets
│   ├── cluster2_config/
│   └── custom_overrides.yml.example    # Example overrides file
└── utility/
    └── generate_datasets.py            # Core dataset generation engine
```

---

## Prerequisites

- GitLab server (CE or EE) with a registered Runner (shell executor)
- Python 3 with `jinja2`, `pyyaml` on the machine running dataset generation
- `sshpass` and `git` installed on the GitLab Runner
- SSH access from the Runner to each target OIM server

---

## Quick Start

### 1. Configure Clusters

Edit each `pipeline/clusters/<name>/cluster.env` with your cluster details:

```bash
# pipeline/clusters/cluster1/cluster.env
CLUSTER_NAME="cluster1"
TARGET_IP="10.10.0.1"                    # OIM server IP
TARGET_USER="root"
TARGET_PASS="${CLUSTER1_TARGET_PASS}"     # GitLab CI/CD variable reference
DATASET="cluster1_config"                # Dataset folder name
BASE_TC="tc01_production_standard"       # Base template (optional)
```

### 2. Generate Datasets

```bash
cd pipeline/
python generate_multi_cluster_datasets.py --clean
```

This creates 17 configuration files per cluster under `datasets/<cluster>_config/`.

### 3. Set Passwords in GitLab

Go to **Settings > CI/CD > Variables** and add masked variables:

| Variable                | Value              | Masked |
|-------------------------|--------------------|--------|
| `CLUSTER1_TARGET_PASS`  | (cluster1 password) | Yes    |
| `CLUSTER2_TARGET_PASS`  | (cluster2 password) | Yes    |
| `CLUSTER3_TARGET_PASS`  | (cluster3 password) | Yes    |

Or use the interactive prompt:

```bash
python install_gitlab_cicd.py --skip-install --prompt-passwords
```

### 4. Push to GitLab and Run

```bash
cd /root/rohith/omnia-artifactory
git add pipeline/ datasets/
git commit -m "Add multi-cluster pipeline and datasets"
git push origin main
```

Trigger via **CI/CD > Pipelines > Run pipeline**.

---

## Pipeline Stages

The pipeline executes these stages sequentially, with each stage running in parallel across all clusters:

```
initialization          Validates cluster configs, writes per-cluster env files
    |
setup_environment       Clones repo on target, copies datasets, creates venv
    |
oim_cleanup             Removes existing containers (skipped on fresh install)
    |
omnia_sh_uninstall      Uninstalls previous Omnia (skipped if no core container)
    |
oim_prereq_check        Validates prerequisites on target server
    |
omnia_sh_install        Installs Omnia core via molecule
    |
prepare_oim             Prepares OIM environment
    |
local_repo              Sets up local package repository
    |
build_image_x86_64      Builds OS images inside omnia_core container
    |
provision               Provisions compute nodes via PXE
    |
slurm ──────────┐       Configures Slurm scheduler, DCGM, HPC benchmarks
                |
kubernetes ─────┤       Sets up Kubernetes cluster (parallel with slurm)
                |
telemetry ──────┘       Configures monitoring/telemetry
    |
summary                 Collects all reports, sends email notification
```

### Parallel Execution

Every stage uses GitLab's `parallel: matrix` strategy. With 3 clusters, each stage spawns 3 jobs that run concurrently:

```
initialization [cluster1]    initialization [cluster2]    initialization [cluster3]
         |                            |                            |
setup_environment [cluster1]  setup_environment [cluster2]  setup_environment [cluster3]
         |                            |                            |
        ...                          ...                          ...
```

---

## Pipeline Variables

Override these in **Settings > CI/CD > Variables** or when triggering a pipeline:

| Variable               | Default                                            | Description                                |
|------------------------|----------------------------------------------------|--------------------------------------------|
| `AUTOMATION_REPO`      | `https://github.com/dell/omnia-artifactory.git`   | Repository URL cloned on target servers    |
| `AUTOMATION_BRANCH`    | `automation-v2.2.0.0`                              | Branch to clone                            |
| `REMOTE_WORK_DIR`      | `/root/omnia-artifactory`                          | Working directory on target OIM servers    |
| `PIPELINE_VERSION`     | `2.2`                                              | Pipeline version identifier                |
| `CLUSTERS`             | `cluster1,cluster2,cluster3`                       | Comma-separated cluster list for validation|
| `DEFAULT_DATASET`      | `project_default`                                  | Fallback dataset if none specified         |
| `CONTAINER_NAME`       | `omnia_core`                                       | Podman container name                      |
| `SSH_CONNECT_TIMEOUT`  | `10`                                               | SSH connection timeout (seconds)           |
| `DEFAULT_TIMEOUT`      | `3h`                                               | Per-stage timeout                          |
| `TEST_SUITE_MARKER`    | `sanity`                                           | Pytest marker for molecule verify          |
| `EMAIL_RECIPIENTS`     | _(empty)_                                          | Comma-separated email addresses            |

---

## Cluster Configuration

### cluster.env Format

Each cluster needs a `pipeline/clusters/<name>/cluster.env` file:

```bash
# Required
CLUSTER_NAME="cluster1"                    # Unique identifier
TARGET_IP="10.10.0.1"                     # OIM server IP or hostname
TARGET_USER="root"                        # SSH username
TARGET_PASS="${CLUSTER1_TARGET_PASS}"      # SSH password (use variable reference)
DATASET="cluster1_config"                 # Dataset folder name in datasets/

# Optional
BASE_TC="tc01_production_standard"        # Base template for dataset generation
```

### Adding a New Cluster

1. Create the directory and env file:
   ```bash
   mkdir -p pipeline/clusters/cluster4
   cat > pipeline/clusters/cluster4/cluster.env <<'EOF'
   CLUSTER_NAME="cluster4"
   TARGET_IP="10.10.0.4"
   TARGET_USER="root"
   TARGET_PASS="${CLUSTER4_TARGET_PASS}"
   DATASET="cluster4_config"
   BASE_TC="tc01_production_standard"
   EOF
   ```

2. Create the credentials file:
   ```bash
   cp pipeline/clusters/cluster1/credentials.yml pipeline/clusters/cluster4/credentials.yml
   # Edit with cluster4-specific credentials
   ```

3. Generate the dataset:
   ```bash
   cd pipeline/
   python generate_multi_cluster_datasets.py --clusters cluster4 --clean
   ```

4. Update the pipeline matrix in `.gitlab-ci.yml` - add `cluster4` to every `CLUSTER: [...]` list and to the `CLUSTERS` variable.

5. Add `CLUSTER4_TARGET_PASS` as a masked CI/CD variable in GitLab.

### Removing a Cluster

1. Remove the cluster from every `CLUSTER: [...]` matrix in `.gitlab-ci.yml`.
2. Remove it from the `CLUSTERS` variable.
3. Delete `pipeline/clusters/<name>/` and optionally `datasets/<name>_config/`.

### Single-Cluster Setup

For a single cluster, keep one entry everywhere:

```yaml
# In .gitlab-ci.yml
variables:
  CLUSTERS: "cluster1"

# In every parallel: matrix: block
parallel:
  matrix:
    - CLUSTER: [cluster1]
```

---

## Dataset Generation

### Available Base Templates

| Template                    | Description                                          |
|-----------------------------|------------------------------------------------------|
| `tc01_production_standard`  | Production Standard -- Slurm+K8s, iDRAC+LDMS, OpenLDAP |
| `tc02_dell_storage`         | Dell Storage + Observability -- PowerScale, DNS, OME  |
| `tc03_minimal_hpc`          | Minimal HPC -- Slurm-only, PowerVault, kernel override|
| `tc04_k8s_multisubnet`      | K8s + Multi-Subnet + RHEL Subscription               |
| `tc05_full_dell_stack`      | Full Dell Stack -- multi-arch, air-gapped, BuildStream|
| `tc06_buildstream_x86`      | BuildStream x86_64 -- Slurm+K8s, LDMS, BuildStream   |

### Commands

```bash
cd pipeline/

# List available base templates
python generate_multi_cluster_datasets.py --list-base-tcs

# Generate datasets for all clusters
python generate_multi_cluster_datasets.py --clean

# Generate for specific clusters only
python generate_multi_cluster_datasets.py --clusters cluster1,cluster2 --clean

# Override the base template for all clusters
python generate_multi_cluster_datasets.py --base-tc tc03_minimal_hpc --clean
```

### Per-Cluster Base Templates

Set `BASE_TC` in each `cluster.env` to use different templates per cluster:

```bash
# pipeline/clusters/cluster1/cluster.env  (production standard)
BASE_TC="tc01_production_standard"

# pipeline/clusters/cluster2/cluster.env  (Slurm-only HPC)
BASE_TC="tc03_minimal_hpc"

# pipeline/clusters/cluster3/cluster.env  (K8s multi-subnet)
BASE_TC="tc04_k8s_multisubnet"
```

### Generated Files (17 per cluster)

Each dataset folder contains:

| File                           | Purpose                           |
|--------------------------------|-----------------------------------|
| `network_spec.yml`             | Network subnets, DNS, NTP, IPs   |
| `provision_config.yml`         | Node provisioning settings       |
| `omnia_config.yml`             | Core Omnia configuration         |
| `omnia_config_credentials.yml` | Omnia credentials                |
| `telemetry_config.yml`         | Monitoring/telemetry setup       |
| `telemetry_storage_config.yml` | Telemetry storage settings       |
| `storage_config.yml`           | Storage (NFS, PowerScale, etc.)  |
| `local_repo_config.yml`        | Local package repository         |
| `build_stream_config.yml`      | Build stream configuration       |
| `gitlab_config.yml`            | GitLab integration settings      |
| `high_availability_config.yml` | HA configuration                 |
| `pxe_mapping_file.csv`         | PXE boot MAC-to-IP mappings     |
| `software_config.json`         | Software packages to install     |
| `security_config.yml`          | Security hardening settings      |
| `discovery_config.yml`         | Node discovery settings          |
| `additional_cloud_init.yml`    | Cloud-init customizations        |
| `user_registry_credential.yml` | Container registry credentials   |

After generation, **review and customize** these files for each cluster (IPs, MACs, credentials, etc.) either locally or in GitLab's web editor.

---

## GitLab Setup

### Automated Setup

```bash
cd pipeline/

# Full install: installs GitLab, creates project, configures variables, generates datasets
python install_gitlab_cicd.py --generate-datasets --prompt-passwords

# Skip installation (GitLab already running): just configure variables and datasets



# Non-interactive mode
python install_gitlab_cicd.py --skip-install --non-interactive \
  --gitlab-url https://gitlab.example.com \
  --admin-token glpat-xxxxxxxxxxxx \
  --generate-datasets
```

### Manual Setup

#### 1. Clone and Push to GitLab

```bash
git clone -b automation-v2.2.0.0https://github.com/dell/omnia-artifactory.git
cd omnia-artifactory
git remote add gitlab http://YOUR_GITLAB_SERVER/root/omnia-automation.git
git push -u gitlab --all
```

#### 2. Install and Register GitLab Runner

```bash
# Install Runner
curl -L --output /usr/local/bin/gitlab-runner \
  https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64
chmod +x /usr/local/bin/gitlab-runner
gitlab-runner install --user=gitlab-runner --working-directory=/home/gitlab-runner
gitlab-runner start

# Register (get token from Project > Settings > CI/CD > Runners)
gitlab-runner register
# Executor: shell

# Install Runner dependencies
# RHEL/CentOS/Rocky:
yum install -y python3 python3-pip sshpass git
# Debian/Ubuntu:
apt-get install -y python3 python3-pip sshpass git

pip3 install pyyaml
```

#### 3. Configure CI/CD Variables

Go to **Project > Settings > CI/CD > Variables** and add:

| Variable               | Value                                              | Protected | Masked |
|------------------------|----------------------------------------------------|-----------|--------|
| `AUTOMATION_REPO`      | Your repo URL                                      | No        | No     |
| `AUTOMATION_BRANCH`    | `automation-v2.2.0.0`                              | No        | No     |
| `CLUSTER1_TARGET_PASS` | _(actual password)_                                | No        | Yes    |
| `CLUSTER2_TARGET_PASS` | _(actual password)_                                | No        | Yes    |
| `CLUSTER3_TARGET_PASS` | _(actual password)_                                | No        | Yes    |
| `EMAIL_RECIPIENTS`     | `user@example.com`                                 | No        | No     |

#### 4. Set Pipeline Configuration Path

Go to **Settings > CI/CD > General pipelines** and set:

- **CI/CD configuration file**: `pipeline/.gitlab-ci.yml`

#### 5. Prepare Configuration Files

Create these files in your GitLab repo root:

- `omnia_test_config.yml` -- main automation configuration
- `omnia_test_credentials.yml` -- sensitive credentials

#### 6. Trigger the Pipeline

Go to **CI/CD > Pipelines > Run pipeline**.

---

## Security Best Practices

- **Never hardcode passwords** in `cluster.env`. Use GitLab CI/CD variable references:
  ```bash
  TARGET_PASS="${CLUSTER1_TARGET_PASS}"
  ```
- **Mask sensitive variables** in GitLab (Settings > CI/CD > Variables > "Mask variable").
- **Protect branches** to prevent unauthorized pipeline triggers.
- Consider adding `pipeline/clusters/` to `.gitignore` if you want to keep env files local-only.

---

## Reports

Each stage produces HTML test reports per cluster, collected in `reports_<cluster>/`:

```
reports_cluster1/report_provision_cluster1_2026-07-21_14-30-00.html
reports_cluster2/report_provision_cluster2_2026-07-21_14-30-00.html
```

The **summary** stage aggregates all reports into `final_reports/` with a `pipeline_summary.txt`.

If `EMAIL_RECIPIENTS` is set, an email with the test report is sent via `send_email.py`.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `datasets/$DATASET` not found | Run `cd pipeline/ && python generate_multi_cluster_datasets.py --clean` |
| SSH connection timeout | Verify `TARGET_IP` in `cluster.env`, check firewall rules |
| `generate_datasets.py not found` | Ensure `utility/generate_datasets.py` exists at repo root |
| Password not resolving | Add the `CLUSTER<N>_TARGET_PASS` variable in GitLab CI/CD settings |
| Pipeline says "Cluster X not in list" | Add the cluster to the `CLUSTERS` variable and the matrix |
| `omnia_test_config.yml` not found | Create the file in the GitLab repo root |

---

## Email Notifications

The `send_email.py` script sends an HTML email with the test report attached after pipeline completion. Configure these variables:

| Variable           | Description                        |
|--------------------|------------------------------------|
| `EMAIL_RECIPIENTS` | Comma-separated recipient emails  |
| `SENDER_EMAIL`     | From address (optional)            |

The email includes:
- Pipeline trigger time and URL
- HTML test report as an attachment

---

## Command Reference

```bash
cd pipeline/

# Dataset generation
python generate_multi_cluster_datasets.py --list-base-tcs          # List templates
python generate_multi_cluster_datasets.py --clean                   # Generate all
python generate_multi_cluster_datasets.py --clusters cluster1 --clean  # Specific cluster

# GitLab setup
python install_gitlab_cicd.py --skip-install --generate-datasets    # Generate + upload
python install_gitlab_cicd.py --skip-install --prompt-passwords     # Set passwords
python install_gitlab_cicd.py --generate-datasets --prompt-passwords  # Full setup
```
