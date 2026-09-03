# Initialize Domains

## Overview

Domain initialization stages input files from the source repository to the runtime location and installs domain-specific dependencies. This step is required before running any domain.

## Prerequisites

- [Setup the OIM](setup_oim.md) is complete
- Source repository is available on the OIM host
- Network connectivity to download dependencies (if not using cached dependencies)

## Procedure

1. **Initialize all domains**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --init
    ```

    This initializes all domains in dependency order:
    - repo_manager
    - image_build_manager
    - discovery
    - orchestrator
    - telemetry
    - build_stream
    - utils

2. **Initialize a specific domain**:

    ```bash title="Run on: OIM host"
    ./omnia.sh -i repo_manager
    ```

3. **Initialize multiple specific domains**:

    ```bash title="Run on: OIM host"
    ./omnia.sh -i repo_manager,telemetry
    ```

4. **Initialize all domains except specific ones**:

    ```bash title="Run on: OIM host"
    ./omnia.sh -i --skip telemetry
    ```

5. **Preview initialization without executing**:

    ```bash title="Run on: OIM host"
    ./omnia.sh -i --dry-run
    ```

## Initialization Options

| Option | Description |
|--------|-------------|
| `--init` | Initialize all domains (stage input files + deps) |
| `-i <domain>` | Initialize single domain |
| `-i <domain1>,<domain2>` | Initialize specific domains |
| `-i --force-deps` | Force reinstall deps for all domains |
| `-i --skip <domain>` | Initialize all domains except specified |
| `-i --dry-run` | Preview which domains would be initialized |

## What Initialization Does

For each domain, `domain-init.sh` performs:

1. **Installs pip packages** from the domain's `requirements.txt`
2. **Installs Ansible Galaxy collections** from the domain's `requirements.yml`
3. **Creates Ansible log directories**
4. **Copies input files** from `src/<domain>/input/` to `/opt/omnia/<domain>/input/<project>/`

## Dependency Caching

On first run, each domain's `requirements.txt` and `requirements.yml` are hashed (MD5). On subsequent runs, if the file hasn't changed, the install step is skipped entirely — saving 10-30s per domain.

Use `--force-deps` to bypass the cache. Cache files live at `$OMNIA_DATA_PATH/.data/deps-cache/`.

## Input File Flow

```
Source (git repo)                        Runtime (NFS share / data path)
─────────────────                        ─────────────────────────────
src/<domain>/input/*.yml        ──copy──>  /opt/omnia/<domain>/input/<project>/
  (flat — no project subdir)                     │
                                              ▼
                                     Ansible playbooks read from here
```

- **Source** input files are flat in `src/<domain>/input/` (no project subdirectory)
- **domain-init.sh** copies them into a project-specific directory at the runtime path
- **Playbooks** read from the runtime location only

## Verification

After initialization completes:

1. **Check that input files are staged**:
    ```bash
    ls -la /opt/omnia/repo_manager/input/project_default/
    ```

2. **Verify dependencies are installed**:
    ```bash
    source /opt/omnia/venv/bin/activate
    pip list
    ansible-galaxy collection list
    ```

3. **Check domain status**:
    ```bash
    omnia-cli status
    ```

## Troubleshooting

- **Initialization fails for a specific domain**: Check that the domain's `requirements.txt` and `requirements.yml` are valid. Try with `--force-deps` to bypass the cache.
- **Input files not copied**: Ensure source files exist in `src/<domain>/input/` and check permissions.
- **Permission denied**: Run the initialization with root or equivalent privileges.

## Next Steps

- [Configure Environment](configure_environment.md) -- Fine-tune environment settings
- [Run Domains](run_domains.md) -- Execute domain workflows
