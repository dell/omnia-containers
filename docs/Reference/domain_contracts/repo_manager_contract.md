# Repository Manager Domain Contract

**Deployment module**: Repository Manager | **CLI identifier**: `repo_manager`

## Upstream domain contract

Repository Manager does not require another deployment domain's status
output.

## Output contract

### `repo_status.yml`

**Location**:
`$OMNIA_DATA_PATH/repo_manager/output/<project>/repo_status.yml`

**Producer**: `generate_local_repo_access` module, run by the `status` tag.

**Consumers**: Image Build Manager and cluster provisioning workflows.

The current producer does not write a `schema_version` or `contract_version`
field. Consumers determine compatibility by validating the required fields
directly.

| Field | Type | Purpose |
|---|---|---|
| `overall_status` | string | Aggregate readiness across selected catalog contexts. |
| `cluster_os_type` | string | Catalog operating-system type. |
| `execution_contexts` | list | Ordered OS-version and architecture contexts. |
| `overall_status_by_version` | object | Per-version `pending`, `success`, or `failed` state. |
| `repo_config` | string | Effective repository policy reported by the generator. |
| `repo_manager.port` | integer | Pulp HTTPS host port. |
| `repo_manager.certificates` | object | Public Pulp certificate path and directory. |
| `repositories.<version>.<architecture>` | object | RPM distribution URLs and optional DNF priorities. |
| `registries` | object | Configured private-registry endpoints and non-secret TLS settings. |
| `file_repos.<architecture>` | object | File and Python distribution URLs by content type and artifact. |
| `*_base_url` and `offline_*_path` | string | Content-type base URLs and backward-compatible URLs. |

Repository URLs come from actual Pulp distributions. A missing required
distribution makes the affected version and aggregate status `failed`. During
a multi-version download, `overall_status` remains `in_progress` while later
contexts are pending and becomes `success` only after every selected context
completes.

The `status` operation publishes `repo_status.yml` atomically. It writes and
flushes a temporary file in the destination directory, sets mode `0644`, and
then replaces the current status file. If status collection fails or a required
distribution is unavailable, Repository Manager publishes a fail-closed
manifest with `overall_status: failed` and without consumable repository URLs.
If file publication itself fails, the task fails and no new contract is
published.

Registry authentication references, usernames, passwords, and tokens are not
written to `repo_status.yml`. Selective cleanup removes the stale status file;
the `status` tag regenerates it from the current Pulp state.

### Managed services and content

The `prepare` operation creates or configures these resources:

| Output | Location or name | Purpose |
|---|---|---|
| Systemd service | `pulp.service` | Enabled Pulp Podman Quadlet service. |
| Quadlet | `/etc/containers/systemd/pulp.container` | Pulp container definition. |
| HTTPS endpoint | `https://<pulp_server_ip>:<pulp_server_port>` | Pulp API, content, and OCI registry endpoint. |
| CA certificate | `$OMNIA_DATA_PATH/repo_manager/pulp_config/settings/certs/pulp_webserver.crt` | Client trust certificate. |
| Pulp CLI | `/usr/local/bin/pulp` | Managed CLI configured for HTTPS access. |
| Host trust anchor | `/etc/pki/ca-trust/source/anchors/omnia-pulp.crt` | System CA trust. |

Content stored in Pulp is the authoritative downloadable output. Files under
`offline_repo` are staging content rather than the downstream contract.

### Runtime state and logs

| Output | Location | Purpose |
|---|---|---|
| Package status | `$OMNIA_DATA_PATH/repo_manager/log/<os>/<version>/<architecture>/<group>/status.csv` | Per-package and artifact state for a catalog group. |
| Group status | `$OMNIA_DATA_PATH/repo_manager/log/<os>/<version>/<architecture>/groups_status.csv` | Overall state for resolved groups. |
| Mirror indexes | `$OMNIA_DATA_PATH/repo_manager/log/<os>/<version>/mirror_status/` | Catalog package ownership and Pulp mirror state. |
| Execution summary | `$OMNIA_DATA_PATH/repo_manager/log/<os>/catalog_execution_summary.yml` | Ordered contexts and aggregate run state. |
| Top-level Ansible log | `/var/log/omnia/repo_manager/repo_manager.log` | Repo Manager playbook log. |

Runtime status and mirror files support idempotent reruns. Downstream components
consume `repo_status.yml`.

## Related documentation

- [Repository Manager](../../HowTo/repo_manager/index.md)
- [Create Local Repositories](../../HowTo/repo_manager/configure_repos.md)
