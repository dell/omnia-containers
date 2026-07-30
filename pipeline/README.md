# GitLab Installation & Dataset Configuration Guide

This guide walks you through installing GitLab, configuring the multi-cluster CI/CD pipeline, and generating cluster datasets.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Dataset Configuration](#dataset-configuration)
3. [Automated GitLab Installation](#automated-gitlab-installation)
4. [Manual GitLab Installation](#manual-gitlab-installation)
5. [Cluster Management](#cluster-management)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **Operating System**: RHEL/CentOS/Rocky 8+ or Debian/Ubuntu 20.04+
- **RAM**: Minimum 8GB (16GB+ recommended for production)
- **Disk Space**: Minimum 50GB free
- **CPU**: 4 cores minimum

### Software Requirements

```bash
# Python 3 and dependencies
python3
python3-pip

# Git
git

# SSH utilities
sshpass

# For dataset generation
jinja2
pyyaml
```

### Install Dependencies

**RHEL/CentOS/Rocky:**
```bash
yum install -y python3 python3-pip git sshpass
pip3 install pyyaml jinja2
```

**Install script dependencies:**
```bash
cd pipeline/
pip3 install -r requirements_gitlab_install.txt
```

---

## Dataset Configuration

### Understanding Datasets

Each cluster requires a dataset containing 17 configuration files:
- `software_config.json` - Software packages, architecture, repo policy
- `network_spec.yml` - Admin/IB networks, subnets, DNS, NTP
- `provision_config.yml` - PXE mapping, DNS toggle, kernel override, cloud-init
- `omnia_config.yml` - Slurm + K8s cluster definitions
- `omnia_config_credentials.yml` - Credentials (auto-encrypted via Vault)
- `storage_config.yml` - NFS/VAST/PowerVault mounts, S3 config
- `telemetry_config.yml` - Telemetry sources, sinks, collection targets
- `telemetry_storage_config.yml` - VictoriaMetrics, Kafka, Vector resource limits
- `local_repo_config.yml` - Repos, registries, RHEL subscriptions, air-gap mirrors
- `discovery_config.yml` - BMC / OME discovery settings
- `security_config.yml` - LDAP connection type
- `high_availability_config.yml` - K8s HA virtual IP
- `build_stream_config.yml` - BuildStream CI/CD pipeline settings
- `gitlab_config.yml` - GitLab deployment config
- `additional_cloud_init.yml` - Custom cloud-init (write_files / runcmd)
- `user_registry_credential.yml` - Container registry credentials
- `pxe_mapping_file.csv` - Node inventory (MACs, IPs, functional groups)

### Generate Datasets

**List available base templates:**
```bash
cd pipeline/
python3 generate_multi_cluster_datasets.py --list-base-tcs
```

**Available templates:**
| Template | Description |
|----------|-------------|
| `tc01_production_standard` | Production Standard -- Slurm+K8s, iDRAC+LDMS, OpenLDAP |
| `tc02_dell_storage` | Dell Storage + Observability -- PowerScale, DNS, OME |
| `tc03_minimal_hpc` | Minimal HPC -- Slurm-only, PowerVault, kernel override |
| `tc04_k8s_multisubnet` | K8s + Multi-Subnet + RHEL Subscription |
| `tc05_full_dell_stack` | Full Dell Stack -- multi-arch, air-gapped, BuildStream |
| `tc06_buildstream_x86` | BuildStream x86_64 -- Slurm+K8s, LDMS, BuildStream |

**Generate datasets for all clusters:**
```bash
python3 generate_multi_cluster_datasets.py --clean
```

**Generate for specific clusters:**
```bash
python3 generate_multi_cluster_datasets.py --clusters cluster1,cluster2 --clean
```

**Use specific base template:**
```bash
python3 generate_multi_cluster_datasets.py --base-tc tc03_minimal_hpc --clean
```

### Customize Generated Datasets

After generation, review and customize the files in `datasets/<cluster>_config/`:

```bash
# Edit network configuration
vi datasets/cluster1_config/network_spec.yml

# Edit PXE mappings
vi datasets/cluster1_config/pxe_mapping_file.csv

# Edit storage configuration
vi datasets/cluster1_config/storage_config.yml
```

### Upload Datasets to GitLab

**Manual upload:**
```bash
cd /root/omnia-artifactory
git add datasets/
git commit -m "Add cluster datasets"
git push origin main
```

**Automated upload via script:**
```bash
python3 install_gitlab_cicd.py --skip-install --generate-datasets
```

---

## Automated GitLab Installation

### Automated Setup (Recommended)

The `install_gitlab_cicd.py` script automates the entire setup process. **HTTPS is configured by default** with a self-signed certificate.

```bash
cd pipeline/

# Full installation: install GitLab, configure project, generate datasets
python3 install_gitlab_cicd.py --generate-datasets
```

**What this does:**
1. ✅ Installs GitLab server with HTTPS (self-signed certificate)
2. ✅ Configures external URL
3. ✅ Creates GitLab project
4. ✅ Sets up CI/CD variables
5. ✅ Generates cluster datasets
6. ✅ Uploads configuration files
7. ✅ Registers GitLab runner with 'omnia' and 'shell' tags
8. ✅ Exits with error if any critical stage fails

**Skip HTTPS configuration:**
```bash
python3 install_gitlab_cicd.py --generate-datasets --skip-https
```

### Skip GitLab Installation

If GitLab is already installed:

```bash
# Configure existing GitLab and generate datasets
python3 install_gitlab_cicd.py --skip-install --generate-datasets
```

### Non-Interactive Mode

For automation/CI:

```bash
python3 install_gitlab_cicd.py \
  --skip-install \
  --non-interactive \
  --gitlab-url https://gitlab.example.com \
  --admin-token glpat-xxxxxxxxxxxx \
  --generate-datasets
```

---

## Manual GitLab Installation

### Step 1: Install GitLab Server

**Debian/Ubuntu:**
```bash
# Add GitLab repository
curl -sS https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.deb.sh | sudo bash

# Install GitLab
apt-get install -y gitlab-ce

# Configure GitLab
EXTERNAL_URL="https://gitlab.example.com" \
  GITLAB_OMNIBUS_CONFIG="letsencrypt['enable']=false;nginx['redirect_http_to_https']=false" \
  gitlab-ctl reconfigure
```

**RHEL/CentOS/Rocky:**
```bash
# Add GitLab repository
curl -sS https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.rpm.sh | sudo bash

# Install GitLab
yum install -y gitlab-ce

# Configure GitLab
EXTERNAL_URL="https://gitlab.example.com" \
  GITLAB_OMNIBUS_CONFIG="letsencrypt['enable']=false;nginx['redirect_http_to_https']=false" \
  gitlab-ctl reconfigure
```

### Step 2: Configure Firewall

```bash
# Configure firewall for GitLab access
python3 install_gitlab_cicd.py --firewall-only

# Or restrict to specific IPs
python3 install_gitlab_cicd.py --firewall-only --allowed-ips 192.168.1.0/24,10.0.0.100
```

### Step 3: Configure HTTPS

**HTTPS is configured by default during installation.** To skip HTTPS and use HTTP:

```bash
python3 install_gitlab_cicd.py --skip-https
```

For manual HTTPS configuration with self-signed certificate:
```bash
python3 install_gitlab_cicd.py --skip-install --configure-firewall
```

### Step 4: Create GitLab Project

1. Log in to GitLab as root
2. Create a new project named `omnia-automation`
3. Note the project path (e.g., `root/omnia-automation`)

### Step 5: Install GitLab Runner

**use the automated runner registration:**
```bash
python3 install_gitlab_cicd.py --register-runner
```

**Or**

```bash
# Download and install gitlab-runner
curl -L --output /usr/local/bin/gitlab-runner \
  https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64
chmod +x /usr/local/bin/gitlab-runner

# Install and start service
gitlab-runner install --user=root --working-directory=/home/gitlab-runner
gitlab-runner start

# Register runner
gitlab-runner register
# Follow prompts:
# - GitLab instance URL: https://gitlab.example.com
# - Registration token: Get from Project > Settings > CI/CD > Runners
# - Executor: shell
```

### Step 6: Clone Repository to GitLab

**Note:** If using the automated `install_gitlab_cicd.py` script, this step is handled automatically. Only perform this if doing a completely manual setup.

```bash
# Clone the omnia-artifactory repository
git clone -b automation-v2.2.0.0 https://github.com/dell/omnia-containers.git
cd omnia-containers

# Add GitLab remote
git remote add gitlab https://gitlab.example.com/root/omnia-automation.git

# Push to GitLab
git push -u gitlab --all
```

### Step 7: Configure CI/CD Variables

Go to **Project > Settings > CI/CD > Variables** and add:

| Variable | Value | Protected | Masked |
|----------|-------|-----------|--------|
| `AUTOMATION_REPO` | https://github.com/dell/omnia-containers.git | No | No |
| `AUTOMATION_BRANCH` | automation-v2.2.0.0 | No | No |
| `REMOTE_WORK_DIR` | /root/omnia-containers | No | No |
| `GIT_CLONE_BASE_DIR` | /root | No | No |
| `PIPELINE_VERSION` | 2.2 | No | No |
| `CLUSTERS` | cluster1,cluster2,cluster3 | No | No |
| `CONTAINER_NAME` | omnia_core | No | No |
| `SSH_CONNECT_TIMEOUT` | 30 | No | No |
| `TEST_SUITE_MARKER` | sanity | No | No |
| `EMAIL_SENDER` | noreply@example.com | No | No |
| `EMAIL_RECIPIENTS` | admin@example.com | No | No |
| `SMTP_SERVER` | localhost | No | No |
| `SMTP_PORT` | 587 | No | No |
| `CLUSTER1_TARGET_PASS` | (password) | No | Yes |
| `CLUSTER2_TARGET_PASS` | (password) | No | Yes |
| `CLUSTER3_TARGET_PASS` | (password) | No | Yes |

**Note:** Cluster-specific variables (CLUSTER1_BASE_TC, CLUSTER1_CLUSTER_NAME, etc.) are automatically configured from `pipeline/clusters/<name>/cluster.env` files.

---

## Cluster Management

### Add a New Cluster

**1. Create cluster directory and configuration:**
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

**2. Copy and edit credentials:**
```bash
cp pipeline/clusters/cluster1/omnia_test_credentials.yml pipeline/clusters/cluster4/omnia_test_credentials.yml
# Edit with cluster4-specific credentials
vi pipeline/clusters/cluster4/omnia_test_credentials.yml
```

**Note:** Cluster credentials files are **not encrypted**. They are stored as plain text YAML files in the repository.

**3. Generate dataset:**
```bash
cd pipeline/
python3 generate_multi_cluster_datasets.py --clusters cluster4 --clean
```

**4. Update pipeline matrix:**
Edit `.gitlab-ci.yml` and add `cluster4` to all `CLUSTER: [...]` lists and the `CLUSTERS` variable.

**5. Add GitLab CI/CD variable:**
Add `CLUSTER4_TARGET_PASS` as a masked variable in GitLab.

### Remove a Cluster

**1. Update pipeline matrix:**
Remove the cluster from all `CLUSTER: [...]` matrices in `.gitlab-ci.yml`.

**2. Remove from CLUSTERS variable:**
Update the `CLUSTERS` variable to exclude the removed cluster.

**3. Delete configuration:**
```bash
rm -rf pipeline/clusters/cluster4
rm -rf datasets/cluster4_config
```

### Single-Cluster Setup

For a single cluster, simplify the configuration:

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

## Advanced Configuration

### HTTPS Configuration

HTTPS is configured by default with a self-signed certificate during installation. To skip HTTPS and use HTTP:

```bash
python3 install_gitlab_cicd.py --skip-https
```

To re-enable HTTPS manually:
```bash
python3 install_gitlab_cicd.py --skip-install
```

### Configure Firewall Rules

**Public access:**
```bash
python3 install_gitlab_cicd.py --configure-firewall
```

**Restrict to specific IPs:**
```bash
python3 install_gitlab_cicd.py --allowed-ips 192.168.1.0/24,10.0.0.100
```

### Register GitLab Runner Standalone

If you need to register a runner separately:

```bash
# Using saved vault credentials
python3 install_gitlab_cicd.py --register-runner

# With explicit token
python3 install_gitlab_cicd.py --register-runner --admin-token glpat-xxxxxxxxxxxx
```

**Note:** The runner is registered with 'omnia' and 'shell' tags. The token regex now supports dots (e.g., `glrt-Xs.abcd1234`).

### Test Report Changes

The test report (`automation_library/core/functions/report_func.py`) has been updated with the following changes:

1. **Detailed test results now appear before playbook execution logs** in the HTML report
2. **Pass rate calculation excludes skipped tests** - only considers passed + failed tests
3. **Suite pass rates also exclude skipped tests** for more accurate metrics
4. **Total duration has been removed** from summary cards and suite breakdown table

These changes make the report more focused on actual test execution results rather than including skipped tests in the pass rate calculation.

### Script Command-Line Options

The `install_gitlab_cicd.py` script has the following command-line options:

| Option | Description |
|--------|-------------|
| `--gitlab-url` | GitLab server URL |
| `--admin-username` | GitLab admin username (fixed as 'root', no prompt) |
| `--admin-password` | GitLab admin password (pre-fills the prompt) |
| `--admin-token` | GitLab personal access token |
| `--project-name` | GitLab project name (default: omnia-automation) |
| `--project-path` | GitLab project path (default: root/omnia-automation) |
| `--skip-install` | Skip GitLab installation (assume already installed) |
| `--generate-datasets` | Generate per-cluster datasets |
| `--artifactory-path` | Path to omnia-artifactory repo |
| `--base-tc` | Base test case for dataset generation |
| `--clusters` | Comma-separated cluster names |
| `--configure-firewall` | Configure firewall for GitLab access |
| `--allowed-ips` | Comma-separated list of IPs/CIDRs to allow |
| `--skip-firewall` | Skip firewall configuration entirely |
| `--firewall-only` | Only configure firewall, skip GitLab operations |
| `--skip-https` | Skip HTTPS configuration (HTTPS is default) |
| `--non-interactive` | Run in non-interactive mode |
| `--register-runner` | Only register GitLab runner |

**Key Changes:**
- `--enable-https` replaced with `--skip-https` (HTTPS is now default)
- Admin username is fixed as 'root' (no longer prompts)
- Cluster credentials are no longer encrypted

---

## Troubleshooting

### GitLab Installation Issues

**Problem:** GitLab fails to start
```bash
# Check GitLab status
gitlab-ctl status

# Check logs
gitlab-ctl tail

# Reconfigure
gitlab-ctl reconfigure
```

**Problem:** Port conflicts
```bash
# Check what's using port 80/443
netstat -tlnp | grep -E ':80|:443'

# Stop conflicting services
systemctl stop nginx
systemctl stop httpd
```

### Dataset Generation Issues

**Problem:** Template not found
```bash
# List available templates
python3 generate_multi_cluster_datasets.py --list-base-tcs
```

**Problem:** Cluster directory missing
```bash
# Ensure cluster directory exists
ls -la pipeline/clusters/

# Create if missing
mkdir -p pipeline/clusters/<cluster_name>
```

### Runner Registration Issues

**Problem:** Runner not connecting
```bash
# Check runner status
gitlab-runner status

# Check runner logs
gitlab-runner verify

# Restart runner
gitlab-runner restart
```

**Problem:** SSL certificate verification failed
```bash
# The script handles self-signed certificates automatically
# If manual registration fails, use:
gitlab-runner register --tls-ca-file /etc/gitlab/ssl/<hostname>.crt
```

### Common Errors

| Error | Solution |
|-------|----------|
| `datasets/$DATASET not found` | Run `python3 generate_multi_cluster_datasets.py --clean` |
| `TARGET_IP empty` | Set `TARGET_IP` in `pipeline/clusters/<name>/cluster.env` |
| `Password not resolving` | Add `CLUSTER<N>_TARGET_PASS` variable in GitLab CI/CD settings |
| `Cluster not in list` | Add cluster to `CLUSTERS` variable and matrix in `.gitlab-ci.yml` |
| `SSH connection timeout` | Verify `TARGET_IP` and firewall rules |
| `Runner not found` | Run `python3 install_gitlab_cicd.py --register-runner` |

---

## Verification

After installation, verify everything is working:

### 1. Check GitLab Status
```bash
gitlab-ctl status
```

### 2. Check Runner Status
```bash
gitlab-runner status
```

### 3. Verify Project Files
```bash
# Check pipeline files
ls -la pipeline/

# Check cluster configs
ls -la pipeline/clusters/

# Check datasets
ls -la datasets/
```

### 4. Trigger Test Pipeline

1. Go to GitLab project
2. Navigate to **CI/CD > Pipelines**
3. Click **Run pipeline**
4. Verify pipeline runs successfully

---

## Next Steps

After installation and configuration:

1. **Review generated datasets** - Customize IPs, MACs, and credentials
2. **Test single cluster** - Run pipeline on one cluster first
3. **Scale to multi-cluster** - Add additional clusters as needed
4. **Configure email notifications** - Set up `EMAIL_RECIPIENTS` variable
5. **Monitor pipelines** - Check pipeline status and reports

---

## Additional Resources

- **Main Pipeline README**: `pipeline/README.md` - Complete pipeline documentation
- **Script Reference**: `pipeline/README.md#install_gitlab_cicd-py-script-reference`
- **GitLab Documentation**: https://docs.gitlab.com/
- **Omnia Documentation**: Refer to project documentation

---

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs in `/var/log/gitlab/` and `/var/log/gitlab-runner/`
3. Check pipeline logs in GitLab CI/CD interface
