# Clean Up Orchestrator

## Overview

Orchestrator provides a full cleanup workflow and a standalone
component-cleanup playbook. Full cleanup removes every enabled Orchestrator
component, including the encrypted credential file and Vault key by default.

Component cleanup can remove OpenCHAMI, OpenLDAP, Slurm, Kubernetes, storage
mounts, or generated Orchestrator artifacts independently. Slurm and
Kubernetes cleanup unmounts the corresponding storage and removes its
`/etc/fstab` entries.

!!! danger

    Cleanup is destructive. Slurm and Kubernetes cleanup unmounts shared
    NFS storage and removes `/etc/fstab` entries. To delete shared data,
    you must manually stop services and remove data from the NFS share
    before running cleanup. Back up required data and review the selected
    components before confirming the operation. OpenCHAMI cleanup also
    permanently deletes the `boot-service-data`, `metadata-service-data`,
    and `postgres-data` Podman volumes.

!!! warning "Credential retention"

    Full cleanup removes the Orchestrator credential file and Vault key by
    default. To retain them, add `-e cleanup_credentials=false` to the full
    cleanup command. The standalone component-cleanup playbook removes
    credentials only when its selected scope includes `cleanup_credentials`.

## Prerequisites

- Run cleanup from the OIM with the same `OMNIA_DATA_PATH` and
  `OMNIA_PROJECT_NAME` values used for deployment. Orchestrator uses
  `<OMNIA_DATA_PATH>/orchestrator` as its data root.
- Stop cluster workloads that use the selected services or shared storage.
- Back up configuration, application, project, scratch, and other required
  data stored in directories managed through the selected mounts.
- Run `omnia.sh` commands from `src/main` and direct domain commands from
  `src/orchestrator`. Run the standalone component playbook only from
  `src/orchestrator`.

## Procedure

### Preview full cleanup

Set `DRY_RUN=true` to display the cleanup plan and execute the component tasks
in Ansible check mode:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    DRY_RUN=true ./omnia.sh --run orchestrator --tags cleanup
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
    DRY_RUN=true ansible-playbook orchestrator.yml --tags cleanup
    ```

Review the displayed component order and every shared-storage path before
continuing.

### Clean all enabled components

Run the full cleanup workflow:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags cleanup
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
    ansible-playbook orchestrator.yml --tags cleanup
    ```

