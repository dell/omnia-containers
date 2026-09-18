# Configure the Main environment

## Overview

`src/main/omnia.env` is the initial environment template. During the first OIM
setup, Main installs it as `/etc/omnia/omnia.env` and creates
`/etc/profile.d/omnia-env.sh` so that new login shells load the installed
values. After installation, `/etc/omnia/omnia.env` is authoritative and
subsequent setup runs preserve it.

## Prerequisites

- Use an Omnia source checkout on the OIM.
- Identify the IPv4 address assigned to the OIM administrative interface.
- Confirm the OIM short hostname with `hostname -s`.
- Decide whether the default data, project, virtual-environment, domain, and
  catalog paths are suitable for the deployment.

## Procedure

1. Change to the Main source directory and open `src/main/omnia.env`:

    ```bash title="Run on: OIM host"
    cd src/main
    vi omnia.env
    ```

2. Set `SYSTEM_ADMIN_NIC_IPV4` to an address assigned to the OIM. Review the
   optional values and keep or replace their supplied defaults:

    ```bash title="File: src/main/omnia.env"
    SYSTEM_ADMIN_NIC_IPV4=172.16.107.254
    OMNIA_DATA_PATH=/opt/omnia
    OMNIA_PROJECT_NAME=project_default
    SYSTEM_HOSTNAME=oim
    SYSTEM_DOMAIN_NAME=omnia.cluster
    OMNIA_VENV_PATH=/opt/omnia/venv
    OMNIA_VERSION=2.3.0.0
    CATALOG_FILE_PATH=${OMNIA_DATA_PATH}/catalog/catalog_rhel.json
    ```

    `SYSTEM_HOSTNAME` must match the value returned by `hostname -s`. A
    mismatch between `SYSTEM_DOMAIN_NAME` and `hostname -d` produces a warning.

    !!! note

        After the first setup, edit `/etc/omnia/omnia.env` for configuration
        changes. If you instead update `src/main/omnia.env`, run
        `./omnia.sh -s --force-env` to replace the installed environment with
        the updated source file.

3. Install the environment as part of OIM setup:

    ```bash title="Run on: OIM host"
    ./omnia.sh --setup-venv
    ```

4. After setup, load the installed environment and activate the shared virtual
   environment in the current shell:

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    ```

    If `OMNIA_DATA_PATH` is customized, source
    `<OMNIA_DATA_PATH>/activate-omnia.sh` instead.

## Verification

Verify that Main installed the source configuration and exported the selected
values:

```bash title="Run on: OIM host"
source /etc/profile.d/omnia-env.sh
printf '%s\n' "$SYSTEM_ADMIN_NIC_IPV4"
printf '%s\n' "$OMNIA_DATA_PATH"
printf '%s\n' "$OMNIA_PROJECT_NAME"
```

The printed values must match `/etc/omnia/omnia.env`.

## Next steps

- [Set up the OIM](setup_oim.md) to install the configured environment and
  create the shared virtual environment.

## Troubleshooting

- **The administrative address is rejected**: Set `SYSTEM_ADMIN_NIC_IPV4` to
  an IPv4 address assigned to a local OIM interface.
- **Hostname validation fails**: Make `SYSTEM_HOSTNAME` match `hostname -s`.
- **The installed values did not change**: After the first setup, edit
  `/etc/omnia/omnia.env` for normal configuration changes. To intentionally
  replace it with `src/main/omnia.env`, run
  `./omnia.sh --setup-venv --force-env`.
- **The activation script is not at `/opt/omnia`**: Use the configured
  `OMNIA_DATA_PATH` when locating `activate-omnia.sh`.
