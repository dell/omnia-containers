
# gitlab_config.yml Reference

File path: `/opt/omnia/input/gitlab_config.yml`

This file configures GitLab deployment settings for the BuildStreaM catalog
pipeline, including host, project, network, and resource parameters.

## Parameters

--8<-- "html/gitlab_config.html"

## Usage example
```yaml title="File: /opt/omnia/input/gitlab_config.yml"
---
# Target host
gitlab_host: "192.168.1.50"

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

!!! note

    - HTTPS is always enabled for GitLab deployment.
    - GitLab credentials are managed separately via `get_config_credentials`.
    - The target host must be configured in `build_stream/gitlab/inventory/hosts.ini`.
