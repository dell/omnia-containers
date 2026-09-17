# Clean Up Orchestrator

## Overview

Orchestrator provides a full cleanup workflow and a standalone
component-cleanup playbook. Full cleanup removes every enabled Orchestrator
component, including the encrypted credential file and Vault key by default.

Component cleanup can remove OpenCHAMI, OpenLDAP, Slurm, Kubernetes, storage
mounts, or generated Orchestrator artifacts independently. Slurm and
Kubernetes cleanup deletes or preserves the selected shared data first and
then unmounts the corresponding storage and removes its `/etc/fstab` entries.

!!! danger

    Cleanup is destructive. Slurm and Kubernetes cleanup can permanently
    delete data from mounted shared NFS storage. Back up required data and
    review the selected components before confirming the operation.

!!! warning "Credential preservation limitation"

    The current cleanup implementation does not consume the
    `cleanup_credentials=false` extra variable, although source comments still
    mention it. A full cleanup therefore removes the Orchestrator credential
    file and Vault key. To retain them, use the standalone component-cleanup
    playbook with explicit component tags that omit `cleanup_credentials`, or
    preserve both files in an approved secure backup before full cleanup.

## Prerequisites

- Run cleanup from the OIM with the same `OMNIA_PROJECT_NAME` and resolved
  Orchestrator data root used for deployment. Set `ORCHESTRATOR_DATA_PATH` to
  the original custom root; when it is unset, Orchestrator uses
  `<OMNIA_DATA_PATH>/orchestrator`.
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
    cd <OMNIA_SOURCE_PATH>/src/orchestrator
    DRY_RUN=true ansible-playbook playbooks/orchestrator.yml --tags cleanup
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
    cd <OMNIA_SOURCE_PATH>/src/orchestrator
    ansible-playbook playbooks/orchestrator.yml --tags cleanup
    ```

Full cleanup prompts independently before deleting Slurm and Kubernetes shared
data. For each prompt, type exactly `yes` to delete that component's shared
data. Any other response preserves the shared data; cleanup continues and
still unmounts that component's storage.

Use `cleanup_slurm` and `cleanup_k8s` to make these decisions
non-interactively:

| Value | Behavior |
|---|---|
| `true` | Delete the component's shared data without prompting, then unmount its storage. |
| `false` | Preserve the component's shared data without prompting, then unmount its storage. |
| Omitted | Prompt independently for that component. |

For example:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags cleanup \
      -e cleanup_slurm=true -e cleanup_k8s=false
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator
    ansible-playbook playbooks/orchestrator.yml --tags cleanup \
      -e cleanup_slurm=true -e cleanup_k8s=false
    ```

This deletes Slurm shared data, preserves Kubernetes shared data, and unmounts
both storage domains. Full cleanup also removes
`orchestrator_credentials.yml` and `.orchestrator_credentials_key`. The
documented `cleanup_credentials=false` compatibility value is not honored by
the current runtime; use the preservation options in the warning above.

For an approved non-interactive operation, set `SKIP_APPROVAL=true`:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    SKIP_APPROVAL=true ./omnia.sh --run orchestrator --tags cleanup
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator
    SKIP_APPROVAL=true ansible-playbook playbooks/orchestrator.yml --tags cleanup
    ```

When `cleanup_slurm` or `cleanup_k8s` is omitted,
`SKIP_APPROVAL=true` approves deletion of that component's shared data. The
command above also removes Orchestrator credentials because credential cleanup
is enabled by default.

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
    cd <OMNIA_SOURCE_PATH>/src/orchestrator
    ansible-playbook playbooks/orchestrator.yml --tags cleanup_credentials
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
    cd <OMNIA_SOURCE_PATH>/src/orchestrator
    ansible-playbook playbooks/orchestrator.yml --tags cleanup,cleanup_credentials
    ```

### Clean selected components

Component tags are intentionally rejected by the top-level Orchestrator
playbook. Run the standalone cleanup playbook directly from
`src/orchestrator`:

```bash title="Run on: OIM"
cd src/orchestrator
ansible-playbook playbooks/cleanup/cleanup_orchestrator.yml --tags <component>
```

Supported component tags are:

| Tag | Scope |
|---|---|
| `openchami` | OpenCHAMI services, containers, configuration, and artifacts. |
| `openldap` | OpenLDAP container, Quadlet configuration, and data. |
| `slurm` | Slurm configuration and managed shared-storage directories. It deletes or preserves shared data before scoped storage cleanup. |
| `k8s` | Kubernetes configuration and managed shared-storage directories. It deletes or preserves shared data before scoped storage cleanup. |
| `storage_mounts` | Configured NFS unmount and `/etc/fstab` cleanup. |
| `artifacts` | Generated Orchestrator artifacts and state files. |
| `cleanup_credentials` | Encrypted credential file and Vault key. |

Use `DRY_RUN=true` or `SKIP_APPROVAL=true` with the standalone command when
the same preview or explicitly approved non-interactive behavior is required.
Running the standalone playbook without tags selects all enabled components
and removes Orchestrator credentials. To preserve them, select each required
component explicitly and omit `cleanup_credentials`; do not run the standalone
playbook without tags.

## Verification

- Confirm that the play recap contains no failed tasks and that the completion
  message lists the intended number of components.
- For a component cleanup, verify only the selected service, configuration,
  mounts, and artifacts were removed.
- When credentials were intentionally omitted from component cleanup, confirm
  both credential files remain in the project input directory.
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
