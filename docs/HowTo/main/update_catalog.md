# Select or update the catalog

## Overview

The catalog selects the operating-system version, node architectures,
functional layers, software groups, packages, and artifact sources used by
Repository Manager, Image Build Manager, and Orchestrator.

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

!!! warning

    Bundled catalog availability is not a product-support statement. For Omnia
    2.3.0.0-rc1, the documented validated combination is a RHEL 10.0 OIM with
    RHEL 10.0 cluster nodes. The bundled RHEL 10.2 cluster-node catalogs do not
    have a published Supported, Validated, Technology preview, or Not supported
    classification. Until Engineering publishes that classification, use the
    RHEL 10.0 catalogs for deployments that must remain within the documented
    validated baseline. See the
    [Operating Systems Matrix](../../Reference/SupportMatrix/operating_systems.md).

During `./omnia.sh --setup-venv`, Main installs the bundled default at
`CATALOG_FILE_PATH` only when that target does not already exist. Setup never
replaces an active catalog. Use the catalog selector to intentionally activate
another bundled catalog.

## Prerequisites

- Complete [Set up the OIM](setup_oim.md).
- Determine the approved RHEL version, node architecture, workload, and
  whether the deployment requires the VAST software group. Confirm the
  OIM/cluster-node combination in the
  [Operating Systems Matrix](../../Reference/SupportMatrix/operating_systems.md).
- Ensure the functional layers in the selected catalog match the functional
  groups that will be built and provisioned.
- Use an account that can write to the directory containing
  `CATALOG_FILE_PATH`.

## Procedure

1. Change to the Main source directory:

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ```

2. List the bundled catalogs:

    ```bash title="Run on: OIM host"
    ./omnia.sh --list-catalogs
    ```

    The command displays a stable selector, embedded catalog name and
    description, source path, and a content-derived summary of the RHEL
    version, workloads, architectures, VAST client inclusion, and functional
    layers.

    Choose the catalog that matches the approved target RHEL version and
    deployment. The same catalog filenames are present under the `10.0` and
    `10.2` directories, but this source-tree symmetry does not give the two
    versions the same product-support status. Use a `10.0` selector for the
    documented validated RC1 baseline.

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

3. Activate the catalog interactively or provide the exact selector printed by
   `--list-catalogs`:

    ```bash title="Run on: OIM host"
    ./omnia.sh --select-catalog
    ```

    For a non-interactive exact selection, pass the selector:

    ```bash title="Run on: OIM host"
    ./omnia.sh --select-catalog 10.0/slurm_x86_64_no_vast.json
    ```

    The interactive flow also accepts the displayed list number. Prefer the
    exact selector in scripts because list positions can change when bundled
    catalogs are added.

    The command loads the installed Omnia environment, validates the selected
    JSON, and copies it atomically to the existing `CATALOG_FILE_PATH`. If that
    target already contains different content, the command requests
    confirmation and creates a timestamped `.backup.<UTC-timestamp>` file
    before replacing it. If the selected catalog is already active, the
    command makes no change.

    `CATALOG_FILE_PATH` must be an absolute path ending in `.json`. Its default
    is `$OMNIA_DATA_PATH/catalog/catalog_rhel.json`; selecting a bundled catalog
    changes the content at that path, not the configured path itself.

## Controlled fallback for a custom catalog

`--select-catalog` discovers only the catalogs bundled under
`src/main/samples`. Use this fallback only for an approved custom catalog that
is not part of the source checkout.

1. Load the installed environment and define the custom source:

    ```bash title="Run on: OIM host"
    set -a
    source /etc/omnia/omnia.env
    set +a
    catalog_source=/absolute/path/to/approved-custom-catalog.json
    catalog_target="$CATALOG_FILE_PATH"
    ```

2. Validate the source and target paths:

    ```bash title="Run on: OIM host"
    test -f "$catalog_source"
    test "${catalog_source##*.}" = json
    test "${catalog_target#/}" != "$catalog_target"
    test "${catalog_target##*.}" = json
    test ! -L "$catalog_target"
    if [ -e "$catalog_target" ]; then test -f "$catalog_target"; fi
    python3 -m json.tool "$catalog_source" >/dev/null
    ```

3. Preserve the active catalog, install the replacement through a temporary
   file, and then rename it atomically:

    ```bash title="Run on: OIM host"
    catalog_dir=$(dirname "$catalog_target")
    mkdir -p "$catalog_dir"
    if [ -f "$catalog_target" ]; then
      cp -p -- "$catalog_target" \
        "${catalog_target}.backup.$(date -u +%Y%m%dT%H%M%SZ)"
    fi
    catalog_tmp=$(mktemp "${catalog_dir}/.omnia-catalog.XXXXXX")
    install -m 0644 "$catalog_source" "$catalog_tmp"
    mv -f -- "$catalog_tmp" "$catalog_target"
    ```

    Do not replace a symbolic link or a non-regular catalog target. Add a custom
    catalog to the reviewed source bundle when it must be selected repeatedly.

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

3. Run Repository Manager precheck to validate the environment, catalog, and Repo
   Manager inputs:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run repo_manager --tags precheck
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
        ansible-playbook repo_manager.yml --tags precheck
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

- **`CATALOG_FILE_PATH` is empty**: The selector uses
  `$OMNIA_DATA_PATH/catalog/catalog_rhel.json` as the default. Set an absolute
  `.json` path in `/etc/omnia/omnia.env` only when the active catalog must live
  elsewhere, then rerun the command.
- **The selector is unknown or ambiguous**: Run `./omnia.sh --list-catalogs`
  and copy the complete selector, including its RHEL-version directory.
- **The catalog path is rejected**: Use an absolute path whose name ends in
  `.json`. If the target exists, it must be a regular file and not a symbolic
  link. Do not specify the catalog directory.
- **The catalog file is not valid JSON**: Correct the reported JSON syntax or
  recopy the unmodified source sample.
- **The expected functional group is not built**: Confirm that the selected
  catalog contains the matching functional layer and architecture. Choose a
  combined catalog when both Slurm and service Kubernetes layers are required.
- **VAST content is included unexpectedly**: Activate the corresponding
  `_no_vast.json` selector.
- **A later setup does not restore the default catalog**: This is expected.
  Setup preserves an existing active catalog. Use `--select-catalog default`
  to intentionally reactivate the bundled default.
