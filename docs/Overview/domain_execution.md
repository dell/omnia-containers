# Running Deployment Modules

## Overview

Omnia provides seven independently invocable deployment-module entry playbooks. The
`src/main/omnia.sh` script installs and activates the shared runtime, validates
the requested module identifier, and invokes its top-level playbook.

The supported domain identifiers are `repo_manager`, `image_build_manager`,
`discovery`, `orchestrator`, `telemetry`, `build_stream`, and `utils`.

`--run` accepts one module's internal domain identifier per command. It does
not accept `all` or a comma-separated list. Run each required module in dependency order, or
use the BuildStreaM pipeline path where applicable.

For example:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator
    ansible-playbook playbooks/orchestrator.yml
    ```

## Prepare the common runtime

From the Omnia source tree on the OIM, edit the environment first:

```bash title="Run on: OIM host"
cd src/main
vi omnia.env
```

Review these environment variables for the deployment:

- `SYSTEM_ADMIN_NIC_IPV4` must identify an IPv4 address assigned to the OIM
  administrative NIC.
- `OMNIA_DATA_PATH` is the data directory for all persistent Omnia data,
  whether NFS-mounted or local.
- `OMNIA_PROJECT_NAME` is the project name that maps to input and output
  subdirectories.
- `SYSTEM_HOSTNAME` is the short hostname of the OIM, not the FQDN.
- `SYSTEM_DOMAIN_NAME` is the domain name of the OIM.
- `OMNIA_VENV_PATH` is the path to the shared Omnia Python virtual environment.
- `CATALOG_FILE_PATH` is the path to the catalog JSON used by catalog-aware
  operations.

Set up the shared virtual environment, install module dependencies, create
runtime directories, stage input templates, and copy the supplied catalog
samples:

```bash title="Run on: OIM host"
./omnia.sh --setup-venv
```

Useful initialization variants implemented by `omnia.sh` include:

| Command | Effect |
|---|---|
| `./omnia.sh --setup-venv --deps-only` | Install the shared environment and dependencies without staging module inputs. |
| `./omnia.sh --setup-venv --skip <domain>` | Set up all modules except the comma-separated skip list. `<domain>` is a module's internal CLI identifier. |
| `./omnia.sh --init <domain>` | Initialize one module without repeating full common setup. |
| `./omnia.sh --init <domain1>,<domain2>` | Initialize the named modules. Comma-separated lists are supported by `--init`, not by `--run`. |
| `./omnia.sh --init --dry-run` | Show which module initialization scripts would run. |
| `./omnia.sh --check-deps` | Audit installed dependency versions against module declarations. |

Initialization copies source templates from `src/<domain>/input/` to the
domain's runtime data root:

```text
<RUNTIME_DATA_ROOT>/input/<OMNIA_PROJECT_NAME>/
```

For domains that implement a component-specific path, the initializer uses
that value and otherwise derives the root from `OMNIA_DATA_PATH`. For example,
Orchestrator resolves `ORCHESTRATOR_DATA_PATH` first and otherwise uses
`<OMNIA_DATA_PATH>/orchestrator`. Discovery and BuildStreaM currently use
`<OMNIA_DATA_PATH>/discovery` and `<OMNIA_DATA_PATH>/build_stream` directly.

Edit the staged project inputs before running a deployment phase. Existing
files may require confirmation before an initialization script overwrites them.

`./omnia.sh --prepare-base` runs the validation, `credentials`, and `prepare`
phases for Repository Manager, Image Build Manager, and Orchestrator. During
the validation phase, it runs `precheck` for Repository Manager and `validate`
for Image Build Manager and Orchestrator. It does not synchronize repositories,
build images, or provision nodes. No separate Repository Manager `precheck` is
required after the helper completes successfully.

## Run one module

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

For example:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run image_build_manager --tags validate
    ./omnia.sh --run image_build_manager --tags prepare
    ./omnia.sh --run image_build_manager --tags build
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/image_build_manager
    ansible-playbook playbooks/image_build_manager.yml --tags validate
    ansible-playbook playbooks/image_build_manager.yml --tags prepare
    ansible-playbook playbooks/image_build_manager.yml --tags build
    ```

`omnia.sh` activates the configured virtual environment and runs:

```text
src/<domain>/playbooks/<domain>.yml
```

Except where the module entry playbook explicitly documents a safe combination,
select one tag per invocation. Running without `--tags` uses that module's own
default flow; defaults differ between modules.

