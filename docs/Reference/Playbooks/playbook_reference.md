# Module Playbook Entry Points

## Overview

Omnia does not use one centralized deployment playbook. Each deployment module exposes a
top-level playbook at `src/<domain>/playbooks/<domain>.yml`. The `src/main/omnia.sh`
script selects one of those playbooks, activates the shared Python environment,
and passes the requested tags and additional Ansible arguments to it.

Use this page to identify the executable entry point and supported customer
operations for each module. For configuration fields and generated artifacts,
use the linked module contract.

## Invocation methods

Choose one execution method for a module operation:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run <domain> --tags <tag>
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/<domain>
    ansible-playbook playbooks/<domain>.yml --tags <tag>
    ```

`--run` accepts one module's internal domain identifier. Unless a module entry
point explicitly supports a combination, run one tag at a time. Omitting
`--tags` follows that module's own default flow; it is not a universal alias
for `execute`.

## Module entry points

| Deployment module | Executable entry point | Implemented customer operations | Module guidance |
| --- | --- | --- | --- |
| BuildStreaM | `src/build_stream/playbooks/build_stream.yml` | `precheck`, `validate`, `credentials`, `prepare`, `execute`, `build`, `cleanup` | [How-to guide](../../HowTo/build_stream/index.md) · [Contract](../domain_contracts/build_stream_contract.md) |
| Discovery | `src/discovery/playbooks/discovery.yml` | `precheck`, `validate`, `credentials`, `execute`, `cleanup`, `cleanup_credentials` | [How-to guide](../../HowTo/discovery/index.md) · [Contract](../domain_contracts/discovery_contract.md) |
| Image Build Manager | `src/image_build_manager/playbooks/image_build_manager.yml` | `precheck`, `validate`, `credentials`, `prepare`, `execute`, `build`, `cleanup`, `cleanup_images` | [How-to guide](../../HowTo/image_build_manager/index.md) · [Contract](../domain_contracts/image_build_manager_contract.md) |
| Orchestrator | `src/orchestrator/playbooks/orchestrator.yml` | `precheck`, `validate`, `credentials`, `prepare`, `deploy`, `provision`, `execute`, `validate-deployment`, `pxeboot`, `cleanup`, `cleanup_credentials`, `upgrade`; `rollback` is reserved and unsupported | [How-to guide](../../HowTo/orchestrator/index.md) · [Contract](../domain_contracts/orchestrator_contract.md) |
| Repository Manager | `src/repo_manager/playbooks/repo_manager.yml` | `precheck`, `credentials`, `prepare`, `deploy`, `execute`, `download`, `status`, `cleanup_pulp`, `cleanup_repos`, and catalog operations | [How-to guide](../../HowTo/repo_manager/index.md) · [Contract](../domain_contracts/repo_manager_contract.md) |
| Telemetry | `src/telemetry/playbooks/telemetry.yml` | `precheck`, `validate`, `validation`, `prepare`, `credentials`, `execute`, `deploy`, `cleanup`, component cleanup tags, `external_kafka`, `external_victoria` | [How-to guide](../../HowTo/Telemetry/index.md) · [Contract](../domain_contracts/telemetry_contract.md) |
| Utils | `src/utils/playbooks/utils.yml` | `precheck`, `collect`, `install_os`, `backup_oim_logs`, `slurm_config_backup`, `slurm_config_cleanup`, `slurm_config_rollback`, `cleanup`, `cleanup_logs`, `cleanup_install_os`, `cleanup_backup_oim_logs`, `cleanup_slurm_config_backups` | [How-to guide](../../HowTo/utils/index.md) · [Contract](../domain_contracts/utils_contract.md) |

Discovery's `prepare`, `upgrade`, and `rollback` lifecycle files currently
contain placeholders. Orchestrator's `rollback` operation is reserved and
intentionally fails because rollback is unsupported. BuildStreaM's upgrade and rollback files,
Image Build Manager's upgrade and rollback files, and Repo Manager's upgrade
and rollback files are also placeholders. Do not use a placeholder operation
as a deployment step.
Utils is an on-demand utility module and does not implement the standard
`validate`, `credentials`, `prepare`, or `execute` tags.

## Dependency order

For direct module execution, use the output contracts to establish the order:

```text
Repository Manager
        │ repo_status.yml
        ▼
Image Build Manager
        │ build_status.yml
        ├───────────────┐
        ▼               │
Discovery (optional)    │
        │ PXE mapping   │
        └───────┬───────┘
                ▼
          Orchestrator
                │ Kubernetes cluster, when selected
                ▼
          Telemetry (optional)

Utils: run on demand
```

BuildStreaM provides a separate catalog-driven automation path. Its build
pipeline invokes Repository Manager and Image Build Manager, and its deploy
pipeline invokes Orchestrator. Telemetry is initialized separately after a
Kubernetes cluster is available.

## Command examples

Run these commands from `src/main` on the OIM host after the environment and the
selected modules have been initialized.

| Task | Command |
| --- | --- |
| Synchronize catalog content | `./omnia.sh --run repo_manager --tags download` |
| Generate Repository Manager status | `./omnia.sh --run repo_manager --tags status` |
| Prepare image services | `./omnia.sh --run image_build_manager --tags prepare` |
| Build images | `./omnia.sh --run image_build_manager --tags build` |
| Discover BMC endpoints through OME | `./omnia.sh --run discovery --tags execute` |
| Deploy Orchestrator services | `./omnia.sh --run orchestrator --tags deploy` |
| Provision the selected node categories | `./omnia.sh --run orchestrator --tags provision` |
| Deploy enabled telemetry sources and sinks | `./omnia.sh --run telemetry --tags deploy` |
| Deploy BuildStreaM infrastructure and GitLab | `./omnia.sh --run build_stream --tags build` |
| Collect logs with Utils | `./omnia.sh --run utils --tags collect` |
| Back up OIM logs with Utils | `./omnia.sh --run utils --tags backup_oim_logs` |
| Back up Slurm configuration | `./omnia.sh --run utils --tags slurm_config_backup` |
| Delete active Slurm configuration | `./omnia.sh --run utils --tags slurm_config_cleanup` |
| Restore Slurm configuration | `./omnia.sh --run utils --tags slurm_config_rollback` |
| Delete stored Slurm configuration backups | `./omnia.sh --run utils --tags cleanup_slurm_config_backups` |

The Repository Manager entry point supports the standard workflow combination
`prepare,precheck,download,status`. The other module entry points validate tag
combinations and generally require one operation tag at a time.

## Outputs and verification

Each module reads project input from and writes project output to its own runtime
directory:

```text
<OMNIA_DATA_PATH>/<domain>/input/<OMNIA_PROJECT_NAME>/
<OMNIA_DATA_PATH>/<domain>/output/<OMNIA_PROJECT_NAME>/
```

Verify the output named in the module contract before invoking a dependent
module. In particular, verify `repo_status.yml` before building images,
`build_status.yml` before provisioning, and the Discovery PXE mapping output
when Discovery supplies the Orchestrator inventory.

Cleanup operations can remove services, images, repositories, or generated
artifacts. Review the module-specific cleanup guide and any required extra
variables before running them.

## Related documentation

- [Running deployment modules](../../Overview/domain_execution.md)
- [Module contracts](../index.md#module-contracts)
- [Main environment configuration](../Configuration/omnia_env.md)
