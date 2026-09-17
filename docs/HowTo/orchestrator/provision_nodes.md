# Provision Nodes

## Overview

Orchestrator provisions nodes from `pxe_mapping_file.csv`. It classifies each
functional group, registers the corresponding nodes and groups in OpenCHAMI
SMD, creates boot-service and metadata-service configuration, prepares category
bolt-ons, generates inventories, and optionally reboots physical servers
through iDRAC PXE boot.

The source recognizes these categories:

| Functional-group prefix | Provisioning path |
|---|---|
| `service_kube_` | Kubernetes |
| `slurm_` | Slurm |
| `login_node_`, `login_compiler_node_` | Slurm, including login nodes |
| `os_` | OS-only |
| Any other value | Custom |

## Prerequisites

- Complete Repo Manager and Image Build Manager successfully. Orchestrator
  requires a successful `repo_status.yml`, a valid Pulp public certificate, and
  a successful `build_status.yml` containing an image for each functional
  group.
- Provide the mapping with the exact 11 case-sensitive columns documented in
  [PXE mapping file](../../Reference/SampleFiles/pxe_mapping_file.md), including
  `IB_NIC_NAME` and `IB_IP`. Optional cells may be empty, but columns must not
  be removed.
- Use unique hostnames, normalized admin MAC addresses, and admin IPs. Every
  nonempty service tag and InfiniBand IP must also be unique. Hostnames must be
  lowercase, must not begin with a number, and must not contain underscores,
  dots, or spaces.
- Configure `network_spec.yml`. Every mapped admin IP must be valid for the
  configured network.
- For physical-server PXE boot, provide reachable Dell iDRAC addresses and BMC
  credentials. For virtual machines or environments without iDRAC, set
  `enable_pxe_boot: false`.
- Configure `omnia_config.yml`, `storage_config.yml`,
  `high_availability_config.yml`, and `security_config.yml` for the catalog
  features used by the mapped functional groups.

## Procedure

### 1. Initialize and configure the module

```bash title="Run on: OIM"
cd src/main
./omnia.sh --setup-venv
source /etc/profile.d/omnia-env.sh
orchestrator_path="${ORCHESTRATOR_DATA_PATH:-${OMNIA_DATA_PATH}/orchestrator}"
```

The input directory is
`$orchestrator_path/input/$OMNIA_PROJECT_NAME/`. In
`orchestrator_config.yml`, configure the mapping and any non-default upstream
paths:

```yaml title="orchestrator_config.yml"
pxe_mapping_file_path: "/path/to/pxe_mapping_file.csv"
image_build_manager_output_path: ""
repo_manager_output_path: ""
catalog_file_path: ""
enable_pxe_boot: true
```

Empty upstream paths use the current project defaults. For a mapping already
copied to the default project input location, leave `pxe_mapping_file_path`
empty. Set it to an absolute path only when the mapping is stored elsewhere.

### 2. Validate the inputs and prerequisites

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags validate
    ./omnia.sh --run orchestrator --tags precheck
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator
    ansible-playbook playbooks/orchestrator.yml --tags validate
    ansible-playbook playbooks/orchestrator.yml --tags precheck
    ```

### 3. Run the complete or staged workflow

For a complete run, use the playbook without tags. An untagged run executes all
phases that are not protected by the Ansible `never` tag, in playbook order:
shared setup and input validation, functional-group generation, precheck,
standalone credential collection, preparation, deployment and service
readiness, provisioning, and PXE boot when `enable_pxe_boot` is `true`.

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator
    ansible-playbook playbooks/orchestrator.yml
    ```

