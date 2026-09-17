# Collect Cluster Logs

## Overview

The Utils `collect` workflow gathers troubleshooting logs from Kubernetes,
Slurm, login, and login-compiler nodes listed in `collect_pxe.yml`. It creates
dynamic Ansible groups, fetches the configured log sources, and writes a
timestamped archive and `metadata.json` under the active Utils project output.

Missing log sources and unreachable nodes are recorded as warnings so that
collection can continue for the remaining nodes. An unreachable node also
receives an `SSH_COLLECTION_FAILED.txt` marker in the collected workspace
before the archive is created.

## Prerequisites

- Initialize the Utils module so that `collect_pxe.yml` is staged under
  `$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/`.
- Ensure the OIM can reach and authenticate to every administrative IP listed
  in `collect_pxe.yml` through SSH.
- Ensure the Utils output directory is writable and has enough space for the
  collected logs.
- Add only the functional groups supported by the source input template.

## Procedure

1. Initialize the Utils domain so that its inputs and dependencies are staged:

    ```bash title="Run from: <omnia-repository>/src/main"
    ./omnia.sh -i utils
    ```

2. Edit the staged inventory:

    ```bash title="Run on: OIM"
    vi "$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/collect_pxe.yml"
    ```

3. Add administrative IP addresses under the applicable functional groups:

    ```yaml title="collect_pxe.yml"
    service_kube_control_plane_x86_64:
      - 192.0.2.10
    service_kube_node_x86_64:
      - 192.0.2.20
    slurm_control_node_x86_64:
      - 192.0.2.30
    slurm_node_x86_64:
      - 192.0.2.40
    slurm_node_aarch64:
      - 192.0.2.41
    login_node_x86_64:
      - 192.0.2.50
    login_compiler_node_aarch64:
      - 192.0.2.60
    ```

    Remove the example addresses and enter only nodes in the active cluster.

4. Run the log-collection workflow through the OIM domain launcher:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run utils --tags collect
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/utils/playbooks
        ansible-playbook utils.yml --tags collect
        ```

The workflow collects the source-defined Kubernetes or Slurm log paths for
each node type. It combines `slurm_node_x86_64` and `slurm_node_aarch64` into
one collection group.

## Verification

The completion summary prints the archive path, metadata path, SHA-256
checksum, collection mode, and warning count. Inspect the generated files:

```bash title="Run on: OIM"
find "$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/collect" \
  -maxdepth 2 -type f \( -name 'omnia_logs_*.tar.gz' -o -name metadata.json \)
cat "$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/utils_status.yml"
```

Each run uses this layout:

```text
$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/collect/
└── omnia_logs_<timestamp>/
    ├── omnia_logs_<timestamp>.tar.gz
    └── metadata.json
```

`metadata.json` records the archive name and checksum, generation times,
triggering user, OIM operating system, collection mode, exclusions, and any
warnings.

## Next steps

- Provide the archive and its `metadata.json` to the support workflow that
  requested the diagnostic data.
- Run the collection again after correcting any unreachable-node or
  missing-source warnings.
- To clean the collection workspace, run:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run utils --tags cleanup_logs
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/utils/playbooks
        ansible-playbook utils.yml --tags cleanup_logs
        ```

    The cleanup flow searches for archives older than seven days and then
    removes every `omnia_logs_*` run directory. Because each archive and its
    metadata are stored inside a run directory, copy any files that must be
    retained before running cleanup.

## Troubleshooting

- **`collect_pxe.yml` is missing**: Run `./omnia.sh -i utils` from `src/main`
  and edit the staged file in the active project input directory.
- **A node is marked unreachable**: Verify its administrative IP and SSH
  access from the OIM. Collection continues for other nodes and records the
  failure in the archive metadata.
- **A log path is missing**: Review the warning in `metadata.json`. Missing
  source files and directories do not stop collection for other sources.
- **No archive is created**: Confirm that
  `$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/collect` is writable and
  review `/var/log/omnia/utils/utils.log`.
