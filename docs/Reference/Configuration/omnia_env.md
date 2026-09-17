# omnia.env

`omnia.env` is the shared environment configuration used by `omnia.sh`, module
initialization scripts, and Ansible playbooks. Edit `src/main/omnia.env` before
the first OIM setup. After installation, `/etc/omnia/omnia.env` is authoritative
and is preserved by subsequent setup runs.

## Location

```text
Source:    src/main/omnia.env
Installed: /etc/omnia/omnia.env
```

Source the installed environment before running Omnia commands directly:

```bash
set -a
source /etc/omnia/omnia.env
set +a
```

For normal changes after setup, edit `/etc/omnia/omnia.env`. To intentionally
replace the installed environment with the source template, run
`./omnia.sh --setup-venv --force-env`.

## Variables

| Variable | Requirement | Source value | Purpose |
|---|---|---|---|
| `SYSTEM_ADMIN_NIC_IPV4` | Required | `172.16.107.254` | OIM admin-network IPv4 address used by platform services. |
| `OMNIA_DATA_PATH` | Optional | `/opt/omnia` | Root for persistent module data. |
| `OMNIA_PROJECT_NAME` | Optional | `project_default` | Selects each module's input and output project directory. |
| `SYSTEM_HOSTNAME` | Optional | `oim` | Short hostname of the OIM host. |
| `SYSTEM_DOMAIN_NAME` | Optional | `omnia.cluster` | Domain name of the OIM host. |
| `OMNIA_VENV_PATH` | Optional | `/opt/omnia/venv` | Shared Python virtual environment created during setup. |
| `OMNIA_VERSION` | Optional | `2.3` | Omnia release version. |
| `CATALOG_FILE_PATH` | Optional | `${OMNIA_DATA_PATH}/catalog/catalog_rhel.json` | Shared catalog path consumed by catalog-aware modules. |

The source also provides optional component path overrides:

```bash
# IMAGE_BUILD_MANAGER_DATA_PATH=${OMNIA_DATA_PATH}/image_build_manager
# DISCOVERY_DATA_PATH=${OMNIA_DATA_PATH}/discovery
# ORCHESTRATOR_DATA_PATH=${OMNIA_DATA_PATH}/orchestrator
```

Image Build Manager and Orchestrator consume their component-specific path
overrides. If an applicable override is unset or empty, that component uses
`${OMNIA_DATA_PATH}/<component>`. Repository Manager always uses
`${OMNIA_DATA_PATH}/repo_manager`. Discovery, Telemetry, and BuildStreaM derive
their runtime paths directly from `OMNIA_DATA_PATH`. Do not set
`DISCOVERY_DATA_PATH` to a different root. For example,
`ORCHESTRATOR_DATA_PATH=/data/orchestrator` selects
`/data/orchestrator/input/$OMNIA_PROJECT_NAME` and
`/data/orchestrator/output/$OMNIA_PROJECT_NAME`; it does not append another
`orchestrator` directory. Upstream consumers use the producer's component path,
so Orchestrator resolves Image Build Manager output from
`IMAGE_BUILD_MANAGER_DATA_PATH` before falling back to
`${OMNIA_DATA_PATH}/image_build_manager`.

For an existing deployment that stores Repository Manager data outside the
common hierarchy, move that data into `${OMNIA_DATA_PATH}/repo_manager` before
running Repository Manager. Changing `OMNIA_DATA_PATH` changes the common data
root for every domain.

For an existing deployment that stores Telemetry data outside the common
hierarchy, move that data into `${OMNIA_DATA_PATH}/telemetry` before running
Telemetry.

Do not add credentials to `omnia.env`; module credential playbooks create their
own encrypted credential files.

## Related configuration

- [Repo Manager configuration](repo_manager_config.md)
- [Image Build configuration](image_build_manager_config.md)
- [Orchestrator configuration](orchestrator_config.md)