## Required deployment sequence

For a direct cluster deployment, run modules in this dependency order:

| Step | Deployment module | Requirement and handoff |
|---|---|---|
| 1 | `repo_manager` | Synchronizes catalog content and writes `repo_status.yml`. |
| 2 | `image_build_manager` | Reads successful Repository Manager output, builds functional-group images, and writes `build_status.yml`. |
| 3 | `discovery` (optional) | Writes `bmc_pxe_mapping_file.csv`. Skip Discovery only when supplying a reviewed PXE mapping directly. |
| 4 | `orchestrator` | Reads repository and image outputs plus the PXE mapping, then deploys OpenCHAMI and provisions selected Slurm or service Kubernetes groups. |
| 5 | `telemetry` (optional) | Uses the generated Orchestrator inventory and requires a provisioned service Kubernetes cluster. LDMS additionally requires Slurm control and compute nodes. |
| 6 | `utils` (on demand) | Runs an operation-specific utility and is not a required deployment stage. |

BuildStreaM is not an additional final step in this direct sequence. It is an
alternative automation path: its build pipeline invokes Repository Manager and
Image Build Manager, and its deploy pipeline invokes Orchestrator.

## Module operations and tags

Tags are module-specific. The following table lists the implemented
customer-facing entry operations. Reserved or placeholder operations are
identified per module and are not deployment procedures.

| Deployment module | Principal tags |
|---|---|
| `repo_manager` | `precheck`, `credentials`, `prepare`/`deploy`, `download`/`execute`, `status`, `cleanup_pulp`/`cleanup`, `cleanup_repos`, and catalog-operation tags |
| `image_build_manager` | `precheck`, `validate`, `credentials`, `prepare`, `build`/`execute`, `x86_64`, `aarch64`, `cleanup`, `cleanup_images` |
| `discovery` | `precheck`, `validate`, `credentials`, `execute`, the `discovery` execution alias, `cleanup`, and `cleanup_credentials`; `prepare`, `upgrade`, and `rollback` currently select placeholder flows |
| `orchestrator` | `precheck`, `validate`, `credentials`, `prepare`, `deploy`, `provision`, `execute`, `validate-deployment`, `pxeboot`, `cleanup`, `cleanup_credentials`, and `upgrade`; `rollback` is reserved and unsupported |
| `telemetry` | `precheck`, `validate`/`validation`/`prepare`, `credentials`, `execute`/`deploy`, `cleanup`, source-specific cleanup tags, `external_kafka`, `external_victoria` |
| `build_stream` | `precheck`, `validate`, `credentials`, `prepare`, `execute`, `build`, `cleanup` |
| `utils` | `precheck`, `collect`, `install_os`, `backup_oim_logs`, `cleanup`, `cleanup_logs`, `cleanup_install_os`, `cleanup_backup_oim_logs`; running without a tag performs setup only |

Repository Manager's standard tags can be combined in the order implemented by
its entry playbook. Other module entry points direct operators to run one tag
at a time. Cleanup tags are explicit operations and are not selected by the
normal untagged deployment flows.

Orchestrator accepts `upgrade` and `rollback`. Its `upgrade` tag invokes the
current OpenCHAMI and OpenLDAP component workflows; review their documented
limitations before use. Its `rollback` workflows are reserved and intentionally
fail because rollback is not supported in this release.

## Direct deployment example

