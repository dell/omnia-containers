# Configure Environment

## Overview

The omnia.env file is the single source of truth for environment configuration in Omnia v2.3. It contains all the environment variables required for domain execution.

## Prerequisites

- [Setup the OIM](setup_oim.md) is complete
- Root or equivalent privileges

## Procedure

1. **Edit the environment file**:

    ```bash title="Run on: OIM host"
    vi /etc/omnia/omnia.env
    ```

    Or edit the source file and re-run setup:
    ```bash
    cd /path/to/omnia/src/main
    vi omnia.env
    ./omnia.sh -s
    ```

2. **Configure the required variables**:

    ```bash title="File: /etc/omnia/omnia.env"
    # Required
    OMNIA_VERSION=2.3.0
    OMNIA_BRANCH=main
    OIM_HOSTNAME=oim.example.com
    OIM_IP=192.168.1.100
    SYSTEM_ADMIN_NIC_IPV4=192.168.1.100
    ADMIN_PASSWORD=your_password

    # Optional
    TIMEZONE=UTC
    LANG=en_US.UTF-8
    OMNIA_DATA_PATH=/opt/omnia
    OMNIA_VENV_PATH=/opt/omnia/venv
    OMNIA_PROJECT_NAME=project_default
    ```

3. **Reload the environment**:

    ```bash title="Run on: OIM host"
    source /etc/profile.d/omnia-env.sh
    ```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OMNIA_VERSION` | Yes | - | Omnia version |
| `OMNIA_BRANCH` | Yes | - | Git branch for source code |
| `OIM_HOSTNAME` | Yes | - | OIM hostname |
| `OIM_IP` | Yes | - | OIM IP address |
| `SYSTEM_ADMIN_NIC_IPV4` | Yes | - | Admin network IPv4 address |
| `ADMIN_PASSWORD` | Yes | - | Admin password for services |
| `TIMEZONE` | No | UTC | System timezone |
| `LANG` | No | en_US.UTF-8 | System language |
| `OMNIA_DATA_PATH` | No | /opt/omnia | Root Omnia runtime data directory |
| `OMNIA_VENV_PATH` | No | /opt/omnia/venv | Python virtual environment path |
| `OMNIA_PROJECT_NAME` | No | project_default | Active project name |

## Verification

After updating the environment:

1. **Verify environment variables are loaded**:
    ```bash
    env | grep OMNIA
    ```

2. **Check that the environment file is valid**:
    ```bash
    ./omnia.sh --check-deps
    ```

3. **Re-run setup if needed**:
    ```bash
    ./omnia.sh -s
    ```

## Troubleshooting

- **Environment variables not loaded**: Ensure `/etc/profile.d/omnia-env.sh` exists and source it manually.
- **Validation fails**: Check that `SYSTEM_ADMIN_NIC_IPV4` is a valid IPv4 address.
- **Changes not reflected**: Re-run `./omnia.sh -s` to apply changes system-wide.

## Next Steps

- [Initialize Domains](initialize_domains.md) -- Stage input files with updated environment
- [Run Domains](run_domains.md) -- Execute domain workflows