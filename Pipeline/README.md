# Omnia Automation GitLab CI/CD Pipeline

## Overview
This directory contains the GitLab CI/CD pipeline configuration for automating Omnia deployments. The pipeline enables users to edit configuration files through GitLab's web interface and automatically execute the automation workflow.

## Quick Start Guide

### Prerequisites
- GitLab server (CE or EE)
- GitLab Runner configured with shell executor
- Target OIM server accessible from GitLab Runner
- Python 3.x and required dependencies on Runner

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
sudo yum install -y python3 python3-pip sshpass git

# Install Python packages
pip3 install pyyaml
```

#### 3. Configure Your Deployment
Edit the following files in GitLab's web interface or locally:

**Essential Configuration Files:**
- `omnia_test_config.yml` - Main configuration (OIM server details, deployment options)
- `omnia_test_credentials.yml` - Credentials (passwords)
- `datasets/project_default/` - All omnia-specific configurations

#### 4. Trigger the Pipeline
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
  - omnia_sh_uninstall # Uninstalls previous Omnia core
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
  

## Support and Resources

- **Omnia Documentation**: https://omnia-doc.readthedocs.io/
- **GitLab CI/CD Docs**: https://docs.gitlab.com/ee/ci/
- **Ansible Documentation**: https://docs.ansible.com/
- **Issue Tracker**: https://github.com/dell/omnia/issues
- **Dell Support**: https://www.dell.com/support

## License
This project is licensed under the Apache License 2.0. See LICENSE file for details.

---
*Last Updated: January 2025*
*Version: 2.2.0.0*
