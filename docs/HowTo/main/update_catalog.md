# Select or update the catalog

## Overview

The catalog selects the operating-system version, node architectures,
functional layers, software groups, packages, and artifact sources used by
Repo Manager, Image Build Manager, and Orchestrator.

Omnia includes a default catalog at:

```text
src/main/samples/catalog_rhel.json
```

The default catalog targets RHEL 10.0 and combines x86_64 management and
service Kubernetes layers with aarch64 Slurm compute layers without VAST.
Additional deployment-specific catalogs for RHEL 10.0 and RHEL 10.2 are
available under:

```text
src/main/samples/catalogs/<RHEL-version>/
```

During `./omnia.sh --setup-venv`, Main copies only the top-level JSON and YAML
files from `src/main/samples` to `$OMNIA_DATA_PATH/catalog`. Catalogs in the
versioned `catalogs` subdirectory must be selected and copied explicitly.

## Prerequisites

- Complete [Set up the OIM](setup_oim.md).
- Determine the RHEL version, node architecture, workload, and whether the
  deployment requires the VAST software group.
- Ensure the functional layers in the selected catalog match the functional
  groups that will be built and provisioned.
- Use an account that can copy files to `$OMNIA_DATA_PATH/catalog` and edit
  `/etc/omnia/omnia.env`.

## Procedure

1. Change to the Omnia source directory and load the installed environment:

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>
    set -a
    source /etc/omnia/omnia.env
    set +a
    ```

2. Choose the catalog that matches the target RHEL version and deployment.
   The same catalog filenames are available under the `10.0` and `10.2`
   directories:

    | Deployment | With VAST | Without VAST |
    |---|---|---|
    | Slurm on x86_64 | `slurm_x86_64.json` | `slurm_x86_64_no_vast.json` |
    | Slurm on aarch64 | `slurm_aarch64.json` | `slurm_aarch64_no_vast.json` |
    | Slurm with x86_64 control and login nodes and aarch64 compute and compiler nodes | `slurm_x86_64_aarch64.json` | `slurm_x86_64_aarch64_no_vast.json` |
    | Slurm and service Kubernetes on x86_64 | `slurm_service_k8s_x86_64.json` | `slurm_service_k8s_x86_64_no_vast.json` |
    | Slurm with x86_64 control and login nodes, aarch64 compute and compiler nodes, and service Kubernetes on x86_64 | `slurm_service_k8s_combined.json` | `slurm_service_k8s_combined_no_vast.json` |
    | Service Kubernetes on x86_64 | `service_k8s_x86_64.json` | Not applicable; this catalog does not include the VAST software group. |

    Catalogs whose names end in `_no_vast.json` omit
    `vast_stack_driver_groupv1`. The corresponding Slurm catalogs without
    that suffix include the VAST group.

3. Copy the selected catalog to the runtime catalog directory. For example:

    ```bash title="Run on: OIM host"
    cp src/main/samples/catalogs/10.0/slurm_x86_64_no_vast.json \
      "${OMNIA_DATA_PATH}/catalog/slurm_x86_64_no_vast.json"
    ```

    This example selects the RHEL 10.0 variant. Use the corresponding file
    under `src/main/samples/catalogs/10.2/` when building RHEL 10.2 nodes.

    Keep the default `catalog_rhel.json` when it already matches the intended
    deployment.

4. Set `CATALOG_FILE_PATH` in `/etc/omnia/omnia.env` to the selected file. For
   the preceding example, use:

    ```bash title="File: /etc/omnia/omnia.env"
    CATALOG_FILE_PATH=${OMNIA_DATA_PATH}/catalog/slurm_x86_64_no_vast.json
    ```

    `CATALOG_FILE_PATH` must resolve to an absolute path ending in `.json` and
    identify an existing regular file. Select the file itself; do not set the
    variable to `src/main/samples/catalogs` or another directory.

    Before the first OIM setup, make environment changes in
    `src/main/omnia.env`. After setup, use `/etc/omnia/omnia.env`; later setup
    runs preserve the installed file unless `--force-env` is specified.

## Verification

1. Reload the installed environment and confirm the selected path:

    ```bash title="Run on: OIM host"
    set -a
    source /etc/omnia/omnia.env
    set +a
    printf '%s\n' "$CATALOG_FILE_PATH"
    test -f "$CATALOG_FILE_PATH"
    ```

2. Confirm that the file contains valid JSON:

    ```bash title="Run on: OIM host"
    python3 -m json.tool "$CATALOG_FILE_PATH" >/dev/null
    ```

3. Run Repo Manager precheck to validate the environment, catalog, and Repo
   Manager inputs:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run repo_manager --tags precheck
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/repo_manager
        ansible-playbook playbooks/repo_manager.yml --tags precheck
        ```

## Next steps

- [Prepare the base infrastructure](prepare_base.md) to validate the selected
  base domains, collect credentials, and deploy their services.
- [Configure and synchronize repositories](../repo_manager/configure_repos.md)
  to make the selected catalog content available and generate
  `repo_status.yml`.
- [Build OS images](../image_build_manager/build_images.md) for the functional
  layers and architectures selected by the catalog.
- See the [Catalog JSON reference](../../Reference/SampleFiles/catalog_json.md)
  for the standard runtime and source locations.

## Troubleshooting

- **`CATALOG_FILE_PATH` is empty**: Set it in `/etc/omnia/omnia.env` after OIM
  setup, then rerun the command. Main loads the installed environment for
  subsequent operations.
- **The catalog path is rejected**: Use an absolute path to an existing regular
  file whose name ends in `.json`. Do not specify the catalog directory.
- **The catalog file is not valid JSON**: Correct the reported JSON syntax or
  recopy the unmodified source sample.
- **The expected functional group is not built**: Confirm that the selected
  catalog contains the matching functional layer and architecture. Choose a
  combined catalog when both Slurm and service Kubernetes layers are required.
- **VAST content is included unexpectedly**: Select the corresponding
  `_no_vast.json` catalog and update `CATALOG_FILE_PATH`.
- **A later setup restores the default catalog file**: Main refreshes the
  top-level `catalog_rhel.json` during setup. Store a selected scenario under
  its own filename, as shown in the procedure, and keep `CATALOG_FILE_PATH`
  pointed to that file.