Full cleanup unmounts Slurm and Kubernetes storage and removes their
`/etc/fstab` entries. To delete shared data from NFS shares, you must
manually stop the services and remove the data before running cleanup.
See [Shared (NFS) data cleanup](#shared-nfs-data-cleanup) for detailed
manual cleanup steps.

Full cleanup also removes
`orchestrator_credentials.yml` and `.orchestrator_credentials_key` by default.
To preserve both files while cleaning the other enabled components, run:

```bash title="Run on: OIM"
./omnia.sh --run orchestrator --tags cleanup \
  -e cleanup_credentials=false
```

The value must be `true` or `false`. An invalid value stops cleanup before
component removal begins. An explicit `cleanup_credentials` tag still removes
the credential files and takes precedence over this full-cleanup opt-out.

### Clean credentials

Remove only the Orchestrator credential file and Vault key:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags cleanup_credentials
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
    ansible-playbook orchestrator.yml --tags cleanup_credentials
    ```

Remove all enabled components and credentials in one supported operation:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags cleanup,cleanup_credentials
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
    ansible-playbook orchestrator.yml --tags cleanup,cleanup_credentials
    ```

### Clean selected components

Component tags are intentionally rejected by the top-level Orchestrator
playbook. Run the standalone cleanup playbook directly from
`src/orchestrator`:

```bash title="Run on: OIM"
cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks/cleanup
ansible-playbook cleanup_orchestrator.yml --tags <component>
```

Supported component tags are:

| Tag | Scope |
|---|---|
| `openchami` | OpenCHAMI services, containers, configuration, artifacts, the `openchami` and `ochami` RPMs, and the persistent `boot-service-data`, `metadata-service-data`, and `postgres-data` Podman volumes. |
| `openldap` | OpenLDAP container, Quadlet configuration, and data. |
| `slurm` | Slurm configuration and managed shared-storage directories. It unmounts storage and removes fstab entries. |
| `k8s` | Kubernetes configuration and managed shared-storage directories. It unmounts storage and removes fstab entries. |
| `storage_mounts` | Configured NFS unmount and `/etc/fstab` cleanup. |
| `artifacts` | Generated Orchestrator artifacts and state files. |
| `cleanup_credentials` | Encrypted credential file and Vault key. |

Use `DRY_RUN=true` or `SKIP_APPROVAL=true` with the standalone command when
the same preview or explicitly approved non-interactive behavior is required.
Running the standalone playbook without tags selects all enabled components
and removes Orchestrator credentials. To preserve them, select each required
component explicitly and omit `cleanup_credentials`; do not run the standalone
playbook without tags.

### Shared (NFS) data cleanup

When selected, Slurm cleanup removes data from the **shared filesystem**,
not just the local mount point, so the data is deleted on the NFS server. This is
done by writing through the mount point while the share is still mounted, which
means no SSH access to the NFS server is required and it works with NFS appliances.
Slurm cleanup removes its configured data directories while retaining
`preserve_directories`.

**Slurm and Kubernetes NFS share cleanup are disabled by default** and must be performed manually.
When the Slurm daemons or Kubernetes cluster are running, files in the NFS share are locked by active
processes, pods, or containers, causing automated cleanup to fail. To clean up Slurm or Kubernetes NFS
data manually:

**For Slurm:**
1. Stop the Slurm daemons (slurmctld, slurmd) and ensure all jobs are terminated
2. Manually delete the data from the NFS share path configured in `storage_config.yml`
3. Run the orchestrator cleanup playbook with `cleanup_slurm=true` to unmount the share
   and remove fstab entries

**For Kubernetes:**
1. Stop the Kubernetes cluster (or ensure all pods are terminated)
2. Manually delete the data from the NFS share path configured in `storage_config.yml`
3. Run the orchestrator cleanup playbook with `cleanup_k8s=true` to unmount the share
   and remove fstab entries

Order of operations per component (Slurm):

1. Remove the component's directories via the mount point (deletes them on the server)
2. Unmount the share and remove its `/etc/fstab` entry
3. Remove the now-empty local mount point directories

If the share is **not mounted** and the same path is not a local NFS export,
cleanup fails instead of claiming that requested server-side data was removed.
Mount or export the share and re-run the cleanup.

To keep shared data, set `cleanup_nfs_server: false` in the relevant component spec:

- `roles/cleanup/components/slurm/vars/component_spec.yml`
- `roles/cleanup/components/k8s/vars/component_spec.yml`

Directories listed under `preserve_directories` (Slurm: `slurm_backups`) are never
removed.

**Warning:** this is destructive and irreversible. On shared storage these paths
(`projects`, `scratch`, `apps`, …) may hold data Omnia did not create. Verify backups
before running, and do a `DRY_RUN=true` pass first.

## Verification

- Confirm that the play recap contains no failed tasks and that the completion
  message lists the intended number of components.
- For a component cleanup, verify only the selected service, configuration,
  mounts, and artifacts were removed.
- When OpenCHAMI cleanup was selected, confirm its three managed persistent
  Podman volumes and the `openchami` and `ochami` RPMs are absent, and confirm
  the data-volume systemd units are inactive.
- When credentials were intentionally omitted from component cleanup, confirm
  both credential files remain in the project input directory.
- When full cleanup used `cleanup_credentials=false`, confirm both credential
  files remain in the project input directory.
- When `cleanup_credentials` was selected, confirm both credential files were
  removed.

## Next steps

- Run `./omnia.sh --setup-venv` again only when project inputs need to be
  restaged.
- Follow [Deploy OpenCHAMI](deploy_openchami.md) or
  [Provision Nodes](provision_nodes.md) to redeploy the required components.

## Troubleshooting

- **Explicit component cleanup aborts:** Run it interactively and type exactly
  `yes`, or set `SKIP_APPROVAL=true` only after reviewing the destructive
  scope.
- **Shared-data cleanup fails:** Confirm the expected share is mounted on the
  OIM or is a local NFS export. When deletion was selected, cleanup fails if
  the server-side data is inaccessible.
- **A component tag is rejected:** Run component tags against
  `playbooks/cleanup/cleanup_orchestrator.yml`, not the top-level
  `playbooks/orchestrator.yml`.
- **A mount remains active:** Stop processes using the mount, verify the
  relevant `storage_config.yml` entry, and rerun the `storage_mounts`
  component cleanup.
