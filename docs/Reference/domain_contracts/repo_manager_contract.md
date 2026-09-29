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
| `file_repos.<version>.<architecture>.<type>.<artifact>` | string | Version-qualified File or Python distribution URL. |
| `base_urls.<version>.<architecture>.<type>` | string | Version-qualified content-type URL derived from a ready File or Python distribution. |

The producer does not publish flat `*_base_url` or `offline_*_path` aliases.
Consumers must select the required OS version, architecture, and content type
from `base_urls`.

The active catalog determines which OS-version keys are published. A
single-version catalog publishes one version context; a multi-version catalog
publishes one context for each selected RHEL 10.x minor version in ascending
version order. The following table illustrates the current 10.0-only,
10.2-only, and combined examples:

| Example catalog selection | Ordered `execution_contexts` | `overall_status_by_version` keys | OS-version keys eligible for versioned content maps |
|---|---|---|---|
| Single-version example: RHEL 10.0 | RHEL 10.0 | `10.0` | `10.0` |
| Single-version example: RHEL 10.2 | RHEL 10.2 | `10.2` | `10.2` |
| Multi-version (hybrid) example: RHEL 10.0 and RHEL 10.2 | RHEL 10.0, then RHEL 10.2 | `10.0` and `10.2` | `10.0` and `10.2` |

The versioned content maps are `repositories`, `file_repos`, and `base_urls`.
They contain entries only for content selected by the catalog and available
from a ready Pulp distribution.

The following abbreviated example shows a successful RHEL 10.0 and RHEL 10.2
catalog execution:

```yaml
overall_status: "success"
cluster_os_type: "rhel"
repo_config: "partial"
execution_contexts:
  - context_id: "rhel_10.0"
    os_type: "rhel"
    os_version: "10.0"
    architectures: ["x86_64"]
  - context_id: "rhel_10.2"
    os_type: "rhel"
    os_version: "10.2"
    architectures: ["x86_64"]
overall_status_by_version:
  "10.0": "success"
  "10.2": "success"
repositories:
  "10.0":
    x86_64:
      baseos:
        url: "https://192.0.2.10:2225/pulp/content/.../rhel/10.0/baseos/"
  "10.2":
    x86_64:
      baseos:
        url: "https://192.0.2.10:2225/pulp/content/.../rhel/10.2/baseos/"
file_repos:
  "10.0":
    x86_64:
      tarball:
        example-tool: "https://192.0.2.10:2225/pulp/content/.../rhel/10.0/tarball/example-tool/"
  "10.2":
    x86_64:
      tarball:
        example-tool: "https://192.0.2.10:2225/pulp/content/.../rhel/10.2/tarball/example-tool/"
base_urls:
  "10.0":
    x86_64:
      tarball: "https://192.0.2.10:2225/pulp/content/.../rhel/10.0/tarball/"
  "10.2":
    x86_64:
      tarball: "https://192.0.2.10:2225/pulp/content/.../rhel/10.2/tarball/"
```

Repository URLs come from actual Pulp distributions. A missing required
distribution makes the affected version and aggregate status `failed`. During
a multi-version download, `overall_status` remains `in_progress` while later
contexts are pending and becomes `success` only after every selected context
completes. A failed context stops later contexts. Verified URLs for successful
versions can remain present while failed or pending version maps are empty.
When the active catalog changes, versions and architectures that are no longer
selected are removed from the generated contract.

The `status` operation publishes `repo_status.yml` atomically. It writes and
flushes a temporary file in the destination directory, sets mode `0644`, and
then replaces the current status file. If a required distribution is missing
after Pulp inspection completes, Repository Manager publishes a failed
manifest with empty maps for the affected version. If live status collection
or file publication fails before replacement completes, the task fails and no
new contract is guaranteed; verify that the output belongs to the current run
before passing it to a consumer.

Registry authentication references, usernames, passwords, and tokens are not
written to `repo_status.yml`. Selective cleanup removes the stale status file;
the `status` tag regenerates it from the current Pulp state.

### `repo_resync_status.yml`

**Location**:
`$OMNIA_DATA_PATH/repo_manager/output/<project>/repo_resync_status.yml`

The standalone `repo_sync.yml` operation reconciles only RPM repositories
referenced by the active catalog. It uses exact-mirror behavior so packages
removed from the upstream repository are removed from the replacement Pulp
publication. Container images, pip modules, tarballs, operating-system
repositories outside the active catalog, and other non-RPM artifacts are not
part of this operation.

| Field | Purpose |
|---|---|
| `overall_status` | Aggregate reconciliation status. |
| `orphan_cleanup` | Final Pulp orphan-cleanup status. |
| `repositories.<name>.sync_status` | Upstream synchronization result for one selected repository. |
| `repositories.<name>.cleanup_status` | Stale-package cleanup result. |
| `repositories.<name>.packages_added` | Count of packages added by reconciliation. |
| `repositories.<name>.packages_removed` | Count of packages removed by reconciliation. |
| `repositories.<name>.stale_packages_remaining` | Packages that should have been removed but remain. |

The cadence watcher accepts the contract only when the aggregate, orphan
cleanup, and every per-repository operation succeeded; every stale-package
count is zero; and the addition and removal counters are nonnegative integers.
It advances the cadence catalog only when at least one addition or removal is
reported.

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
| Top-level Ansible log | `/var/log/omnia/repo_manager/repo_manager.log` | Repository Manager playbook log. |

Runtime status and mirror files support idempotent reruns. Downstream components
consume `repo_status.yml`.

## Related documentation

- [Repository Manager](../../HowTo/repo_manager/index.md)
- [Create Local Repositories](../../HowTo/repo_manager/configure_repos.md)
- [Automate Build and Deployment with Cadence](../../HowTo/build_stream/execute_cadence_pipeline.md)
