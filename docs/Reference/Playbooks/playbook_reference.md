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
    source "${OMNIA_DATA_PATH:-/opt/omnia}/activate-omnia.sh"
    cd <OMNIA_SOURCE_PATH>/src/<domain>/playbooks
    ansible-playbook <domain>.yml --tags <tag>
    ```

For direct Utils execution, set `ANSIBLE_CONFIG=../ansible.cfg` after changing
to `src/utils/playbooks`; the Utils configuration remains at the domain root.

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
| Repository Manager | `src/repo_manager/playbooks/repo_manager.yml` | `precheck`, `credentials`, `prepare`, `deploy`, `execute`, `download`, `status`, `cleanup`, `cleanup_pulp`, `cleanup_repos`, `catalog_generate`, `catalog_add`, `catalog_delete`, `catalog_validate` | [How-to guide](../../HowTo/repo_manager/index.md) · [Contract](../domain_contracts/repo_manager_contract.md) |
| Telemetry | `src/telemetry/playbooks/telemetry.yml` | `precheck`, `validate`, `validation`, `prepare`, `credentials`, `execute`, `deploy`, `cleanup`, `cleanup_idrac`, `cleanup_ldms`, `cleanup_ome`, `cleanup_powerscale`, `cleanup_ufm`, `cleanup_vast`, `external_kafka`, `external_victoria` | [How-to guide](../../HowTo/Telemetry/index.md) · [Contract](../domain_contracts/telemetry_contract.md) |
| Utils | `src/utils/playbooks/utils.yml` | `precheck`, `setup`, `collect`, `install_os`, `backup_oim_logs`, `slurm_config_backup`, `slurm_config_cleanup`, `slurm_config_rollback`, `cleanup`, `cleanup_logs`, `cleanup_install_os`, `cleanup_backup_oim_logs`, `cleanup_slurm_config_backups` | [How-to guide](../../HowTo/utils/index.md) · [Contract](../domain_contracts/utils_contract.md) |

The following accepted lifecycle tags are placeholders and do not perform the
named operation:

- Discovery: `prepare`, `upgrade`, and `rollback`.
- BuildStreaM: `upgrade` and `rollback`.
- Image Build Manager: `upgrade` and `rollback`.
- Repository Manager: `upgrade` and `rollback`.
- Telemetry: `upgrade` and `rollback`.
- Utils: `upgrade` and `rollback`.

Orchestrator's `rollback` operation is reserved and intentionally fails because
rollback is unsupported. Do not use a placeholder operation as a deployment
step.

Utils is an on-demand utility module and does not define the standard domain
lifecycle operations `credentials`, `prepare`, or `execute`. Validation is
selected by the requested utility operation instead of through a standalone
customer `validate` operation. A no-tag run performs common domain setup and
writes `utils_status.yml`. The explicit `setup` tag also selects setup stages
imported by log collection and OIM log backup. These stages can prepare backup
paths, inventories, and workspaces, but do not collect or archive logs.

Telemetry provides granular cleanup for the source components listed in the
table. Shared Kafka, VictoriaMetrics, and VictoriaLogs sinks are removed only
by the complete `cleanup` operation, together with the sources. The parsed
`cleanup_kafka`, `cleanup_victoria_metrics`, and `cleanup_victoria_logs` tags do
not independently remove their corresponding sinks and are not customer
operations.

## Dependency order

For direct module execution, use the output contracts to establish the order:

```text
Repository Manager
    ├── repo_status.yml ──> Image Build Manager
    │                         └── build_status.yml ───────────────┐
    └── repo_status.yml ─────────────────────────────────────────┤
Discovery (optional)                                             │
    └── review and install mapping as pxe_mapping_file.csv ──────┤
                                                                  ▼
                                                            Orchestrator
                                                                  │
                                             Kubernetes cluster, when selected
                                                                  ▼
                                                       Telemetry (optional)

