
# Log Management

Omnia maintains logs across playbook executions, container operations, and cluster activities. These logs are essential for monitoring, debugging, and troubleshooting deployments across the OIM, Kubernetes, and Slurm environments.

!!! warning

    Do not delete log files or the directories they reside in.

!!! tip

    To generate log files for a specific playbook, use the `cd` command to move into the playbook directory before running it. For example, run `cd local_repo` before executing the playbook to get dedicated local repo logs. If the directory is not changed, all playbook execution logs are consolidated under `/opt/omnia/log/core/playbooks`.

## Log locations

### Playbook logs

All Ansible playbook execution logs are written to the OIM host filesystem under `/opt/omnia/log/core/playbooks/`:

| Log File | Purpose | Playbook |
| --- | --- | --- |
| `discovery.log` | Discovery logs | `discovery/discovery.yml` |
| `local_repo.log` | Local repository logs | `local_repo/local_repo.yml` |
| `prepare_oim.log` | Prepare OIM logs | `prepare_oim/prepare_oim.yml` |
| `provision.log` | Provision logs | `provision/provision.yml` |
| `telemetry.log` | Telemetry logs | `telemetry/telemetry.yml` |
| `utils.log` | Utility logs | `utils/*.yml` |
| `credential_utility.log` | Credential utility logs | `credential_utility/get_config_credentials.yml` |
| `validation_omnia_project_default.log` | Input validation report logs | |
| `input_validation.log` | Input validation playbook logs | `input_validation/validate_config.yml` |
| `gitlab_build_stream.log` | GitLab BuildStreaM logs | |
| `build_image_<arch>.log` | Build image logs | `build_image_<arch>/build_image_<arch>.yml` |

### Core and container logs

| Location | Purpose |
| --- | --- |
| `/opt/omnia/log/openchami/*log` | OpenCHAMI playbook logs |
| `/opt/omnia/log/pulp/*log` | Pulp container logs |
| `/opt/omnia/log/local_repo/*log` | Local repo logs |
| `/opt/omnia/log/core/container/*log` | Core container logs |
| `/opt/omnia/log/build_stream/` | BuildStreaM pipeline logs |

!!! note

    BuildStreaM and GitLab log paths are available inside the BuildStreaM container.

### Slurm logs

On Slurm cluster nodes, logs are stored in standard Slurm log directories:

| Path | Description |
| --- | --- |
| `/var/log/slurm/slurmctld.log` | Slurm controller daemon log (on the control node). |
| `/var/log/slurm/slurmd.log` | Slurm compute daemon log (on each compute node). |
| `/var/log/slurm/slurmdbd.log` | Slurm database daemon log (job accounting). |

## Viewing Podman container logs on OIM

