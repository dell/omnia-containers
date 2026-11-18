# build_stream_config.yml

The consolidated BuildStreaM configuration controls the BuildStreaM Manager
(BSM) API and the managed GitLab deployment. It replaces the former separate
BuildStreaM and GitLab configuration files.

## Location

```text
$OMNIA_DATA_PATH/build_stream/input/project_default/build_stream_config.yml
```

The current entry playbook fixes the project directory to `project_default`.

## Configuration parameters

| Parameter | Type | Requirement | Default |
|---|---|---|---|
| `enable_build_stream` | boolean | Required | None |
| `build_stream_host_ip` | IPv4 string | Required when enabled | Empty |
| `build_stream_port` | integer | Required when enabled | `8010` |
| `gitlab_host` | IPv4 string | Required for GitLab execution | Empty |
| `gitlab_project_name` | string | Optional | `omnia-catalog` |
| `gitlab_project_visibility` | string | Optional: `private`, `internal`, or `public` | `private` |
| `gitlab_default_branch` | string | Optional | `main` |
| `gitlab_https_port` | integer | Optional | `443` |
| `gitlab_min_storage_gb` | integer | Optional | `20` |
| `gitlab_min_memory_gb` | integer | Optional | `4` |
| `gitlab_min_cpu_cores` | integer | Optional | `2` |
| `gitlab_puma_workers` | integer | Optional | `2` |
| `gitlab_sidekiq_concurrency` | integer | Optional | `10` |
| `cadence.enabled` | boolean | Optional | `false` |
| `cadence.interval_seconds` | integer | Optional; minimum `86400` (1 day) | `604800` (7 days) |
| `cadence.gitlab_repo_path` | string | Required and nonempty when cadence is enabled | Empty |
| `cadence.playbook_name` | string | Optional; retain the allow-listed `repo_sync.yml` value | `repo_sync.yml` |
| `cadence.sync_timeout_seconds` | integer | Optional; minimum `60` | `3600` |
| `cadence.sync_poll_interval_seconds` | integer | Optional; `1` through `300` | `10` |
| `log_tail_lines_default` | integer | Optional; `1` through `log_tail_lines_max` | `50` |
| `log_tail_lines_max` | integer | Optional; `1` through `10000` | `10000` |
| `max_log_response_bytes` | integer | Optional; `1024` through `52428800` (50 MiB) | `10485760` (10 MiB) |
| `log_query_rate_limit` | integer | Optional; minimum `1` | `60` |
| `log_query_max_concurrent` | integer | Optional; minimum `1` | `5` |
| `log_ci_preview_lines` | integer | Optional; `1` through `log_tail_lines_max` | `50` |

Ports must be from 1 through 65535. Resource minimums and worker counts must be
positive integers. Unknown fields are rejected.

`PIPELINE_TYPE` is a GitLab pipeline variable, not a field in this YAML file.
The supported values are `build`, `deploy`, `cadence`, and `cleanup`.

BuildStreaM uses the same image-group identifier across all pipeline stages.
The identifier combines the catalog identifier and version in the format
`<catalog.identifier>-v<catalog.version>`.

The cadence settings control the periodic watcher operation. They do not
belong in either catalog JSON file. `gitlab_repo_path` must identify a writable
local clone of the managed GitLab project on the OIM. The watcher reads this
configuration when `playbook-watcher.service` starts.

### Pipeline log observability settings

The `log_*` and `max_log_response_bytes` parameters control how BuildStreaM
returns the execution logs of pipeline stages that run an Ansible playbook.
You retrieve these logs through the BSM API request
`GET /api/v1/jobs/{job_id}/logs?stage=<stage>&tail_lines=<n>`. Stages that do
not run a playbook, such as `parse-catalog`, have no execution log. BuildStreaM
redacts secrets when it writes a log and again when it serves the log. For the
procedure, see
[View Stage Execution Logs](../../HowTo/build_stream/execute_build_pipeline.md#view-stage-execution-logs).

All of these parameters are optional. Omit a parameter to keep its default.

| Parameter | Description |
|---|---|
| `log_tail_lines_default` | Number of lines returned for a stage log when the API request omits `tail_lines`. |
| `log_tail_lines_max` | Largest `tail_lines` value that the API accepts. A request for more lines returns an error. |
| `max_log_response_bytes` | Maximum number of log bytes returned for one stage, for a tail request or for `full=true`. When the log is larger, BuildStreaM drops the oldest content first and flags the response as `truncated`. |
| `log_query_rate_limit` | Number of log query requests allowed for each API client each minute. Requests above the limit receive HTTP `429`. |
| `log_query_max_concurrent` | Number of log query requests served at the same time across all clients. Requests above the limit receive HTTP `503` with a `Retry-After` header. |
| `log_ci_preview_lines` | Number of execution-log lines that the GitLab CI job console previews when a playbook stage finishes or fails. Omnia pushes this value to the GitLab project as the CI/CD variable `BSM_LOG_TAIL_LINES` each time you run the `build_stream` playbook. |

The `omnia_build_stream` container reads these values when it starts. After you
change them, re-run the `build_stream` playbook or restart the container.

## Usage example

```yaml title="File: /opt/omnia/build_stream/input/project_default/build_stream_config.yml"
enable_build_stream: true
build_stream_host_ip: "172.16.107.254"
build_stream_port: 8010
gitlab_host: "172.16.107.20"
gitlab_project_name: "omnia-catalog"
gitlab_project_visibility: "private"
gitlab_default_branch: "main"
gitlab_https_port: 443
gitlab_min_storage_gb: 20
gitlab_min_memory_gb: 4
gitlab_min_cpu_cores: 2
gitlab_puma_workers: 2
gitlab_sidekiq_concurrency: 10

cadence:
  enabled: false
  interval_seconds: 604800
  gitlab_repo_path: ""
  playbook_name: "repo_sync.yml"
  sync_timeout_seconds: 3600
  sync_poll_interval_seconds: 10

log_tail_lines_default: 50
log_tail_lines_max: 10000
max_log_response_bytes: 10485760
log_query_rate_limit: 60
log_query_max_concurrent: 5
log_ci_preview_lines: 50
```

## Related configuration

- [Main environment](omnia_env.md)
- [BuildStreaM contract](../domain_contracts/build_stream_contract.md)
- [BuildStreaM](../../HowTo/build_stream/index.md)
- [Automate Build and Deployment with Cadence](../../HowTo/build_stream/execute_cadence_pipeline.md)
