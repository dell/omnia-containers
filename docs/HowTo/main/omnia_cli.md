# Use the diagnostics CLI

## Overview

`omnia-cli` provides status, input, output, and log diagnostics for every Omnia
domain. Use it to inspect a project without manually locating files under each
domain's data directory.

`./omnia.sh --setup-venv` installs the command at
`/usr/local/bin/omnia-cli`. The same setup installs shared Bash completion for
`omnia-cli`, `omnia.sh`, and `./omnia.sh` at
`/etc/bash_completion.d/omnia-bash-completion`.

## Prerequisites

- Complete [Set up the OIM](setup_oim.md) without `--skip-omnia-cli`.
- Use the account that manages the Omnia project data, or an account with
  permission to read the selected domain's input, output, and log paths.
- Activate the Omnia environment when the current shell does not already load
  `/etc/omnia/omnia.env`:

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    ```

    If `OMNIA_DATA_PATH` is customized, source
    `<OMNIA_DATA_PATH>/activate-omnia.sh` instead.

To load command completion immediately after setup, start a new shell or run:

```bash title="Run on: OIM host"
source /etc/bash_completion.d/omnia-bash-completion
```

## Command reference

```text
omnia-cli <command> [--project <name>] [--limit <n>]
```

| Command | Purpose |
|---|---|
| `status [--project <name>]` | Summarize the canonical status of every domain for a project. |
| `check [--project <name>]` | Validate the expected domain inputs and output locations for a project. |
| `edit <domain> [file] [--project <name>]` | Show the domain input checklist and interactively select or directly open a staged input file. |
| `output <domain> [file] [--project <name>]` | List generated domain artifacts and interactively select or directly display a text output. |
| `logs <domain> [--project <name>] [--limit <n>]` | Find domain runtime, output, and Ansible logs and open or follow a selected log. |
| `repo_manager [--project <name>]` | Validate detailed Repository Manager output, including execution contexts, repository URLs, and the configured certificate. |
| `image_build_manager [--project <name>]` | Validate image-build status, functional-group artifact entries, S3 settings, and the latest build log. |
| `orchestrator [--project <name>]` | Show Orchestrator status and validate phase-specific output artifacts. |
| `discovery [--project <name>]` | Show Discovery status and validate generated mapping and report artifacts. |
| `telemetry [--project <name>]` | Show Telemetry status and component results. |
| `build_stream [--project <name>]` | Show BuildStreaM status. |
| `utils [--project <name>]` | Show Utils status and generated utility artifacts. |
| `version` | Display the Omnia CLI and release version. |
| `help [<domain>]` | Display general help or help for a supported domain. |

### Options

| Option | Behavior |
|---|---|
| `--project <name>`, `-p <name>` | Select a project. The default is `OMNIA_PROJECT_NAME`, or `project_default` when that variable is unset. |
| `--limit <n>`, `-l <n>` | Limit the number of entries returned by `logs`. The default is 30; the value must be a positive integer. |

Supported domain names are `repo_manager`, `image_build_manager`,
`orchestrator`, `discovery`, `telemetry`, `build_stream`, and `utils`.

## Review domain status

Display the status of every domain for the configured project:

```bash title="Run on: OIM host"
omnia-cli status
```

Select another project without changing `OMNIA_PROJECT_NAME`:

```bash title="Run on: OIM host"
omnia-cli status --project my_cluster
```

The summary reports each domain as successful, failed, incomplete, or not yet
run. A domain's canonical status file determines its state; secondary reports
and artifacts do not replace that status file.

Run a domain command for additional validation:

```bash title="Run on: OIM host"
omnia-cli repo_manager
omnia-cli image_build_manager --project prod
omnia-cli orchestrator
omnia-cli discovery
omnia-cli telemetry
omnia-cli build_stream
omnia-cli utils
```

Repository Manager and Image Build Manager have specialized checks. Other
domain commands validate the canonical status and any required artifacts for
the completed phase, then recursively list the generated output.

## Check project inputs and outputs

```bash title="Run on: OIM host"
omnia-cli check
omnia-cli check --project prod
```

The check reports whether each domain's input and output directories exist and
whether expected input and status files are available. Conditional and
generated inputs are identified separately from files that operators must
provide.

## Review or edit domain input

Display a domain input checklist and choose a staged file interactively:

```bash title="Run on: OIM host"
omnia-cli edit image_build_manager
omnia-cli edit repo_manager --project prod
```

Open a listed file directly:

```bash title="Run on: OIM host"
EDITOR=vim omnia-cli edit orchestrator pxe_mapping_file.csv
```

Plain-text files open with `$EDITOR`, or `$VISUAL` when `EDITOR` is unset.
Credential and Vault-encrypted files open with `ansible-vault edit`. Only a
file shown in the editable-file list can be opened; relative-path traversal and
hidden Vault key files are rejected.

!!! note

    Generated credentials must never be committed. Run the complete domain
    flow to create or update its required Vault-encrypted credential document.

## Inspect generated output

List every artifact below a domain's project output directory:

```bash title="Run on: OIM host"
omnia-cli output telemetry
```

In an interactive terminal, select a numbered text file to open it with
`$PAGER`. Provide a relative filename to print a known text output directly:

```bash title="Run on: OIM host"
omnia-cli output telemetry telemetry_status.yml
omnia-cli output orchestrator provisioning_report.yml --project prod
```

Binary files are listed but not printed. Symbolic links that resolve outside
the selected output directory are rejected.

## Inspect domain logs

The log browser combines and de-duplicates logs from:

1. `$OMNIA_DATA_PATH/<domain>/log/`, including project and shared directories.
2. `$OMNIA_ANSIBLE_LOG_PATH/<domain>/`, with
   `OMNIA_ANSIBLE_LOG_PATH` defaulting to `/var/log/omnia`.
3. Legacy domain-named logs directly under the Ansible log root.
4. The selected domain's project output directory.

Results are sorted newest first. Each entry includes its source, relative path,
size, timestamp, and absolute path.

```bash title="Run on: OIM host"
omnia-cli logs image_build_manager
omnia-cli logs repo_manager --project prod
omnia-cli logs orchestrator --limit 50
omnia-cli logs discovery -l 100
```

In an interactive terminal, select a numbered log to open it with `$PAGER`, or
enter `t` to follow the newest log.

## Data-path resolution

By default, `omnia-cli` resolves input, output, and runtime logs below:

```text
$OMNIA_DATA_PATH/<domain>/input/<project>/
$OMNIA_DATA_PATH/<domain>/output/<project>/
$OMNIA_DATA_PATH/<domain>/log/
```

The CLI honors the domain-specific path overrides in `omnia.env`, including
`REPO_MANAGER_DATA_PATH`, `IMAGE_BUILD_MANAGER_DATA_PATH`,
`DISCOVERY_DATA_PATH`, `ORCHESTRATOR_DATA_PATH`, `TELEMETRY_DATA_PATH`, and
`BUILD_STREAM_DATA_PATH`.

### Canonical status files

| Domain | Status file |
|---|---|
| `repo_manager` | `repo_status.yml` |
| `image_build_manager` | `build_status.yml` |
| `orchestrator` | `orchestrator_status.yml` |
| `discovery` | `discovery_status.yml` |
| `telemetry` | `telemetry_status.yml` |
| `build_stream` | `build_stream_status.yml` |
| `utils` | `utils_status.yml` |

An empty output directory is reported as not run. If output artifacts exist but
the canonical status is missing, the CLI warns that the run might be
incomplete or might predate the current status contract. Orchestrator setup and
inventory artifacts can exist before a provisioning or PXE phase writes
`orchestrator_status.yml`, so that case is reported separately.

## Get help and version information

```bash title="Run on: OIM host"
omnia-cli help
omnia-cli help repo_manager
omnia-cli help logs
omnia-cli version
```

## Troubleshooting

- **`omnia-cli: command not found`**: Rerun `./omnia.sh --setup-venv` without
  `--skip-omnia-cli`, or run `./src/main/omnia-cli` directly from the source
  checkout.
- **The wrong project is displayed**: Pass `--project <name>` or update
  `OMNIA_PROJECT_NAME` in `/etc/omnia/omnia.env`.
- **No output or logs are found**: Confirm the domain has run for the selected
  project and review any domain-specific data-path override in `omnia.env`.
- **A plain input file does not open**: Set `EDITOR` to an installed editor.
- **A Vault file does not open**: Activate the Omnia virtual environment so
  `ansible-vault` is available, then retry and provide the Vault password file
  when prompted.

## Related documentation

- [Main command reference](index.md#command-reference)
- [Main environment configuration](../../Reference/Configuration/omnia_env.md)
- [Playbook reference](../../Reference/Playbooks/playbook_reference.md)
- [Module contracts](../../Reference/index.md#module-contracts)
