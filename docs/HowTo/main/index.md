# Main

The main domain handles setup, initialization, and cross-domain coordination for the Omnia Infrastructure Manager (OIM).

## Overview

The main domain is responsible for environment configuration, setup, initialization, and cross-domain coordination. It is the first domain that must be executed before any other domains can run.

## When to Use This Domain

- Use when setting up the OIM for the first time
- Use when installing dependencies and creating virtual environment
- Use when staging input files for all domains
- Required for all deployment paths

## Setup Process

The main domain is executed via the `omnia.sh` script:

```bash title="Run on: OIM host"
# Setup (one-time)
./omnia.sh -s

# Initialize domains
./omnia.sh --init

# Initialize specific domains
./omnia.sh -i repo_manager,telemetry
```

## Domain Workflow

The main domain supports the following operations:

| Operation | Description |
|-----------|-------------|
| `-s` | Full setup: venv + deps + input copy + catalog + omnia-cli |
| `-s --deps-only` | Venv + deps only, skip input file staging |
| `-s --skip-catalog` | Setup without catalog copy |
| `-s --skip-omnia-cli` | Setup without omnia-cli install |
| `-s --force-deps` | Force reinstall all dependencies |
| `--init` | Init all domains (stage input files + deps) |
| `-i <domain>` | Init single domain |
| `-i <domain1>,<domain2>` | Init specific domains |
| `-i --force-deps` | Force reinstall deps for all domains |
| `-i --skip <domain>` | Init all domains except specified |
| `--check-deps` | Audit dependency version mismatches |
| `--cleanup` | Remove venv + env (preserve data) |
| `--cleanup --all` | Full reset (remove everything including data) |

## Environment Configuration

The main domain uses `omnia.env` as the single source of truth for environment configuration:

```bash title="File: /opt/omnia/omnia.env"
OMNIA_VERSION=2.3.0
OMNIA_BRANCH=main
OIM_HOSTNAME=oim.example.com
OIM_IP=192.168.1.100
ADMIN_PASSWORD=your_password
TIMEZONE=UTC
LANG=en_US.UTF-8
```

## How-to Guides

- [Setup the OIM](setup_oim.md) -- Set up the OIM environment with omnia.sh
- [Initialize Domains](initialize_domains.md) -- Stage input files and install dependencies
- [Run Domains](run_domains.md) -- Execute domain workflows with tags
- [Check Domain Status](check_domain_status.md) -- Monitor domain health with omnia-cli
- [View Domain Logs](view_domain_logs.md) -- Browse and troubleshoot domain logs
- [Edit Credentials](edit_credentials.md) -- Manage encrypted domain credentials

## Related Guides

- [Getting Started: Full Deployment](../../GetStarted/full_deployment.md)
- [Domain Execution](../../Overview/domain_execution.md)
- [Migration Guide](../../GetStarted/migration_guide.md)

