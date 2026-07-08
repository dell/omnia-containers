# gitlab_config.yml Reference

File path: `/opt/omnia/input/project_default/gitlab_config.yml`

This file configures the GitLab instance for BuildStreaM, including host settings, project configuration, and resource requirements.

## GitLab Configuration Parameters

--8<-- "html/gitlab_config.html"

## Usage example

```yaml title="File: /opt/omnia/input/project_default/gitlab_config.yml"
---
# Target host
gitlab_host: "10.5.0.100"

# Project settings
gitlab_project_name: "omnia-catalog"
gitlab_project_visibility: "private"
gitlab_default_branch: "main"

# Network
gitlab_https_port: 443

# Minimum requirements
gitlab_min_storage_gb: 20
gitlab_min_cpu_cores: 2

# Performance tuning
gitlab_puma_workers: 2
gitlab_sidekiq_concurrency: 10
```
