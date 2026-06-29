
# build_stream_config.yml Reference


File path: `/opt/omnia/input/project_default/build_stream_config.yml`

This file configures the BuildStreaM catalog-driven CI/CD deployment pipeline,
including GitLab integration and pipeline behavior settings.

## Parameter reference


### GitLab settings


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `gitlab_enabled` | Boolean | No | `false` | Enable GitLab deployment for BuildStreaM CI/CD pipelines. |
| `gitlab_server` | String | Conditional | (none) | Hostname or IP of the GitLab server. Required when `gitlab_enabled` is `true`. |
| `gitlab_port` | Integer | No | `443` | HTTPS port for the GitLab web interface and API. |
| `gitlab_external_url` | String | Conditional | (none) | Public-facing URL of the GitLab instance (e.g., `https://gitlab.hpc.example.com`). Used in pipeline configuration and webhook URLs. |
| `gitlab_admin_password` | String | Conditional | (vault-managed) | GitLab root/admin password. Set via `credentials_utility.yml`. |
| `gitlab_runner_token` | String | Conditional | (vault-managed) | Registration token for GitLab Runners. Set via `credentials_utility.yml`. |

### Pipeline settings


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `buildstream_catalog_path` | String | No | `/opt/omnia/buildstream/catalog` | Path to the BuildStreaM declarative catalog on the OIM. The catalog defines the desired cluster state. |
| `buildstream_pipeline_branch` | String | No | `main` | Git branch in the BuildStreaM repository that triggers pipeline execution. |
| `buildstream_auto_trigger` | Boolean | No | `true` | Automatically trigger pipelines when catalog changes are pushed. Set to `false` for manual pipeline execution only. |
| `buildstream_retry_count` | Integer | No | `3` | Number of retry attempts for failed pipeline stages. |
| `buildstream_timeout` | Integer | No | `3600` | Maximum pipeline execution time in seconds (default: 1 hour). |

### GitLab Runner settings


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `runner_executor` | String | No | `shell` | GitLab Runner executor type. Accepted values: `shell`, `docker`, `kubernetes`. |
| `runner_concurrent` | Integer | No | `4` | Maximum number of concurrent pipeline jobs per runner. |
| `runner_tags` | List | No | `["omnia", "buildstream"]` | Tags assigned to the runner for job matching. |

## Usage example


```yaml title="File: /opt/omnia/input/project_default/build_stream_config.yml"
gitlab_enabled: true
gitlab_server: "10.5.0.100"
gitlab_port: 443
gitlab_external_url: "https://gitlab.hpc.example.com"

buildstream_catalog_path: "/opt/omnia/buildstream/catalog"
buildstream_pipeline_branch: "main"
buildstream_auto_trigger: true
buildstream_retry_count: 3
buildstream_timeout: 3600

runner_executor: "shell"
runner_concurrent: 4
runner_tags:
  - omnia
  - buildstream
```


!!! info

    - [Playbook Reference](../Playbooks/playbook_reference.md) -- BuildStreaM-related
      playbooks.
    - [Minimum Nodes](../ClusterRequirements/minimum_nodes.md) -- Minimum nodes
      for BuildStreaM deployments (8+).
