# Clean up the OIM

Use each domain's cleanup workflow to remove the services and artifacts that
it owns. After the required domain cleanups succeed, remove the shared Omnia
execution environment with the Main cleanup command.

Cleanup runs from the Omnia Infrastructure Manager (OIM). Keep the shared
virtual environment installed until every required domain cleanup completes.

!!! danger

    Cleanup is destructive. Depending on the selected domain and options, it
    can remove containers, repositories, images, credentials, cluster
    configuration, telemetry workloads, persistent data, backups, and
    shared-storage content. Back up all required data before continuing.

## When to use OIM cleanup

- Reset a failed or experimental deployment.
- Remove selected Omnia domains before redeployment.
- Return a lab or test OIM to a clean state.
- Remove the shared Omnia environment after domain services are removed.

## Prerequisites

- Log in to the OIM as a user with the privileges required by every selected
  cleanup workflow.
- Use the same `OMNIA_PROJECT_NAME` and resolved domain data paths used for
  deployment. In particular, preserve `ORCHESTRATOR_DATA_PATH` when
  Orchestrator used a custom root; when it is unset, Orchestrator uses
  `<OMNIA_DATA_PATH>/orchestrator`.
- Confirm that the Omnia virtual environment is available.
- Stop or drain workloads that use the services or storage being removed.
- Back up project inputs, credentials, repository content, images, telemetry
  data, databases, log archives, configuration backups, and shared-storage
  data that must be retained.
- Review the cleanup guide for each deployed domain before selecting optional
  data deletion or credential preservation behavior.

## Cleanup scope by domain

| Domain | Default cleanup scope |
|---|---|
| `build_stream` | Removes GitLab, BuildStreaM services, the watcher, PostgreSQL service, runtime artifacts, and BuildStreaM credentials. PostgreSQL data is preserved by default. |
| `telemetry` | Removes all enabled telemetry sources and sinks and deletes the stored telemetry credential file. Source-owned persistent volumes are removed; Kafka, VictoriaMetrics, and VictoriaLogs volumes are preserved by default. |
| `orchestrator` | Removes enabled OpenCHAMI, OpenLDAP, Slurm, Kubernetes, storage-mount, and generated Orchestrator resources. It prompts independently before deleting Slurm and Kubernetes shared data and removes credentials by default. |
| `discovery` | Removes the current project's Discovery output contents and credentials while preserving the output directory and other staged inputs. |
| `image_build_manager` | Removes MinIO when locally managed, the image registry, build artifacts, domain runtime data, logs, and Image Build Manager credentials. |
| `repo_manager` | Removes the Pulp deployment, Pulp data, repository integration, logs, and Repo Manager credentials. Credentials and logs are removed by default. |
| `utils` | Removes cluster-log artifacts, unattended-installation temporary files and credentials, all OIM log-backup runs, and all Slurm configuration backup runs. |

To preserve Image Build Manager services and remove only selected or all built
artifacts, use [Clean up built images](cleanup_built_images.md) instead of the
full `image_build_manager` cleanup tag.

## Clean up deployed domains

Run only the following sections for domains that have deployed or generated
state. Keep the listed reverse dependency order so consumers are removed
before the services they depend on. For example, remove Telemetry before its
Kubernetes environment and remove Image Build Manager before Repo Manager.

### Complete full-cleanup command sequence

Use the following block only when every listed domain was deployed and a
complete data reset is intended. If a domain was not deployed, remove its
command from the block before running it. The subshell exits immediately if a
command fails, which prevents cleanup from continuing to a dependency or the
shared environment.

!!! danger

    This sequence deletes PostgreSQL data, all Telemetry source and sink
    volumes, and Slurm and Kubernetes shared data. It then removes the Omnia
    environment and all remaining data under `OMNIA_DATA_PATH`. Confirm that
    required data has been backed up outside every cleanup target.

    Image Build Manager cleanup does not delete objects from an external
    PowerScale S3 provider. Review and remove external objects separately only
    when their deletion is intended.

```bash title="Run on: OIM host"
(
  set -e
  cd <OMNIA_SOURCE_PATH>/src/main

  ./omnia.sh --run build_stream --tags cleanup \
    -e postgres_backup=false
  ./omnia.sh --run telemetry --tags cleanup \
    -e delete_sinks_volume=true
  ./omnia.sh --run orchestrator --tags cleanup \
    -e cleanup_slurm=true -e cleanup_k8s=true
  ./omnia.sh --run discovery --tags cleanup
  ./omnia.sh --run image_build_manager --tags cleanup
  ./omnia.sh --run repo_manager --tags cleanup
  ./omnia.sh --run utils --tags cleanup

  ./omnia.sh --cleanup --all
)
```

Review each command's final Ansible recap as the sequence runs. Main full
cleanup still performs its safety check and requests the exact confirmation
`yes`; `set -e` stops the sequence when that safety check or any earlier
command fails.

