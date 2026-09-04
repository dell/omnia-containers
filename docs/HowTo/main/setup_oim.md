# Setup the OIM

## Overview

The main domain's setup process (`omnia.sh -s`) prepares the Omnia Infrastructure Manager (OIM) by creating the Python virtual environment, installing dependencies, staging input files, and installing the omnia-cli tool. This is the first step required before running any other domains.

## Prerequisites

- RHEL 10.x installed on the OIM host
- Root or equivalent privileges
- Network connectivity to download dependencies
- At least 2 NICs connected to admin and BMC networks
- Python 3.11+ available on the system

## Procedure

1. **Clone the Omnia repository**:

    ```bash title="Run on: OIM host"
    git clone https://github.com/dell/omnia.git
    cd omnia
    git checkout 2.3.0
    ```

    This downloads the Omnia source code to your OIM host.

2. **Configure the environment file**:

    ```bash title="Run on: OIM host"
    cd src/main
    vi omnia.env
    ```

    Set the required minimum configuration:

    ```bash title="File: omnia.env"
    OMNIA_VERSION=2.3.0
    OMNIA_BRANCH=main
    OIM_HOSTNAME=oim.example.com
    OIM_IP=192.168.1.100
    SYSTEM_ADMIN_NIC_IPV4=192.168.1.100
    ADMIN_PASSWORD=your_password
    TIMEZONE=UTC
    LANG=en_US.UTF-8
    ```

    !!! warning

        `SYSTEM_ADMIN_NIC_IPV4` is required and must be a valid IPv4 address. The setup will fail without it.

3. **Run the setup script**:

    ```bash title="Run on: OIM host"
    ./omnia.sh -s
    ```

    This performs the following:

    - Validates `omnia.env` and `SYSTEM_ADMIN_NIC_IPV4`
    - Installs `omnia.env` to `/etc/omnia/omnia.env` (system-wide)
    - Creates `/etc/profile.d/omnia-env.sh` for automatic environment loading
    - Validates full environment (hostname, domain, admin NIC match)
    - Creates `/opt/omnia/{log,.data}` base directories
    - Finds Python 3.11+ and creates/updates venv at `$OMNIA_VENV_PATH`
    - Runs each domain's `domain-init.sh` to install dependencies and stage input files
    - Copies catalog files from `src/main/samples/` to `$OMNIA_DATA_PATH/catalog/`
    - Installs `omnia-cli` to `/usr/local/bin/omnia-cli` with bash completion

4. **Verify the setup**:

    ```bash title="Run on: OIM host"
    # Check that environment variables are loaded
    source /etc/profile.d/omnia-env.sh
    echo $OMNIA_DATA_PATH

    # Check domain status
    omnia-cli status

    # Verify Python venv
    which python
    python --version
    ```

## Setup Options

The setup script supports several options:

| Option | Description |
|--------|-------------|
| `-s` | Full setup: venv + deps + input copy + catalog + omnia-cli |
| `-s --deps-only` | Venv + deps only, skip input file staging |
| `-s --skip-catalog` | Setup without catalog copy |
| `-s --skip-omnia-cli` | Setup without omnia-cli install |
| `-s --force-deps` | Force reinstall all dependencies (bypass cache) |

**Examples:**

```bash title="Run on: OIM host"
# Setup without omnia-cli
./omnia.sh -s --skip-omnia-cli

# Setup without catalog copy
./omnia.sh -s --skip-catalog

# Force reinstall all dependencies
./omnia.sh -s --force-deps
```

## Verification

After setup completes successfully:

1. **Check environment variables**:
    ```bash
    env | grep OMNIA
    ```

2. **Verify directory structure**:
    ```bash
    ls -la /opt/omnia/
    ```

    Expected output:
    ```
    /opt/omnia/
    ├── venv/
    ├── .data/
    ├── catalog/
    ├── repo_manager/
    ├── image_build_manager/
    ├── discovery/
    ├── orchestrator/
    ├── telemetry/
    ├── build_stream/
    └── utils/
    ```

3. **Check domain status**:
    ```bash
    omnia-cli status
    ```

## Troubleshooting

- **Setup fails with "SYSTEM_ADMIN_NIC_IPV4 not set"**: Ensure `SYSTEM_ADMIN_NIC_IPV4` is set in `omnia.env` and is a valid IPv4 address.
- **Python not found**: Ensure Python 3.11+ is installed and available in the system PATH.
- **Permission denied**: Run the setup script with root or equivalent privileges.
- **Dependency installation fails**: Check network connectivity and try with `--force-deps` to bypass the cache.

## Next Steps

- [Configure Environment](configure_environment.md) -- Fine-tune environment settings
- [Initialize Domains](initialize_domains.md) -- Initialize specific domains for execution
- [Run Domains](run_domains.md) -- Execute domain workflows
