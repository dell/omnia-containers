# BuildStreaM Domain Contract

**Deployment module**: BuildStreaM | **CLI identifier**: `build_stream`

## Upstream domain contract

The deploy pipeline consumes an Orchestrator-compatible
`pxe_mapping_file.csv`, produced by Discovery or maintained by an
administrator and staged in the managed GitLab project.

### `pxe_mapping_file.csv`

**Producer location**:
`$OMNIA_DATA_PATH/discovery/output/$OMNIA_PROJECT_NAME/bmc_pxe_mapping_file.csv`

**BuildStreaM-required staging location**:
`$OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/pxe_mapping_file.csv`

BuildStreaM reads the staged mapping file from this canonical location under
`OMNIA_DATA_PATH`.

#### Structure

The first row must contain the following column names in this order. Each
subsequent row describes one node.

```csv
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_node_x86_64,grp1,ABC1234,PARENT1,slurm-node1,02:00:00:00:00:11,192.0.2.11,02:00:00:00:00:12,198.51.100.11,InfiniBand.Slot.7-1,203.0.113.11
```

Review Discovery output before staging it. The reviewed, staged file is the
authoritative pipeline input. `PARENT_SERVICE_TAG`, `IB_NIC_NAME`, and `IB_IP`
can be empty when they do not apply to the node.

BuildStreaM infrastructure preparation does not require another domain's
status output.

## Output contract

### `build_stream_status.yml`

The `prepare` flow writes:

```text
$OMNIA_DATA_PATH/build_stream/output/project_default/build_stream_status.yml
```

| Field | Purpose |
|---|---|
| `overall_status` | The current writer records `prepared` after infrastructure preparation. |
| `build_stream_host` | Configured BSM host address. |
| `build_stream_port` | Configured BSM port. |
| `gitlab_host` | Configured GitLab host. |
| `gitlab_https_port` | Configured GitLab HTTPS port. |
| `gitlab_url` | Computed GitLab HTTPS base URL. |
| `bsm_api_url` | Computed BSM HTTPS base URL. |

The source does not generate `pipeline_status.yml` or
`catalog_manifest.yml` in the BuildStreaM project output directory.
Pipeline and job results are exposed through GitLab and BSM job state.

### Managed services and GitLab resources

| Output | Purpose |
|---|---|
| `omnia_postgres.service` | PostgreSQL state used by BSM. |
| `omnia_build_stream.service` | BSM FastAPI service. |
| `playbook-watcher.service` | Executes queued module playbooks. |
| GitLab project | Contains the catalog, module inputs, and parent/child CI pipeline files. |
| GitLab runner | Executes the managed build, deploy, and cleanup pipelines. |
| `miscellaneous/failed_nodes.json` | Deploy-pipeline retry state when node PXE boot or registration fails. |

A successful preparation is verified from `build_stream_status.yml`, the
three OIM services, the BSM health endpoint, and the managed GitLab project and
runner.

## Workflow tags

| Tag | Implemented behavior |
|---|---|
| No tag | Setup, validation, credentials, BSM preparation, and GitLab execution. |
| `precheck` | Checks the existing environment without collecting credentials. |
| `validate` | Validates the BuildStreaM domain settings. |
| `credentials` | Collects or updates BuildStreaM credentials. |
| `prepare` | Deploys PostgreSQL, BSM, and the playbook watcher. |
| `execute` | Deploys and configures GitLab CI/CD. |
| `build` | Runs both `prepare` and `execute`. |
| `cleanup` | Removes the GitLab and BuildStreaM infrastructure. |
| `upgrade` | Runs the current placeholder upgrade flow. |
| `rollback` | Runs the current placeholder rollback flow. |

## Related documentation

- [BuildStreaM](../../HowTo/build_stream/index.md)
- [Execute the build pipeline](../../HowTo/build_stream/execute_build_pipeline.md)
- [Execute the deploy pipeline](../../HowTo/build_stream/execute_deploy_pipeline.md)
- [Orchestrator contract](orchestrator_contract.md)
