# Log Management

Omnia writes Ansible execution logs on the OIM and uses the native logging
mechanisms of Podman, systemd, Kubernetes, and Slurm for deployed services.
Review logs before restarting services or re-provisioning nodes so that the
original failure evidence is preserved.

!!! warning

    Do not remove logs or their directories until the required diagnostic and
    audit data has been retained.

## Log locations

### Playbook logs on the OIM

| Log file | Domain |
| --- | --- |
| `/var/log/omnia/discovery/discovery.log` | Discovery |
| `/var/log/omnia/repo_manager/repo_manager.log` | Repository Manager |
| `/var/log/omnia/image_build_manager/image_build_manager.log` | Image Build Manager |
| `/var/log/omnia/orchestrator/orchestrator.log` | Orchestrator |
| `/var/log/omnia/telemetry/telemetry.log` | Telemetry |
| `/var/log/omnia/build_stream/build_stream.log` | BuildStreaM |
| `/var/log/omnia/utils/utils.log` | Utils |

When a standalone phase playbook is invoked directly, its local `ansible.cfg`
writes a phase-specific file under the domain log directory. For example,
Orchestrator phase playbooks write `precheck.log`, `provision.log`, or
`pxeboot.log` under `/var/log/omnia/orchestrator/`. Other domains follow the
same pattern (e.g., `validate.log`, `deploy.log`, `cleanup.log`) in their
respective `/var/log/omnia/<domain>/` directories. Runs through the main
domain entry point use the domain-level log shown in the table above.

Orchestrator input validation also writes a separate project-specific detail
log at
`<OMNIA_DATA_PATH>/log/core/playbooks/orchestrator_validation_<OMNIA_PROJECT_NAME>.log`.
This file is distinct from the Ansible execution log and is replaced on each
validation run.

### Domain data and service logs

| Location | Purpose |
| --- | --- |
| `<ORCHESTRATOR_DATA_PATH>/log/openchami/` | Reserved OpenCHAMI log directory created by Orchestrator |
| `<OMNIA_DATA_PATH>/openchami/workdir/` | Generated OpenCHAMI configuration and node artifacts |
| `<OMNIA_DATA_PATH>/repo_manager/log/` | Repository processing and Pulp logs |
| `<IMAGE_BUILD_MANAGER_DATA_PATH>/log/<OMNIA_PROJECT_NAME>/` | Image-build logs |
| `<OMNIA_DATA_PATH>/build_stream_root/artifacts/<job_id>/` | BuildStreaM job artifacts and results |

`ORCHESTRATOR_DATA_PATH` defaults to `$OMNIA_DATA_PATH/orchestrator`, and
`IMAGE_BUILD_MANAGER_DATA_PATH` defaults to
`$OMNIA_DATA_PATH/image_build_manager`. OpenCHAMI runtime diagnostics are
emitted primarily to the systemd journal and Podman container logs; the
reserved OpenCHAMI log directory is not a replacement for those sources.

### Slurm logs on cluster nodes

| Path | Description |
| --- | --- |
| `/var/log/slurm/slurmctld.log` | Controller daemon log |
| `/var/log/slurm/slurmd.log` | Compute daemon log |
| `/var/log/slurm/slurmdbd.log` | Accounting database daemon log |

These are the default paths. If `SlurmctldLogFile`, `SlurmdLogFile`, or
`LogFile` are overridden in the Slurm configuration, the actual log paths
will differ.

## OpenCHAMI and Podman logs on the OIM

The current OpenCHAMI stack uses Fabrica services installed beneath
`openchami.target`, including services such as SMD, boot-service,
metadata-service, tokensmith, PostgreSQL, HAProxy, step-ca, ACME certificate
units, and CoreSMD DNS/DHCP services. The exact units, containers, and image
versions depend on the installed OpenCHAMI release.

1. Obtain the authoritative unit and container lists:

    ```bash title="Run on: OIM host"
    systemctl list-dependencies openchami.target --plain
    podman ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
    ```

2. View logs from a container:

    ```bash title="Run on: OIM host"
    podman logs --tail 200 <container_name>
    ```

3. For a systemd-managed container, use the corresponding unit reported by
   `systemctl list-dependencies`:

    ```bash title="Run on: OIM host"
    systemctl status <service_name>.service --no-pager
    journalctl -u <service_name>.service -b --no-pager
    ```

For the OIM-hosted OpenLDAP service, inspect `omnia_auth.service` and the
`omnia_auth` container.

## Kubernetes pod logs

```bash title="Run on: Kubernetes control plane"
kubectl get pods -A -o wide
kubectl get pod <pod_name> -n <namespace> \
  -o jsonpath='{.spec.containers[*].name}'
kubectl logs <pod_name> -n <namespace> -c <container_name>
```

Add `--previous` to the final command when a container has restarted and the
failure occurred in its previous instance.

## Retention and rotation

Orchestrator does not install a logrotate rule or change the system-wide
journald retention policy for OpenCHAMI or `omnia_auth`. Retention for their
systemd and Podman logs therefore follows the OIM operating-system policy.
Inspect the effective journal usage and settings with:

```bash title="Run on: OIM host"
journalctl --disk-usage
systemd-analyze cat-config systemd/journald.conf
```

The Ansible execution files under `/var/log/omnia/` are regular files that
grow with each playbook run. Omnia does not define a domain-specific rotation
rule for them. The project-specific input-validation log is recreated for
each validation run. Monitor disk usage under `/var/log/omnia/` and consider
site-specific rotation or archival policies, especially for frequently
executed domains. If the site adds a rotation policy for the Ansible logs,
retain the data required by site policy and verify that the account running
the playbook can continue writing after rotation.

## Cluster log collection

Use the Utils `collect` workflow to gather the source-defined Kubernetes and
Slurm log paths and create a timestamped archive with `metadata.json`. See
[Collect Cluster Logs](collect_cluster_logs.md) for its input, output,
verification, and cleanup procedure.

## OIM log backup

Use the Utils `backup_oim_logs` workflow, where available, to archive selected
domain log directories. When `ORCHESTRATOR_DATA_PATH` points outside the
default `$OMNIA_DATA_PATH/orchestrator` location, include that custom path in
the site's backup procedure; a tool that scans only `$OMNIA_DATA_PATH` will not
discover it automatically.

See [Back Up OIM Logs](../HowTo/utils/backup_oim_logs.md) for the supported
configuration and execution procedure.

!!! info

    - [General Troubleshooting](../Troubleshooting/general.md) -- Uses logs as
      a primary diagnostic source.
    - [Best Practices Checklist](best_practices_checklist.md) -- Storage and
      maintenance practices.
