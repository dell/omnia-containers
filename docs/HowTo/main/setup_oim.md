# Set up the OIM

## Overview

`omnia.sh --setup-venv` installs the Main environment during the first setup,
creates or updates the shared Python virtual environment, initializes the
selected modules, installs `omnia-cli` and shared Bash completion, and ensures
that an active catalog exists. Later setup runs preserve the installed
environment. Use this command to set up the Omnia Infrastructure Manager
(OIM).

## Prerequisites

- Use an Omnia source checkout on the OIM.
- Install Python 3.11 or later. `omnia.sh` searches for `python3.12`, `python3.11`,
  and then `python3`.
- Use an account that can write to `/etc/omnia`, `/etc/profile.d`, the
  configured data path, and the configured virtual-environment path.
- Make the Python and Ansible Galaxy package sources declared by the modules
  available during initialization.
- [Configure `src/main/omnia.env`](configure_environment.md). In particular:

    - `SYSTEM_ADMIN_NIC_IPV4` must be an IPv4 address assigned to the OIM.
    - `SYSTEM_HOSTNAME` must match `hostname -s`.

## Procedure

1. Change to the Main source directory:

    ```bash title="Run on: OIM host"
    cd src/main
    ```

2. Run setup:

    ```bash title="Run on: OIM host"
    ./omnia.sh --setup-venv
    ```

    The short form is `./omnia.sh -s`. The command:

    - Installs `omnia.env` as `/etc/omnia/omnia.env` during the first setup.
      Subsequent setup runs preserve the installed file unless `--force-env`
      is specified.
    - Creates `/etc/profile.d/omnia-env.sh`.
    - Validates the OIM hostname, domain name, and administrative NIC address.
    - Creates `<OMNIA_DATA_PATH>`, `<OMNIA_DATA_PATH>/.data`, and the virtual
      environment at `OMNIA_VENV_PATH`.
    - Upgrades `pip`, `setuptools`, and `wheel` in the virtual environment.
    - Runs each selected module's `domain-init.sh`.
    - Installs the default catalog at `CATALOG_FILE_PATH` only when an active
      catalog does not already exist. Deployment-specific catalogs remain
      available for explicit selection with `--select-catalog`.
    - Installs `omnia-cli` in `/usr/local/bin` and shared completion for
      `omnia-cli` and `omnia.sh` in `/etc/bash_completion.d`.

3. Use setup options when required:

    | Option | Result |
    |---|---|
    | `--deps-only` | Install module dependencies without staging module inputs. |
    | `--force-deps` | Bypass the dependency cache and reinstall dependencies. |
    | `--force-env` | Replace `/etc/omnia/omnia.env` with `src/main/omnia.env`. Use only when intentionally resetting the installed environment from the source template. |
    | `--skip <domain,...>` | Skip the modules identified by the listed internal domain names during initialization. |
    | `--dry-run` | Preview the modules that would be initialized. Environment and virtual-environment setup, catalog copying, and other setup operations still run. |
    | `--skip-catalog` | Do not install a missing default catalog. An existing active catalog is always preserved. |
    | `--skip-omnia-cli` | Do not install `omnia-cli` or shared `omnia-cli`/`omnia.sh` Bash completion. |

    For example:

    ```bash title="Run on: OIM host"
    ./omnia.sh --setup-venv --skip telemetry,utils
    ```

4. Load the installed environment and activate the virtual environment:

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    ```

    If `OMNIA_DATA_PATH` is customized, source
    `<OMNIA_DATA_PATH>/activate-omnia.sh` instead.

## Verification

Verify the installed environment and dependencies:

```bash title="Run on: OIM host"
ansible --version
pip list
ansible-galaxy collection list
ls /etc/omnia/omnia.env
omnia-cli version
```

## Next steps

- [Select or update the catalog](update_catalog.md) when the default catalog
  does not match the required workload, architecture, or VAST selection.
- [Use the diagnostics CLI](omnia_cli.md) to review domain inputs, output, and
  logs.
- [Prepare the base infrastructure](prepare_base.md) to validate the core
  domain inputs, collect credentials, and deploy the services required before
  repository synchronization and image building.

## Troubleshooting

- **`SYSTEM_ADMIN_NIC_IPV4` is missing or invalid**: Before the first setup,
  set a valid IPv4 address in `src/main/omnia.env`. After setup, update
  `/etc/omnia/omnia.env`.
- **The administrative address is not local**: Select an address assigned to
  an OIM network interface.
- **The hostname check fails**: Make `SYSTEM_HOSTNAME` match `hostname -s`. A
  domain-name mismatch is reported as a warning.
- **Python is unavailable or older than 3.11**: Install a supported Python
  version and rerun setup.
- **Setup was interrupted**: Rerun `./omnia.sh --setup-venv`; Main reports that
  the virtual environment might be incomplete.
- **A dependency remains cached**: Rerun setup with `--force-deps`.
