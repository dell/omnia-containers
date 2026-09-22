# Main

## Overview

The Main component provides `omnia.env` and `omnia.sh` for preparing the Omnia
Infrastructure Manager (OIM). Use it to configure the shared environment,
create the Python virtual environment, initialize module dependencies and
stage the catalog samples required by downstream workflows.

After Main setup, prepare the base infrastructure. Module execution and
module-specific inputs, credentials, outputs, and verification are documented
in their respective module sections.

## Prerequisites

- Use an Omnia source checkout on the OIM.
- Use Python 3.11 or later. The setup script searches for `python3.12`,
  `python3.11`, and then `python3`.
- Use an account that can write to the configured data and virtual-environment
  paths and to the system paths created during setup.
- Set `SYSTEM_ADMIN_NIC_IPV4` in `src/main/omnia.env` to an IPv4 address
  assigned to an OIM interface.
- Make the package sources required by each module's `requirements.txt` and
  `requirements.yml` files available during dependency installation.

## Choose a task

| Task | Use it to |
|---|---|
| [Configure the environment](configure_environment.md) | Set the required OIM address, shared paths, project, hostname, domain, version, catalog, and optional component path overrides. |
| [Set up the OIM](setup_oim.md) | Install the environment, create the shared virtual environment, initialize modules, and stage catalog samples. |
| [Select or update the catalog](update_catalog.md) | List the bundled catalogs and activate the RHEL version, workload, architecture, and VAST variant required by the deployment. |
| [Use the diagnostics CLI](omnia_cli.md) | Check domain status and inputs, edit staged input, inspect generated output, and review domain logs. |
| [Prepare base infrastructure](prepare_base.md) | Validate inputs, collect credentials, and prepare Repo Manager, Image Build Manager, and Orchestrator services. |
| [Maintain the Main environment](../../Operations/maintain_main_environment.md) | Audit dependency versions or remove the installed environment while preserving or deleting runtime data. |

## Command reference

Run Main commands from `src/main`. Display the command-line help at any time:

```bash title="Run from: <omnia-repository>/src/main"
./omnia.sh --help
```

The command syntax is:

```text
./omnia.sh <command> [options]
```

Before the first setup, configure `src/main/omnia.env`. After setup,
`/etc/omnia/omnia.env` is authoritative and is preserved by subsequent setup
runs.

### Commands

| Command | Purpose |
|---|---|
| `--setup-venv`, `-s` | Create or update the shared Python virtual environment, install module dependencies, run each selected `domain-init.sh`, stage module inputs, and copy catalog files. |
| `--init`, `-i [domain,...]` | Rerun initialization for all domains or a comma-separated domain list without rebuilding the virtual environment. |
| `--prepare-base` | Run validation, credential collection, and preparation for Repo Manager, Image Build Manager, and Orchestrator. |
| `--run`, `-r <domain> [--tags <tags>] [extra Ansible arguments]` | Activate the shared environment and run the selected domain playbook. |
| `--check-deps` | Report conflicting Python or Ansible Galaxy dependency requirements across domains. The command exits with a nonzero status when conflicts are found. |
| `--list-catalogs` | List bundled catalogs with selectors, descriptions, content-derived summaries, and source paths. |
| `--select-catalog [selection]` | Select a bundled catalog interactively or by number or exact selector, then validate and atomically activate it at `CATALOG_FILE_PATH`. |
| `--cleanup` | Remove the virtual environment, installed environment files, command-line tools, Bash completion, activation helper, and dependency cache. Runtime data under `$OMNIA_DATA_PATH` is preserved. |
| `--cleanup --all` | Perform a guarded full reset. The command refuses to remove anything until deployed, generated, or otherwise uncleared domain state has been cleaned. After the safety check, it requests confirmation and removes the installed resources and remaining runtime data under `$OMNIA_DATA_PATH`. |
| `--help`, `-h` | Display the current command help. |

!!! warning

    `./omnia.sh --cleanup --all` removes all remaining Omnia data under
    `$OMNIA_DATA_PATH` only after its safety preflight succeeds. If the command
    reports uncleared domain state, run the applicable domain cleanup and retry.
    Review the configured path and retain required data before confirming the
    operation.

### Options