The following example shows the module invocations, not the input-editing steps
required by each module:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main

    ./omnia.sh --run repo_manager --tags precheck
    ./omnia.sh --run repo_manager --tags prepare
    ./omnia.sh --run repo_manager --tags download
    ./omnia.sh --run repo_manager --tags status

    ./omnia.sh --run image_build_manager --tags validate
    ./omnia.sh --run image_build_manager --tags prepare
    ./omnia.sh --run image_build_manager --tags build

    # Optional when a valid PXE mapping is supplied directly.
    ./omnia.sh --run discovery --tags validate
    ./omnia.sh --run discovery --tags execute

    ./omnia.sh --run orchestrator --tags validate
    ./omnia.sh --run orchestrator --tags precheck
    ./omnia.sh --run orchestrator --tags prepare
    ./omnia.sh --run orchestrator --tags execute

    # Optional; requires service Kubernetes from Orchestrator.
    ./omnia.sh --run telemetry --tags validate
    ./omnia.sh --run telemetry --tags precheck
    ./omnia.sh --run telemetry --tags deploy
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh

    cd <OMNIA_SOURCE_PATH>/src/repo_manager
    ansible-playbook playbooks/repo_manager.yml --tags precheck
    ansible-playbook playbooks/repo_manager.yml --tags prepare
    ansible-playbook playbooks/repo_manager.yml --tags download
    ansible-playbook playbooks/repo_manager.yml --tags status

    cd <OMNIA_SOURCE_PATH>/src/image_build_manager
    ansible-playbook playbooks/image_build_manager.yml --tags validate
    ansible-playbook playbooks/image_build_manager.yml --tags prepare
    ansible-playbook playbooks/image_build_manager.yml --tags build

    # Optional when a valid PXE mapping is supplied directly.
    cd <OMNIA_SOURCE_PATH>/src/discovery
    ansible-playbook playbooks/discovery.yml --tags validate
    ansible-playbook playbooks/discovery.yml --tags execute

    cd <OMNIA_SOURCE_PATH>/src/orchestrator
    ansible-playbook playbooks/orchestrator.yml --tags validate
    ansible-playbook playbooks/orchestrator.yml --tags precheck
    ansible-playbook playbooks/orchestrator.yml --tags prepare
    ansible-playbook playbooks/orchestrator.yml --tags execute

    # Optional; requires service Kubernetes from Orchestrator.
    cd <OMNIA_SOURCE_PATH>/src/telemetry
    ansible-playbook playbooks/telemetry.yml --tags validate
    ansible-playbook playbooks/telemetry.yml --tags precheck
    ansible-playbook playbooks/telemetry.yml --tags deploy
    ```

Review the module's [How-to guide](../HowTo/index.md) before running these
commands. Each guide identifies its required inputs, credentials, conditional
features, and output contract.

## Verify module outputs

Module status and handoff files are stored under the selected project output
directory. Verify the files relevant to the executed flow:

```bash title="Run on: OIM host"
source /etc/profile.d/omnia-env.sh
repo_manager_path="${REPO_MANAGER_DATA_PATH:-${OMNIA_DATA_PATH}/repo_manager}"
image_build_manager_path="${IMAGE_BUILD_MANAGER_DATA_PATH:-${OMNIA_DATA_PATH}/image_build_manager}"
orchestrator_path="${ORCHESTRATOR_DATA_PATH:-${OMNIA_DATA_PATH}/orchestrator}"
telemetry_path="${TELEMETRY_DATA_PATH:-${OMNIA_DATA_PATH}/telemetry}"

cat "$repo_manager_path/output/$OMNIA_PROJECT_NAME/repo_status.yml"
cat "$image_build_manager_path/output/$OMNIA_PROJECT_NAME/build_status.yml"
cat "$orchestrator_path/output/$OMNIA_PROJECT_NAME/orchestrator_status.yml"
cat "$telemetry_path/output/$OMNIA_PROJECT_NAME/telemetry_status.yml"
```

Discovery primarily produces CSV results, BuildStreaM reports its prepared
services in `build_stream_status.yml`, and Utils writes `utils_status.yml` plus
operation-specific results. A file's presence alone is not success; inspect its
reported state and the corresponding module log.

## Troubleshooting

- **Unknown module identifier:** Use one of `repo_manager`, `image_build_manager`,
  `discovery`, `orchestrator`, `telemetry`, `build_stream`, or `utils`.
- **Virtual environment is missing:** Run `./omnia.sh --setup-venv` from
  `src/main`.
- **A downstream contract is missing:** Complete the producer module and verify
  its reported success before running the consumer.
- **Inputs are not found:** Confirm `OMNIA_DATA_PATH`, `OMNIA_PROJECT_NAME`,
  and any path override implemented by the affected domain, then verify the
  staged module input directory. For Orchestrator, check
  `ORCHESTRATOR_DATA_PATH`; when it is unset, the path falls back to
  `<OMNIA_DATA_PATH>/orchestrator`. Discovery and BuildStreaM use paths below
  `OMNIA_DATA_PATH` directly.
- **A tag is rejected or does nothing:** Check the module entry playbook. Tags
  and default flows are not uniform, and some source tags are placeholders.

See [module-specific troubleshooting](../Troubleshooting/index.md) and the
[Module Playbook Entry Points](../Reference/Playbooks/playbook_reference.md)
for additional routing.
