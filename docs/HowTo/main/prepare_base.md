# Prepare base infrastructure

## Overview

Use `./omnia.sh --prepare-base` after setting up the Omnia Infrastructure
Manager (OIM) to validate and prepare the infrastructure required by the core
deployment workflow. The command processes Repo Manager, Image Build Manager,
and Orchestrator in that order for each lifecycle phase.

| Phase | Repo Manager | Image Build Manager | Orchestrator |
|---|---|---|---|
| Validation | `precheck` | `validate` | `validate` |
| Credentials | `credentials` | `credentials` | `credentials` |
| Preparation | `prepare` | `prepare` | `prepare` |

Preparation deploys the Pulp service, the image registry, MinIO when it is the
selected S3 provider, and the OpenCHAMI services. It also deploys OpenLDAP when
the selected catalog enables it.

This command does not synchronize repository content, generate
`repo_status.yml`, build operating-system images, generate `build_status.yml`,
or provision cluster nodes.

## Prerequisites

- Complete [Set up the OIM](setup_oim.md). The Python virtual environment
  configured by `OMNIA_VENV_PATH` must exist.
- Configure the installed environment in `/etc/omnia/omnia.env`, including a
  valid `SYSTEM_ADMIN_NIC_IPV4` and `CATALOG_FILE_PATH`.
- Review the staged inputs for each domain that will be prepared:

    ```text
    $OMNIA_DATA_PATH/repo_manager/input/$OMNIA_PROJECT_NAME/
    $OMNIA_DATA_PATH/image_build_manager/input/$OMNIA_PROJECT_NAME/
    $ORCHESTRATOR_DATA_PATH/input/$OMNIA_PROJECT_NAME/
    ```

  `ORCHESTRATOR_DATA_PATH` defaults to `$OMNIA_DATA_PATH/orchestrator` when
  no component-specific path is configured.

- Ensure the OIM can reach the package and container sources required by the
  selected configurations.
- Run the command with privileges to manage Podman containers, systemd
  services, firewall settings, certificates, and files under the configured
  Omnia data paths.
- Have the credential values required by the selected Repo Manager, S3,
  aarch64, OpenLDAP, and Orchestrator configurations available. The command
  collects only the values applicable to the current configuration.

For a manual image-build workflow that does not use BuildStreaM, Orchestrator
can be skipped until its inputs are ready.

## Procedure

1. Change to the Main source directory:

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ```

2. Optional: Preview the domains and phase-specific tags without running
   Ansible:

    ```bash title="Run on: OIM host"
    ./omnia.sh --prepare-base --dry-run
    ```

3. Prepare all three base domains:

    ```bash title="Run on: OIM host"
    ./omnia.sh --prepare-base
    ```

    Provide requested credentials at the prompts. The command completes each
    phase across the selected domains before starting the next phase. If any
    domain fails, processing stops immediately.

4. For a manual image-build workflow that does not use BuildStreaM, prepare
   only the services required before building images by skipping Orchestrator:

    ```bash title="Run on: OIM host"
    ./omnia.sh --prepare-base --skip orchestrator
    ```

    `--skip` accepts a comma-separated list containing only `repo_manager`,
    `image_build_manager`, and `orchestrator`. For a new image-building
    environment, include Repo Manager because Image Build Manager requires its
    synchronized output during the build phase. Skip Repo Manager only when
    its Pulp service and a successful `repo_status.yml` are already available.

    !!! note

        For the BuildStreaM workflow, do not skip any domain. Run
        `./omnia.sh --prepare-base` without `--skip` so Repo Manager, Image
        Build Manager, and Orchestrator are all prepared.

## Verification

A successful run ends with a preparation summary reporting zero failed
domains. The preparation playbooks also verify the services that they deploy.

For the default local-service configuration, confirm the following services
are active:

```bash title="Run on: OIM host"
systemctl is-active pulp.service
systemctl is-active registry.service
systemctl is-active openchami.target
```

When MinIO is selected as the S3 provider, also run:

```bash title="Run on: OIM host"
systemctl is-active minio.service
```

When the catalog enables OpenLDAP, also run:

```bash title="Run on: OIM host"
systemctl is-active omnia_auth.service
```

Services for a skipped domain are not expected to be prepared by this command.

## Next steps

!!! note

    Skip the commands in this section for the BuildStreaM workflow. The
    BuildStreaM build and deployment pipelines perform the corresponding
    repository, image-build, and cluster-deployment operations.

For a manual workflow, after configuring the catalog, repository sources, and
required Orchestrator inputs, continue with these domain operations:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run repo_manager --tags execute
    ./omnia.sh --run image_build_manager --tags execute
    ./omnia.sh --run orchestrator --tags execute
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
    ansible-playbook repo_manager.yml --tags execute

    cd <OMNIA_SOURCE_PATH>/src/image_build_manager/playbooks
    ansible-playbook image_build_manager.yml --tags execute

    cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
    ansible-playbook orchestrator.yml --tags execute
    ```

Repo Manager synchronizes the configured content and writes
`repo_status.yml`. Image Build Manager consumes that file, builds the images,
and writes `build_status.yml`. Orchestrator consumes the generated outputs,
provisions the cluster nodes, and performs PXE boot when it is enabled.

For the complete procedures:

1. [Configure and synchronize repositories](../repo_manager/configure_repos.md)
   so Repo Manager generates a successful `repo_status.yml`.
2. [Build OS images](../image_build_manager/build_images.md). Image Build
   Manager consumes `repo_status.yml`, uploads the image artifacts, and
   generates `build_status.yml`.
3. Continue with [Orchestrator](../orchestrator/index.md) after the required
   functional-group images and Orchestrator inputs are ready.

## Troubleshooting

- **The virtual environment is not found**: Run `./omnia.sh --setup-venv`
  before preparing the base domains. The command expects the activation file
  at `$OMNIA_VENV_PATH/bin/activate`.
- **A domain fails during validation**: Correct that domain's staged input or
  environment values. The failure output identifies the domain and phase.
- **A credential phase fails**: Verify the required values and access to the
  domain credential and Vault-key files, then rerun the command.
- **A service fails during preparation**: Review the applicable log:
  `/var/log/omnia/repo_manager/repo_manager.log`,
  `/var/log/omnia/image_build_manager/image_build_manager.log`, or
  `/var/log/omnia/orchestrator/orchestrator.log`. Also inspect the failed
  systemd service and its Podman container logs.
- **An invalid domain is supplied to `--skip`**: Use only `repo_manager`,
  `image_build_manager`, or `orchestrator`.
- **Preparation stops after a failure**: Correct the reported problem and
  rerun `./omnia.sh --prepare-base`. The command starts again with validation
  and safely rechecks already prepared services.

For container, certificate, and connectivity failures, see
[Base infrastructure preparation failures](../../Troubleshooting/general.md#base-infrastructure-preparation-failures).