To control each phase, run one tag at a time after the validation and precheck
commands in step 2. Each phase requires the preceding phase to have completed;
selecting a tag does not automatically run its prerequisites:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags prepare
    ./omnia.sh --run orchestrator --tags provision
    ./omnia.sh --run orchestrator --tags pxeboot
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator
    ansible-playbook playbooks/orchestrator.yml --tags prepare
    ansible-playbook playbooks/orchestrator.yml --tags provision
    ansible-playbook playbooks/orchestrator.yml --tags pxeboot
    ```

`prepare` collects credentials, deploys OpenCHAMI and any catalog-selected
OpenLDAP service, and validates their readiness. Use `deploy` only to retry
service deployment after preparation. `provision` configures every category
present in the mapping and writes a provisioning report. It does not trigger
iDRAC. `pxeboot` sets the boot source, restarts mapped physical servers, waits
for SSH on their admin IPs, verifies that each boot occurred after the PXE
trigger, and writes the final status.

## Verification

Inspect the generated status and provisioning report:

```bash title="Run on: OIM"
cat "$orchestrator_path/output/$OMNIA_PROJECT_NAME/orchestrator_status.yml"
cat "$orchestrator_path/output/$OMNIA_PROJECT_NAME/provisioning_report.yml"
```

The provisioning validation compares expected mapping xnames with SMD,
confirms boot-service configurations for functional groups, checks
metadata-service group data and hostname assignments, and generates
`orchestrator_inventory.yaml` and `bmc_group_data.csv` in the same output
directory. Its `overall_status` is based on missing SMD nodes. Missing boot
configurations, metadata, admin interfaces, or hostname assignments are
reported in warning arrays and can therefore coexist with
`overall_status: success`.

After PXE boot, inspect the two PXE-specific artifacts as well:

```bash title="Run on: OIM"
cat "$orchestrator_path/output/$OMNIA_PROJECT_NAME/pxeboot_status.yml"
cat "$orchestrator_path/output/$OMNIA_PROJECT_NAME/failed_nodes.json"
```

`pxeboot_status.yml` contains every target node. `failed_nodes.json` is
created by the PXE phase and contains only failures; it has an empty
`failed_nodes` list on success. The aggregate `orchestrator_status.yml`
reports `overall_status`, total, success, and failure counts, plus each node's
`pxe_boot` or `node_registration` failure stage.

## Next steps

- Use [Deploy Slurm](deploy_slurm.md) or
  [Deploy Kubernetes](deploy_kubernetes.md) to verify the provisioned service.
- Use [Add Nodes](../../Operations/add_nodes.md) to provision a new subset without rebooting
  existing nodes.
- Use [Remove Slurm Nodes](../../Operations/remove_slurm_nodes.md) for source-supported Slurm compute
  node removal.

## Troubleshooting

**Input validation fails for the mapping**

Confirm the configured path, exact 11-column header, unique identifiers, valid
addresses, paired IB fields, supported functional groups, and lowercase
hostnames. Review the detailed validation log at
`$OMNIA_DATA_PATH/log/core/playbooks/orchestrator_validation_${OMNIA_PROJECT_NAME}.log`.
The surrounding Ansible execution is recorded separately in
`/var/log/omnia/orchestrator/orchestrator.log`.

**OpenCHAMI provisioning fails**

The provision phase requires the configuration created by deployment. Check the
services:

```bash title="Run on: OIM"
systemctl status openchami.target
systemctl status metadata-service
/usr/bin/ochami smd service status
```

Then retry the appropriate phases:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags deploy
    ./omnia.sh --run orchestrator --tags provision
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator
    ansible-playbook playbooks/orchestrator.yml --tags deploy
    ansible-playbook playbooks/orchestrator.yml --tags provision
    ```

**PXE boot reports no BMC hosts**

Populate the named `BMC_IP` field in every physical-node row. Ensure the OIM can
reach each iDRAC and rerun `--tags pxeboot`.

**Node registration times out**

Check admin-network TCP port 22, metadata-service, and cloud-init on the target
node. The polling window is controlled by `node_registration_pause_minutes`,
`node_registration_retries`, and `node_registration_delay` in
`set_pxe_boot_config.yml`. Failure details are written to `failed_nodes.json`.
