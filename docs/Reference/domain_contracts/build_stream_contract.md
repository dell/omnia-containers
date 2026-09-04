# BuildStreaM Input/Output Contract

## Input Contract

### Input Files

| File | Location | Required | Description |
|------|----------|----------|-------------|
| `build_stream_config.yml` | `/opt/omnia/input/project_default/` | Yes | BuildStreaM configuration |
| `omnia_config.yml` | `/opt/omnia/input/project_default/` | Yes | Omnia cluster configuration |
| `catalog_rhel.json` | GitLab repository | Yes | Image catalog |

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `gitlab_host` | string | Yes | - | GitLab server hostname |
| `gitlab_project` | string | Yes | - | GitLab project name |
| `pipeline_type` | string | Yes | - | Pipeline type (build, deploy, clean) |

## Output Contract

### Output Files

| File | Location | Description |
|------|----------|-------------|
| `pipeline_status.yml` | `/opt/omnia/build_stream/output/` | Pipeline execution status |
| `catalog_manifest.yml` | `/opt/omnia/build_stream/output/` | Catalog manifest |

### Output Artifacts

- Built images from build pipeline
- Deployed nodes from deploy pipeline
- Pipeline execution logs
- Catalog updates

## Execution Flow

1. **Validate Configuration**: Check BuildStreaM configuration
2. **Deploy GitLab**: Deploy GitLab CI/CD infrastructure
3. **Configure Pipeline**: Configure build and deploy pipelines
4. **Execute Build Pipeline**: Build images from catalog
5. **Execute Deploy Pipeline**: Deploy images to nodes
6. **Cleanup**: Remove old image groups

## Related Documentation

- [Domain Overview](../../HowTo/build_stream/index.md)
- [Configuration Reference](../../Reference/Configuration/build_stream_config.md)



