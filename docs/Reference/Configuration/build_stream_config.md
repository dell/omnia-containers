# build_stream Config Reference

The `build_stream_config.yml` file configures BuildStreaM CI/CD pipelines.

## Location

```
/opt/omnia/input/project_default/build_stream_config.yml
```

## Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `gitlab_host` | string | Yes | - | GitLab server hostname |
| `gitlab_project` | string | Yes | - | GitLab project name |
| `gitlab_https_port` | integer | No | 443 | GitLab HTTPS port |
| `pipeline_type` | string | Yes | - | Pipeline type (build, deploy, clean) |
| `catalog_path` | string | Yes | - | Catalog file path |

## Usage Example

```yaml title="File: /opt/omnia/input/project_default/build_stream_config.yml"
gitlab_host: gitlab.example.com
gitlab_project: omnia-build
gitlab_https_port: 443
pipeline_type: build
catalog_path: catalog_rhel.json
```

## Related Configuration

- [omnia_env.md](omnia_env.md)
- [Domain Contract](../domain_contracts/build_stream_contract.md)



