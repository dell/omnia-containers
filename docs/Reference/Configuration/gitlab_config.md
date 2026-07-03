# gitlab_config.yml Reference

File path: `/opt/omnia/input/project_default/gitlab_config.yml`

This file configures the GitLab instance for BuildStreaM, including host settings, project configuration, and resource requirements.

!!! note
    - HTTPS is always enabled for GitLab deployment.
    - GitLab credentials are managed separately via `get_config_credentials`.
    - The target host must be configured in `build_stream/gitlab/inventory/hosts.ini`.

## Parameter reference

| Parameter | Mandatory/Optional | Description |
| --- | --- | --- |
| `gitlab_host` | Mandatory | IP address of the target host where GitLab will be deployed. Must be accessible from the OIM server. |
| `gitlab_project_name` | Mandatory | Name of the GitLab project that Omnia creates or manages. **Default value**: `omnia-catalog`. This project is created automatically if it does not exist. |
| `gitlab_project_visibility` | Mandatory | Visibility options that you can set for the GitLab project. **Possible Values**: `private` (Project access must be granted explicitly for each user), `internal` (The project can be cloned by any logged‑in user), `public` (The project can be cloned without any authentication). |
| `gitlab_default_branch` | Mandatory | The default branch used for repository and API operations. **Default value**: `main`. This branch is used as the default for all operations. |
| `gitlab_https_port` | Mandatory | HTTPS port exposed via GitLab NGINX. **Default value**: `443`. Must be between 1-65535. Must not conflict with other services. |
| `gitlab_min_storage_gb` | Mandatory | Free disk space validated before install. **Default value**: `20`. GitLab requires at least 20GB of free disk space. |
| `gitlab_min_cpu_cores` | Mandatory | Minimum CPU core count validated before install. **Default value**: 2. More cores may be needed for production workloads. |
| `gitlab_puma_workers` | Mandatory | Number of worker processes. **Default value**: 2. Scale with CPU cores (recommended: 1-2 workers per CPU core). |
| `gitlab_sidekiq_concurrency` | Mandatory | Background job concurrency. **Default value**: 10. Adjust based on available memory and workload. |

--8<-- "html/gitlab_config.html"

## Usage example
```yaml title="File: /opt/omnia/input/gitlab_config.yml"
---
# Target host
gitlab_host: ""
# Project settings
gitlab_project_name: "omnia-catalog"
gitlab_project_visibility: "private"
gitlab_default_branch: "main"
# Network
gitlab_https_port: 443
# Minimum requirements
gitlab_min_storage_gb: 20
gitlab_min_memory_gb: 4
gitlab_min_cpu_cores: 2
# Performance tuning
gitlab_puma_workers: 2
gitlab_sidekiq_concurrency: 10
```