| Option | Valid with | Behavior |
|---|---|---|
| `--deps-only` | `--setup-venv`, `--init` | Install dependencies without staging input files. It cannot be used as a standalone option. |
| `--force-deps` | `--setup-venv`, `--init` | Bypass the dependency cache and reinstall Python packages and Ansible Galaxy collections. |
| `--force-env` | `--setup-venv` | Replace `/etc/omnia/omnia.env` with the repository copy. Use this only when intentionally replacing the installed configuration. |
| `--skip <domain,...>` | `--setup-venv`, `--init`, `--prepare-base` | Skip a comma-separated list of domains. With `--prepare-base`, only `repo_manager`, `image_build_manager`, and `orchestrator` are valid. Do not combine it with an explicit `--init` domain list. |
| `--dry-run` | `--setup-venv`, `--init`, `--prepare-base` | Preview domain initialization or base-domain phases. With `--setup-venv`, other setup operations still run. |
| `--skip-catalog` | `--setup-venv` | Do not copy the source catalog files during setup. |
| `--skip-omnia-cli` | `--setup-venv` | Do not install `omnia-cli` or shared Bash completion. |
| `--skip-approval` | `--cleanup` | Skip the confirmation prompt for trusted unattended automation. The `--cleanup --all` safety preflight still runs. |

### Supported domains and tags

`--run` accepts one of these domain identifiers. Use `--tags` to select a
domain operation.

| Domain | Public tags |
|---|---|
| `build_stream` | `precheck`, `validate`, `credentials`, `prepare`, `execute`, `build`, `cleanup`, `upgrade`, `rollback` |
| `discovery` | `precheck`, `validate`, `credentials`, `prepare`, `execute`, `cleanup`, `cleanup_credentials`, `upgrade`, `rollback` |
| `image_build_manager` | `precheck`, `validate`, `credentials`, `prepare`, `execute`, `build`, `cleanup`, `cleanup_images`, `upgrade`, `rollback` |
| `orchestrator` | `precheck`, `validate`, `credentials`, `prepare`, `deploy`, `provision`, `execute`, `validate-deployment`, `pxeboot`, `cleanup`, `cleanup_credentials`, `upgrade`, `rollback` |
| `repo_manager` | `precheck`, `credentials`, `prepare`, `deploy`, `execute`, `download`, `status`, `cleanup`, `cleanup_pulp`, `cleanup_repos`, `upgrade`, `rollback`, `catalog_generate`, `catalog_add`, `catalog_delete`, `catalog_validate` |
| `telemetry` | `precheck`, `validate`, `validation`, `prepare`, `credentials`, `execute`, `deploy`, `cleanup`, `cleanup_kafka`, `cleanup_victoria_metrics`, `cleanup_victoria_logs`, `cleanup_idrac`, `cleanup_ldms`, `cleanup_ome`, `cleanup_powerscale`, `cleanup_ufm`, `cleanup_vast`, `upgrade`, `rollback`, `external_kafka`, `external_victoria` |
| `utils` | `precheck`, `setup`, `collect`, `install_os`, `backup_oim_logs`, `slurm_config_backup`, `slurm_config_cleanup`, `slurm_config_rollback`, `cleanup`, `cleanup_logs`, `cleanup_install_os`, `cleanup_backup_oim_logs`, `cleanup_slurm_config_backups`, `upgrade`, `rollback` |

Running a domain without `--tags` starts that domain's default flow. Defaults
are domain-specific. Tags marked `never` in a domain playbook run only when
explicitly selected, and invalid tags or combinations fail validation. Review
the relevant domain guide before running cleanup, upgrade, or rollback tags.

### Recommended execution order

Run deployment domains in the following order because later domains consume
outputs from earlier domains:

| Step | Domain | Handoff |
|---:|---|---|
| 1 | `repo_manager` | Synchronizes software content and writes `repo_status.yml`. |
| 2 | `image_build_manager` | Reads `repo_status.yml`, builds OS images, and writes `build_status.yml`. |
| 3 | `discovery` (optional) | Discovers servers and writes `bmc_pxe_mapping_file.csv`. |
| 4 | `orchestrator` | Reads the repository, image, and reviewed mapping contracts to deploy and provision the cluster. |
| 5 | `telemetry` (optional) | Deploys on the service Kubernetes cluster produced by Orchestrator. |
| 6 | `utils` (as needed) | Runs an independent utility workflow. |

BuildStreaM is an alternative automation path for the build and deployment
flows; it is not an additional step after Utils.

### Dependency caching

Initialization caches the dependency state under
`$OMNIA_DATA_PATH/.data/deps-cache/`. When a domain's `requirements.txt` and
`requirements.yml` are unchanged, their installation is skipped on later
initialization runs. Use `--force-deps` when the dependencies must be
reinstalled.

After setup, [select or update the catalog](update_catalog.md), use
[`omnia-cli`](omnia_cli.md) to review the staged domain inputs, and then
[prepare the base infrastructure](prepare_base.md).