Utils: run on demand
```

Discovery is independent of Image Build Manager. It writes
`bmc_pxe_mapping_file.csv`; review that file and install it in the Orchestrator
project input directory as `pxe_mapping_file.csv`. This handoff is not
automatic.

BuildStreaM provides a separate catalog-driven automation path. Before its
first deployment, prepare the base services and credentials from `src/main`:

```bash title="Run on: OIM host"
./omnia.sh --prepare-base
```

The opt-in BuildStreaM `precheck` verifies that the `pulp`, `minio-server`, and
`registry` containers are running and that the Repository Manager and Image
Build Manager credential artifacts exist. It does not generate or validate
`repo_status.yml` or `build_status.yml`, and the `build` operation does not
automatically select `precheck`.

The BuildStreaM build pipeline invokes Repository Manager and Image Build
Manager, and its deploy pipeline invokes Orchestrator. Telemetry is initialized
separately after a Kubernetes cluster is available.

For the first BuildStreaM deployment, review the Discovery mapping and install
it in the Orchestrator project input directory as described above. The first
GitLab input synchronization reads the Orchestrator input from:

```text
$OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/pxe_mapping_file.csv
```

Stage the reviewed mapping at this location before the first synchronization,
or commit it after GitLab is available. Once the managed GitLab project
exists, update and commit `input/orchestrator/pxe_mapping_file.csv`, verify
that the required functional-group images are available, and start the
applicable deploy job. Rerunning BuildStreaM setup can create or update managed
input files from their `OMNIA_DATA_PATH` locations.

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
| Prepare base services required by BuildStreaM | `./omnia.sh --prepare-base` |
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
`prepare,precheck,download,status`. Discovery and Orchestrator support their
documented `cleanup,cleanup_credentials` combination. Telemetry supports
combinations of its granular source cleanup operations: `cleanup_idrac`,
`cleanup_ldms`, `cleanup_ome`, `cleanup_powerscale`, `cleanup_ufm`, and
`cleanup_vast`. Shared sinks are removed only by `cleanup`. BuildStreaM,
Discovery, Image Build Manager, and Orchestrator reject unsupported or
conflicting tags. For every other invocation, follow the selected module's tag
rules and prefer one operation tag at a time.

## Outputs and verification

By default, each module reads project input from and writes project output to:

```text
<OMNIA_DATA_PATH>/<domain>/input/<OMNIA_PROJECT_NAME>/
<OMNIA_DATA_PATH>/<domain>/output/<OMNIA_PROJECT_NAME>/
```

Each domain uses its own directory beneath `OMNIA_DATA_PATH`:

- `$OMNIA_DATA_PATH/repo_manager`
- `$OMNIA_DATA_PATH/image_build_manager`
- `$OMNIA_DATA_PATH/discovery`
- `$OMNIA_DATA_PATH/orchestrator`
- `$OMNIA_DATA_PATH/telemetry`
- `$OMNIA_DATA_PATH/build_stream`
- `$OMNIA_DATA_PATH/utils`

Changing `OMNIA_DATA_PATH` changes the common data root for every domain. See
[Main environment configuration](../Configuration/omnia_env.md) for the
available settings.

### Cross-domain output contracts

Repository Manager and Image Build Manager status files are consumed in place
from their producer output directories, or from paths explicitly configured by
the consumer. Do not copy them into a downstream input directory unless a
module-specific procedure explicitly requires it.

Before invoking a dependent flow:

- Verify that `repo_status.yml` reports `overall_status: success`, contains the
  required repository and Pulp certificate information, and references an
  existing certificate. Do this before building images and before an
  Orchestrator flow that consumes repositories or the Pulp certificate.
- Verify that `build_status.yml` reports `overall_status: success` before
  Orchestrator `precheck`, `provision`, `execute`, `pxeboot`, or a full no-tag
  run. These contracts also apply to BuildStreaM pipelines: the build pipeline
  produces `repo_status.yml` before Image Build Manager produces
  `build_status.yml`, and the deploy pipeline invokes Orchestrator against both
  successful contracts.
- When Discovery supplies the mapping, review its `bmc_pxe_mapping_file.csv`
  and install it in the Orchestrator project input directory as
  `pxe_mapping_file.csv` before every Orchestrator flow that validates inputs:
  `precheck`, `validate`, `prepare`, `deploy`, `provision`, `execute`,
  `validate-deployment`, or `pxeboot`.
- Before running Telemetry, set `cluster_inventory` to the generated
  `$OMNIA_DATA_PATH/orchestrator/output/<OMNIA_PROJECT_NAME>/orchestrator_inventory.yml`.
- When iDRAC telemetry is enabled, set
  `idrac_telemetry_configurations.bmc_group_data_path` to the generated
  `$OMNIA_DATA_PATH/orchestrator/output/<OMNIA_PROJECT_NAME>/bmc_group_data.csv`, or
  copy that file into the Telemetry project input directory to use the
  empty-path default.

Cleanup operations can remove services, images, repositories, stored
credentials, runtime data, logs, or generated artifacts. Review the
module-specific cleanup guide, including any credential-preservation option
and required extra variables, before running them.

## Related documentation

- [Running deployment modules](../../Overview/domain_execution.md)
- [Module contracts](../index.md#module-contracts)
- [Main environment configuration](../Configuration/omnia_env.md)
