# Upgrade Orchestrator

## Overview

The Orchestrator `upgrade` workflow runs the OpenCHAMI and OpenLDAP component
upgrade playbooks in sequence. The current OpenCHAMI workflow targets the
migration from `0.1.7-1` to `0.2.0-1`. It records the installed package
version, creates a pre-upgrade backup, removes legacy pre-Fabrica services when
present, pulls the configured OpenCHAMI images, restarts the services, and
checks their health.

When the `omnia_auth` container is deployed, the OpenLDAP workflow pulls
`docker.io/dellhpcomniaaisolution/omnia_auth:1.2`, restarts the service, and
checks that the container is running. It also attempts an LDAP endpoint query,
but that query is non-fatal. It skips OpenLDAP when the container is not
deployed.

!!! important "Current upgrade limitations"

    The OpenCHAMI workflow does not install the target `openchami-0.2.0-1`
    RPM and does not verify the installed RPM version again after restarting
    services. A successful health check therefore confirms service health, not
    completion of the package-version transition.

    The OpenLDAP workflow pulls `omnia_auth:1.2`, but it does not rewrite the
    existing `/etc/containers/systemd/omnia_auth.container` Quadlet. Restarting
    the service continues to use the image in that file. If its `Image=` entry
    still names an older tag, pulling `1.2` alone does not switch the running
    container. The automated LDAP query also does not fail the play when the
    endpoint is unavailable. Use an approved package/Quadlet migration
    procedure and perform every version and service check in this guide before
    declaring either component upgraded.

!!! warning

    OpenCHAMI and OpenLDAP rollback are not supported in this release. The
    `rollback` tag enters reserved workflows that intentionally stop with a
    `ROLLBACK NOT SUPPORTED` error. The OpenCHAMI pre-upgrade backup does not
    make the rollback workflow operational.

## Prerequisites

- Run the workflow from the OIM with the project environment used for the
  existing Orchestrator deployment.
- Provide a successful Repository Manager `repo_status.yml` and its referenced
  Pulp certificate. The top-level Orchestrator setup validates this contract
  before the `upgrade` workflow starts.
- Confirm OpenCHAMI is healthy and preserve an external backup of required
  service and project data.
- Confirm the installed OpenCHAMI source version with `rpm -q openchami`, and
  define an approved migration sequence that installs the target `0.2.0-1`
  RPM. The playbook does not install that RPM on your behalf.
- Ensure the OIM can pull the OpenCHAMI and `omnia_auth:1.2` container images.
- Inspect `/etc/containers/systemd/omnia_auth.container` when OpenLDAP is
  deployed. Arrange an approved update of its `Image=` entry to
  `docker.io/dellhpcomniaaisolution/omnia_auth:1.2`; the playbook only pulls
  the image and restarts the existing unit.
- Preserve the Orchestrator credential file and Vault key.
- Plan a maintenance window because the workflow stops legacy services and
  restarts OpenCHAMI and OpenLDAP.

## Procedure

1. Initialize the shared environment if it is not already available:

    ```bash title="Run on: OIM"
    cd src/main
    ./omnia.sh --setup-venv
    ```

2. Run this command only at the point prescribed by the approved migration
   sequence. The component workflows perform their backup, legacy cleanup,
   image pull, restart, and health checks; the surrounding procedure must also
   install the target OpenCHAMI RPM and retarget the OpenLDAP Quadlet:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags upgrade
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator
        ansible-playbook playbooks/orchestrator.yml --tags upgrade
        ```

   OpenCHAMI writes its pre-upgrade backup below
   `$OMNIA_DATA_PATH/openchami/backups/pre_upgrade_<timestamp>/`. The backup
   contains available OpenCHAMI configuration, SMD records, work-directory
   data, and `backup_metadata.yml`. An
   `$OMNIA_DATA_PATH/.data/upgrade_in_progress.lock` file protects the active
   migration and is removed after successful OpenCHAMI health verification.

3. If node configuration must be refreshed after the component upgrade, rerun
   provisioning:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags provision
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator
        ansible-playbook playbooks/orchestrator.yml --tags provision
        ```

## Verification

Verify the OpenCHAMI package and services. Do not treat the play recap or
service health alone as proof that the target RPM is installed:

```bash title="Run on: OIM"
rpm -q openchami
systemctl is-active openchami.target
/usr/bin/ochami smd service status
systemctl is-active boot-service
```

When OpenLDAP is deployed, confirm its image and service state:

```bash title="Run on: OIM"
podman inspect omnia_auth --format '{{.ImageName}}'
systemctl is-active omnia_auth
podman exec omnia_auth ldapsearch -x -H ldap://localhost -b "" -s base namingContexts
```

The OpenCHAMI package must report `0.2.0-1`. The OpenLDAP image name must be
exactly the approved `omnia_auth:1.2` image, and all listed services must report
an active or running state. If either version check fails, the component
upgrade is incomplete even when the playbook health tasks passed.

## Next steps

- Run [Provision Nodes](provision_nodes.md) when node-side configuration must
  be regenerated.
- Review the project outputs and OpenCHAMI service state before returning the
  cluster to production use.

## Troubleshooting

- **The upgrade lock remains after a failure:** Preserve the backup and logs,
  correct the failed service or image operation, and rerun the idempotent
  upgrade workflow. Do not remove the lock merely to bypass a failed upgrade.
- **OpenLDAP is skipped:** The workflow skips it when the `omnia_auth`
  container is not deployed. Use [Deploy OpenLDAP](deploy_openldap.md) when
  the catalog requires it.
- **OpenCHAMI remains on the source RPM:** The workflow does not install or
  post-validate the target RPM. Complete the approved package migration, rerun
  the verification commands, and do not clear a failed migration merely on the
  basis of healthy services.
- **OpenLDAP still runs the old image:** Check the Quadlet `Image=` entry. The
  workflow pulls `1.2` but does not retarget the fixed image reference in an
  existing unit; update or redeploy the unit through the approved procedure,
  reload systemd, restart it, and verify the running image.
- **A rollback command fails:** This is expected in the current release.
  Restore service state through an approved recovery procedure rather than
  invoking the reserved rollback tag.
- Review `/var/log/omnia/orchestrator/orchestrator.log` and the OpenCHAMI or
  `omnia_auth` service logs for the failing task.