The following sections explain each command and its less-destructive options.
For individual execution, choose the applicable command tab. Do not remove the
shared virtual environment while another domain cleanup still needs it.

### 1. Clean up BuildStreaM

Skip this section when BuildStreaM was not deployed. The full cleanup removes
the managed GitLab deployment, BuildStreaM service, watcher, automation
artifacts, PostgreSQL service, NFS runtime directories, and BuildStreaM
credentials. Ensure the configured GitLab host is reachable and its stored SSH
credential is available before starting.

PostgreSQL data and volumes are preserved by default:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run build_stream --tags cleanup
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/build_stream/playbooks
    ansible-playbook build_stream.yml --tags cleanup
    ```

To remove PostgreSQL data and volumes as part of a complete reset, run instead:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run build_stream --tags cleanup -e postgres_backup=false
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/build_stream/playbooks
    ansible-playbook build_stream.yml --tags cleanup -e postgres_backup=false
    ```

To remove an individual BuildStreaM image group while retaining the deployed
domain, do not run full domain cleanup. Use
[Clean up BuildStreaM image groups](build_stream/cleanup_operations.md).

### 2. Clean up Telemetry

Run Telemetry cleanup while its Kubernetes cluster remains available. Full
cleanup removes all enabled Telemetry sources and sinks and deletes the stored
Telemetry credential file and Vault key. Source-owned persistent volumes are
deleted; Kafka, VictoriaMetrics, and VictoriaLogs volumes are preserved by
default:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run telemetry --tags cleanup
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
    ansible-playbook telemetry.yml --tags cleanup
    ```

Delete the preserved sink volumes only when a complete Telemetry data reset is
intended:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run telemetry --tags cleanup -e delete_sinks_volume=true
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
    ansible-playbook telemetry.yml --tags cleanup -e delete_sinks_volume=true
    ```

When retaining the rest of Telemetry, use the applicable component tag instead
of `cleanup`: `cleanup_idrac`, `cleanup_ldms`, `cleanup_ome`,
`cleanup_powerscale`, `cleanup_ufm`, `cleanup_vast`, `cleanup_kafka`,
`cleanup_victoria_metrics`, or `cleanup_victoria_logs`.

### 3. Clean up Orchestrator

Back up required Slurm and Kubernetes shared data before this step. Preview the
full cleanup plan without changing the environment:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    DRY_RUN=true ./omnia.sh --run orchestrator --tags cleanup
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
    DRY_RUN=true ansible-playbook orchestrator.yml --tags cleanup
    ```

For an interactive run, use:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags cleanup
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
    ansible-playbook orchestrator.yml --tags cleanup
    ```

Orchestrator prompts independently before deleting Slurm and Kubernetes shared
data. Only the exact response `yes` deletes the selected component's data. Any
other response preserves its data, but cleanup still unmounts that storage and
removes its `/etc/fstab` entry.

For a reviewed noninteractive decision, set both choices explicitly. For
example, the following command deletes Slurm data and preserves Kubernetes
data:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags cleanup \
      -e cleanup_slurm=true -e cleanup_k8s=false
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
    ansible-playbook orchestrator.yml --tags cleanup \
      -e cleanup_slurm=true -e cleanup_k8s=false
    ```

The current implementation does not consume `cleanup_credentials=false`,
although source comments mention it. Full cleanup therefore removes the
Orchestrator credential file and Vault key. To preserve them or clean only one
component, follow
[Clean up Orchestrator](../HowTo/orchestrator/cleanup_orchestrator.md) and use
the standalone component flow with explicit component tags.

!!! warning

    `SKIP_APPROVAL=true` approves deletion of Slurm and Kubernetes shared data
    when `cleanup_slurm` or `cleanup_k8s` is omitted. Set both choices
    explicitly before using noninteractive cleanup.

### 4. Clean up Discovery

Discovery cleanup affects only the current project. It empties the project
output directory and removes `discovery_credentials.yml` and its Vault key by
default. Copy any discovered node mapping needed for later reuse before
running:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run discovery --tags cleanup
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/discovery/playbooks
    ansible-playbook discovery.yml --tags cleanup
    ```

To empty the current project's output while preserving its credentials, run:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run discovery --tags cleanup \
      -e cleanup_credentials=false
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/discovery/playbooks
    ansible-playbook discovery.yml --tags cleanup \
      -e cleanup_credentials=false
    ```

Other Discovery input files and Discovery logs are preserved. For the
credentials-only operation, see
[Clean up Discovery data](../HowTo/discovery/index.md#clean-up-discovery-data).

### 5. Clean up Image Build Manager

Full Image Build Manager cleanup removes the locally managed MinIO service and
data, the local registry and its data, build work directories, credentials,
domain logs, and `/root/.s3cfg` when local MinIO is used. It also empties the
shared Image Build Manager `output` and `log` roots, affecting every project
that uses the configured domain data path:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run image_build_manager --tags cleanup
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/image_build_manager/playbooks
    ansible-playbook image_build_manager.yml --tags cleanup
    ```

