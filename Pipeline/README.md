# Omnia Automation GitLab CI/CD Pipeline

## Overview
This directory contains the GitLab CI/CD pipeline configuration for automating Omnia deployments. The pipeline enables users to edit configuration files through GitLab's web interface and automatically execute the automation workflow.

## Quick Start Guide

### Prerequisites
- GitLab server (CE or EE)
- GitLab Runner configured with shell executor
- Target OIM server accessible from GitLab Runner
- Python 3.x and required dependencies on Runner

### Setup Checklist
Before running the pipeline, ensure you have completed ALL these steps:

- [ ] **Step 1:** Clone repository and push to your GitLab server
- [ ] **Step 1a:** Edit `.gitlab-ci.yml` variables (AUTOMATION_REPO, AUTOMATION_BRANCH)
- [ ] **Step 2:** Install and register GitLab Runner
- [ ] **Step 3:** Configure GitLab CI/CD variables in project settings
- [ ] **Step 4:** Edit configuration files (`omnia_test_config.yml`, `omnia_test_credentials.yml`)
- [ ] **Step 5:** Verify dataset files in `datasets/project_default/`
- [ ] **Step 6:** Test SSH connectivity to OIM server
- [ ] **Step 7:** Trigger pipeline

### Setting Up Your GitLab Project

#### 1. Clone and Setup Repository
```bash
# Clone the omnia-artifactory repository
git clone -b automation-v2.2.0.0 https://github.com/dell/omnia-artifactory.git
cd omnia-artifactory

# Initialize git if not already done
git init

# Add your GitLab server as remote
git remote add origin http://YOUR_GITLAB_SERVER/YOUR_GROUP/omnia-automation.git

# Push to GitLab
git push -u origin --all
git push -u origin --tags
```

#### 1a. Edit Pipeline Configuration
After cloning, you MUST update the `.gitlab-ci.yml` file with your environment details:

```yaml
# Edit Pipeline/.gitlab-ci.yml
variables:
  AUTOMATION_REPO: "https://github.com/dell/omnia-artifactory.git"  # Automation repo URL
  AUTOMATION_BRANCH: "automation-v2.2.0.0"  # Automation branch
  REMOTE_WORK_DIR: "/root/omnia-artifactory"  # Path on target OIM server
  PIPELINE_VERSION: "2.2"  # Keep as is unless upgrading
```

#### 2. Configure GitLab Runner
```bash
# Install GitLab Runner
curl -L --output /usr/local/bin/gitlab-runner https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64
chmod +x /usr/local/bin/gitlab-runner
gitlab-runner install --user=gitlab-runner --working-directory=/home/gitlab-runner
gitlab-runner start

# Register the runner with your project
gitlab-runner register
# Enter GitLab URL: http://YOUR_GITLAB_SERVER
# Enter registration token (from Project → Settings → CI/CD → Runners)
# Enter description: omnia-automation-runner
# Enter tags: omnia,automation
# Enter executor: shell

# Install dependencies on Runner
sudo apt-get update && sudo apt-get install -y python3 python3-pip sshpass git
# OR for RHEL/CentOS/Rocky
sudo yum install -y python3 python3-pip sshpass git

# Install Python packages
pip3 install pyyaml
```

#### 3. Configure GitLab CI/CD Variables (REQUIRED)
Go to your GitLab project → Settings → CI/CD → Variables and add:

**Email Notification Variables:**
| Variable Name | Value Example | Description | Protected | Masked |
|--------------|---------------|-------------|-----------|---------|
| `EMAIL_RECIPIENTS` | `team@company.com,team@company.com` | Comma-separated email recipients | Yes | Yes |
| `EMAIL_SENDER` | `omnia@company.com` | Email sender address | Yes | Yes |

**Using Variables in Configuration:**
Instead of hardcoding sensitive data in `omnia_test_config.yml`, use CI/CD variables:
```yaml
# omnia_test_config.yml
oim_server_ip: "${OIM_SERVER_IP}"  # Will be replaced by GitLab variable
oim_ssh_user: "${OIM_SSH_USER}"
oim_ssh_password: "${OIM_SSH_PASSWORD}"
```

#### 4. Configure Your Deployment Files
Edit the following files in GitLab's web interface :

**Essential Configuration Files:**
- `omnia_test_config.yml` - Main configuration (OIM server details, deployment options)
- `omnia_test_credentials.yml` - Credentials (passwords)
- `datasets/project_default/` - All Omnia-specific configurations

#### 5. Trigger the Pipeline
```bash
# Option 1: Via GitLab UI
# Go to CI/CD → Pipelines → Run pipeline
# Select branch: main
# Click Run pipeline

## Configuration Files Reference

### Root Directory Files
| File | Purpose | Required |
|------|---------|----------|
| `omnia_test_config.yml` | Main automation configuration | Yes |
| `omnia_test_credentials.yml` | Sensitive credentials | Yes |
| `.gitlab-ci.yml` | Pipeline definition | Yes |
| `send_email.py` | Email notifications | Optional |

### Dataset Files (`datasets/project_default/`)
| File | Purpose | When Needed |
|------|---------|-------------|
| `network_spec.yml` | Network configuration | Provisioning |
| `omnia_config.yml` | Core Omnia settings | Always |
| `provision_config.yml` | Node provisioning | Provisioning |
| `pxe_mapping_file.csv` | PXE boot mappings | Provisioning |
| `software_config.json` | Software packages | Image building |
| `storage_config.yml` | Storage configuration | Storage setup |
| `telemetry_config.yml` | Monitoring setup | Telemetry |
| `security_config.yml` | Security settings | Security hardening |
| `high_availability_config.yml` | HA configuration | HA setup |
| `local_repo_config.yml` | Local repository | Local repo setup |
| `build_stream_config.yml` | Build streams | Image building |
| `gitlab_config.yml` | GitLab integration | GitLab features |
| `user_registry_credential.yml` | Registry credentials | Private registries |

## Pipeline Stages Explained

The pipeline executes the following stages sequentially:

```yaml
stages:
  - initialization       # Validates configs, extracts credentials
  - setup_environment   # Prepares target server, clones repo
  - oim_cleanup        # Removes existing containers
  - omnia_sh_uninstall # Uninstalls previous Omnia
  - oim_prereq_check   # Validates prerequisites
  - omnia_sh_install   # Installs Omnia core
  - prepare_oim        # Prepares OIM environment
  - local_repo         # Sets up local repository
  - build_image_x86_64 # Builds OS images
  - provision          # Provisions compute nodes
  - slurm             # Configures Slurm scheduler
  - kubernetes        # Sets up Kubernetes cluster
  - telemetry         # Configures monitoring
  - summary           # Generates reports
```

### Stage Dependencies
- Each stage depends on the successful completion of previous stages

### Email Notifications
Upon pipeline completion, an automated email will be sent to the configured recipients with:
- **HTML test reports** - Detailed test results from each stage