1. List all containers running on the OIM:

    ```bash title="Run on: OIM host"
    podman ps -a
    ```

    ```text title="Expected output"
    CONTAINER ID   IMAGE                                                        COMMAND                  CREATED        STATUS        PORTS                                        NAMES
    222d8d96554b   localhost/omnia_auth:1.0                                     /bin/sh -c mkdi…         2 days ago     Up 2 days     0.0.0.0:389->389/tcp, 0.0.0.0:636->636/tcp   omnia_auth
    0640a9adfce3   localhost/omnia_core:2.2                                                              2 days ago     Up 2 days     2222/tcp                                     omnia_core
    42515184e9ba   docker.io/pgsty/minio:RELEASE.2026-04-17T00-00-00Z           server /data –co…        2 days ago     Up 2 days     0.0.0.0:9000-9001->9000-9001/tcp             minio-server
    5bbce8efdc27   docker.io/pulp/pulp:3.80                                     /init                    2 days ago     Up 2 days     0.0.0.0:2225->2225/tcp, 80/tcp               pulp
    d0b76ac340c7   docker.io/library/postgres:16                                postgres                 2 days ago     Up 2 days     5432/tcp                                     omnia_postgres
    0608aa923b7c   docker.io/dellhpcomniaaisolution/omnia_build_stream:1.1                               2 days ago     Up 2 days                                                  omnia_build_stream
    251709e17ec2   docker.io/library/registry:3.1.0                             /etc/distribution…       2 days ago     Up 2 days     0.0.0.0:5000->5000/tcp                       registry
    992a9ca91d5d   docker.io/library/postgres:11.5-alpine                       postgres                 2 days ago     Up 2 days     5432/tcp                                     postgres
    b731b88c87ff   ghcr.io/openchami/local-ca:v0.2.6                            /step-ca.sh              2 days ago     Up 2 days     9000/tcp                                     step-ca
    ec2a4422424d   docker.io/oryd/hydra:v2.3                                    serve -c /etc/con…       2 days ago     Up 2 days                                                  hydra
    0751a15ca614   ghcr.io/openchami/opaal:v0.3.12                              /opaal/opaal serv…       2 days ago     Up 2 days                                                  opaal-idp
    72e566933565   ghcr.io/openchami/smd:v2.19.3                                /smd                     2 days ago     Up 2 days     27779/tcp                                    smd
    e95d50f8da14   ghcr.io/openchami/opaal:v0.3.12                              /opaal/opaal logi…       2 days ago     Up 2 days                                                  opaal
    3fac48412fe9   ghcr.io/openchami/bss:v1.32.2                                /bin/sh -c /usr/l…       2 days ago     Up 2 days     27778/tcp                                    bss
    81f488e6b5cb   ghcr.io/openchami/cloud-init:v1.3.0                          /usr/local/bin/cl…       2 days ago     Up 2 days                                                  cloud-init-server
    7e970ad459ca   cgr.dev/chainguard/haproxy:latest                            haproxy -f /usr/l…       2 days ago     Up 2 days     0.0.0.0:8081->80/tcp, 0.0.0.0:8443->443/tcp  haproxy
    5f5028bab1cd   ghcr.io/openchami/coresmd:v0.4.3                             /coredhcp                2 days ago     Up 2 days                                                  coresmd-coredhcp
    354f3305a7b8   ghcr.io/openchami/coresmd:v0.4.3                             /coredns                 2 days ago     Up 2 days                                                  coresmd-coredns
    ```

    !!! note

        Container IDs and image versions will vary on every system.

2. View logs from a specific container:

    ```bash title="Run on: OIM host"
    podman logs <container_name>
    ```

3. If the container is managed as a systemd service, view logs with:

    ```bash title="Run on: OIM host"
    journalctl -xeu <container_name>
    ```

## Viewing Kubernetes pod logs

1. List all namespaces and pods:

    ```bash title="Run on: Kubernetes control plane"
    kubectl get pods -A
    ```

2. Get the list of containers in a pod:

    ```bash title="Run on: Kubernetes control plane"
    kubectl get pods <pod_name> -o jsonpath='{.spec.containers[*].name}'
    ```

3. View logs for a specific container:

    ```bash title="Run on: Kubernetes control plane"
    kubectl logs <pod_name> -n <namespace> -c <container_name>
    ```

## Cluster log collection

Omnia provides a log collection playbook for gathering cluster logs from Kubernetes and Slurm nodes for debugging and support.

```bash title="Run on: omnia_core container"
ssh omnia_core
cd /omnia/log_collector
ansible-playbook collect.yml
```

### Collection modes

- **Full mode** (default): Collects all logs from target nodes.

    ```bash title="Run on: omnia_core container"
    ansible-playbook collect.yml
    ```

- **Curated support mode**: Excludes temporary and stale log files.

    ```bash title="Run on: omnia_core container"
    ansible-playbook collect.yml --tags curated_support
    ```

### Output artifacts

| Artifact | Description |
| --- | --- |
| Workspace | `/opt/omnia/collector_logs` |
| Bundle | `omnia_logs_<YYYYMMDD-HHMMSS>.tar.gz` |
| Metadata | `metadata.json` (included in bundle) |
| Checksum | `.sha256` file for integrity verification |

!!! note

    - PXE mapping file must exist at `/opt/omnia/input/project_default/`.
    - Nodes must be reachable from the OIM.

!!! warning

    Logs are stored in `/var`. Ensure sufficient space is allocated to the `/var` partition.

!!! info

    - [General Troubleshooting](../Troubleshooting/general.md) -- Uses logs as a primary diagnostic tool.
    - [Best Practices Checklist](best_practices_checklist.md) -- Storage and maintenance best practices.
