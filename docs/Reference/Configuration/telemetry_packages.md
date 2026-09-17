# telemetry_packages.yml

This file is the package manifest for Telemetry container images, Helm charts,
Git repositories, and Python modules.

## Location

```text
<OMNIA_DATA_PATH>/telemetry/input/<OMNIA_PROJECT_NAME>/telemetry_packages.yml
```

## Parameters

| Parameter | Type | Required | Default or description |
|---|---|---|---|
| `install_mode` | string | Mandatory | `offline` or `online`; default is `offline`. |
| `repo_url` | string | Optional | Pulp base URL required by runtime validation in offline mode. |
| `k8s_cluster_mount` | absolute path | Mandatory | Kubernetes NFS mount where Telemetry packages are staged. |
| `slurm_cluster_mount` | string | Mandatory | Slurm mount used for LDMS configuration and data. |
| `container_registry` | string | Optional | Optional registry prefix override for air-gapped deployments. |
| `images` | object | Conditional | Image references grouped by subsystem. |
| `helm_charts` | object | Conditional | Chart entries containing `package`, `filename`, and `online_url`. |
| `git_repos` | object | Conditional | Repository entries containing `package`, `filename`, `online_url`, and `version`. |
| `pip_modules` | object | Conditional | Python modules grouped by component; each package value is a scalar version string. |

For offline installation, artifact paths are derived from `repo_url` and the
package metadata. For online installation, the source uses the configured
upstream URLs and image references.

## Usage example

```yaml title="File: <OMNIA_DATA_PATH>/telemetry/input/<OMNIA_PROJECT_NAME>/telemetry_packages.yml"
install_mode: "offline"
repo_url: "https://192.0.2.10:2225/pulp/content/offline_repo/cluster/x86_64/rhel/10.0"
k8s_cluster_mount: "/opt/omnia/k8s_mount"
slurm_cluster_mount: "/share_omnia"
container_registry: ""

images:
  vector:
    vector: "docker.io/timberio/vector:0.54.0-debian"

helm_charts:
  strimzi_kafka_operator:
    package: "strimzi-kafka-operator-helm-3-chart-1.1.0"
    filename: "strimzi-kafka-operator-helm-3-chart-1.1.0.tar.gz"
    online_url: "https://github.com/strimzi/strimzi-kafka-operator/releases/download/1.1.0/strimzi-kafka-operator-helm-3-chart-1.1.0.tgz"

pip_modules:
  idrac:
    kubernetes: "33.1.0"
    pymysql: "1.1.2"
```

Telemetry data is stored under `<OMNIA_DATA_PATH>/telemetry`, and
`OMNIA_PROJECT_NAME` defaults to `project_default`. The staged source file
contains the complete version-pinned package manifest.

## Related configuration

- [Telemetry configuration](telemetry_config.md)
- [Telemetry contract](../domain_contracts/telemetry_contract.md)