When PowerScale is the configured S3 provider, full cleanup preserves
`/root/.s3cfg` and does not delete objects from PowerScale. If the goal is only
to remove selected or all built images while retaining Image Build Manager
services, use
[Clean up built images](cleanup_built_images.md) instead.

### 6. Clean up Repo Manager

Run Repo Manager cleanup after Image Build Manager no longer needs its package
content. Full cleanup removes the Pulp service, container image, Pulp data,
repository integration, credentials, and logs. Credentials and logs are
removed by default without prompting:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run repo_manager --tags cleanup
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
    ansible-playbook repo_manager.yml --tags cleanup
    ```

To retain credentials and logs for a later deployment, run instead:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run repo_manager --tags cleanup \
      -e cleanup_credentials=false -e cleanup_logs=false
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
    ansible-playbook repo_manager.yml --tags cleanup \
      -e cleanup_credentials=false -e cleanup_logs=false
    ```

To remove selected repositories or artifacts while retaining Pulp, use
[Pulp cleanup](pulp_cleanup.md) instead of full Repo Manager cleanup.

### 7. Clean up Utils

The general Utils cleanup removes cluster-log artifacts, unattended-install
temporary files and credentials, all OIM log-backup runs, and all Slurm
configuration backup runs:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags cleanup
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils/playbooks
    export ANSIBLE_CONFIG=../ansible.cfg
    ansible-playbook utils.yml --tags cleanup
    ```

The backup cleanup workflows do not apply retention or ask for confirmation.
When any artifact or backup class must remain, follow
[Clean up Utils](../HowTo/utils/cleanup_utils.md) and run only the applicable
scoped cleanup tags.

## Remove the shared Omnia environment

After every required domain cleanup succeeds, choose one Main cleanup mode.
For complete command behavior and verification, see
[Maintain the Main environment](maintain_main_environment.md).

To remove the installed environment while preserving domain input, output,
and log data under `OMNIA_DATA_PATH`, run:

```bash title="Run on: OIM host"
./omnia.sh --cleanup
```

To perform an explicitly approved full reset, run:

```bash title="Run on: OIM host"
./omnia.sh --cleanup --all
```

The full-reset safety check runs before the confirmation prompt. It refuses to
continue when it finds an unsafe data path or deployed, generated, nonempty,
or unrecognized domain state. No files are removed when this check fails. Run
the matching domain cleanup or review and remove the reported retained path,
then retry.

When the safety check passes, review the displayed paths and type exactly
`yes`. The command removes the installed environment and all remaining data
under `OMNIA_DATA_PATH`. Data in custom component roots or external storage is
removed only by the applicable domain cleanup workflow.

!!! warning

    Adding `--skip-approval` skips the Main confirmation prompt but does not
    bypass the full-reset safety checks.

## Verification

- Confirm that every selected domain cleanup has a successful Ansible recap.
- Verify that the intended services, containers, Kubernetes resources, and
  mounts are absent.
- Confirm that credentials, persistent volumes, shared data, and backups were
  preserved or removed according to the selected options.
- After normal Main cleanup, confirm that the virtual environment and installed
  environment files are absent and `OMNIA_DATA_PATH` remains.
- After `--cleanup --all`, confirm that the configured `OMNIA_DATA_PATH` is
  absent.

## Next steps

- Run `./omnia.sh --setup-venv` to recreate the shared environment when
  required.
- Initialize and deploy only the required domains in dependency order.
- See [Clean up Orchestrator](../HowTo/orchestrator/cleanup_orchestrator.md) for
  component-level Orchestrator cleanup.
- See [Pulp cleanup](pulp_cleanup.md) for selective repository cleanup.

## Troubleshooting

- **A domain cleanup fails**: Stop the sequence, correct the reported problem,
  and rerun that domain cleanup before removing its dependencies.
- **BuildStreaM cannot clean the GitLab host**: Confirm that the configured
  GitLab host is reachable and that the BuildStreaM credential file still
  contains the GitLab SSH password.
- **Orchestrator shared data was preserved unexpectedly**: Only the exact
  response `yes` approves interactive deletion. Rerun with reviewed
  `cleanup_slurm` and `cleanup_k8s` values when a noninteractive decision is
  required.
- **Main full cleanup reports incomplete domain cleanup**: No files were
  removed. Run the cleanup tag for the reported domain. Preserve and then
  remove any reported status, log, output, or backup file that is intentionally
  retained before retrying.
- **A custom data path remains**: Main full cleanup removes only
  `OMNIA_DATA_PATH`. Rerun the owning domain cleanup with the original project
  and component path configuration.
- **The virtual environment was removed too early**: Set up the OIM again to
  restore the shared environment, complete the required domain cleanup, and
  then rerun the selected Main cleanup mode.
