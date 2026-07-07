# build_stream_config.yml Reference

File path: `/opt/omnia/input/project_default/build_stream_config.yml`

This file configures the BuildStreaM catalog-driven CI/CD deployment pipeline,
including GitLab integration and pipeline behavior settings.

## BuildStreaM Configuration Parameters

--8<-- "html/build_stream_config.html"

## Usage example

```yaml title="File: /opt/omnia/input/project_default/build_stream_config.yml"
---
enable_build_stream: false
build_stream_host_ip: "10.5.0.100"
build_stream_port: 8010
aarch64_inventory_host_ip: ""
```
