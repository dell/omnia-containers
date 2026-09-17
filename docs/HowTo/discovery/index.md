# Discovery

The Discovery deployment module queries Dell OpenManage Enterprise (OME) from
the Omnia Infrastructure Manager (OIM), generates server and NIC inventory,
and writes a BMC/PXE mapping for operator review. Orchestrator consumes the
reviewed mapping; it does not consume Discovery output automatically.

Administrators who do not use OME create the Orchestrator mapping directly.
Manual inventory is not a Discovery execution mechanism.

For the `discovery_config.yml` file location, parameter requirements, data
types, defaults, and an example, see the [Discovery configuration
reference](../../Reference/Configuration/discovery_config.md).

For the complete configuration, execution, and verification workflow, see
[Discover nodes using OME](discover_nodes.md).

## Domain boundary

Discovery is the optional third domain in the direct deployment sequence,
after Image Build Manager and before Orchestrator. It runs locally on the OIM
and owns only its project-scoped input, output, and credential files.

```text
Administrator                       Discovery                         Operator                         Orchestrator
--------------                      ---------                         --------                         ------------
discovery_config.yml  ----------->  OME inventory  --------------->  review generated  ------------> pxe_mapping_file.csv
network_spec.yml                    mapping/report                    mapping and copy                  PXE provisioning
OME credentials                          |
                                         +--------------------------> discovery_status.yml
```

The default domain paths are:

```text
/opt/omnia/discovery/input/project_default/
/opt/omnia/discovery/output/project_default/
```

Set `OMNIA_DATA_PATH` and `OMNIA_PROJECT_NAME` to use another data root or
project. Discovery does not build images, provision nodes, or manage the
Orchestrator input directory.

## Prerequisites

- Complete the main setup from `src/main` by running
  `./omnia.sh --setup-venv`.
- Ensure that OME is installed, powered on, and reachable from the OIM over
  HTTPS on TCP port 443.
- Configure network connectivity on every target server's BMC/iDRAC interface,
  and complete device discovery in OME. OME must manage each target as device
  type `1000` and report its service tag and management inventory.
- Review the [NIC MAC address selection
  priorities](discover_nodes.md#nic-mac-address-selection), and confirm that OME
  presents the intended admin/PXE and InfiniBand interfaces in the expected
  order and link state.
- Configure the Discovery-owned
  [`discovery_config.yml`](../../Reference/Configuration/discovery_config.md)
  and [`network_spec.yml`](../../Reference/Configuration/network_spec.md)
  files.
- Plan the iDRAC hostnames and exact, case-sensitive OME static-group names.
  See [Plan iDRAC hostnames](discover_nodes.md#plan-idrac-hostnames) and
  [Plan OME static groups](discover_nodes.md#plan-ome-static-groups).
- Make credentials for an OME administrator, or an account with equivalent
  inventory-read permissions, available through the Discovery credential
  workflow. See [Network connectivity
  requirements](discover_nodes.md#network-connectivity-requirements).

## Run Discovery

Run Discovery through the main domain CLI:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run discovery --tags validate
    ./omnia.sh --run discovery
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/discovery
    ansible-playbook playbooks/discovery.yml --tags validate
    ansible-playbook playbooks/discovery.yml
    ```

The untagged command runs setup, configuration validation, credential handling,
and OME discovery. See [Expected completion
output](discover_nodes.md#expected-completion-output) for the representative
success message and generated artifact paths. Use one tag at a time, except for
the supported `cleanup,cleanup_credentials` combination.

| Tag | Current behavior | Credentials |
|-----|------------------|-------------|
| *(none)* | Runs validation, credential handling, and OME discovery. | Created or loaded |
| `validate` | Validates `discovery_config.yml`; it does not validate `network_spec.yml`. | Skipped |
| `credentials` | Validates the configuration and creates or updates the encrypted OME credential file. | Created or updated |
| `execute` | Runs OME discovery after setup, validation, and credential handling. | Created or loaded |
| `discovery` | Alias of `execute`. | Created or loaded |
| `precheck` | Validates the resolved data path, warns if `/etc/omnia/omnia.env` is absent, and, when BMC discovery is enabled, checks the configured OME endpoint on TCP port 443. It does not authenticate to OME or query its API. | Skipped |
| `prepare` | Reserved placeholder; no Discovery preparation flow is implemented. | Do not use |
| `cleanup` | Empties the current project's Discovery output directory but preserves the directory. | Removed by default |
| `cleanup_credentials` | Removes only the Discovery credential file and Vault key. | Removed |
| `upgrade` | Reserved placeholder; no Discovery upgrade flow is implemented. | Do not use |
| `rollback` | Reserved placeholder; no Discovery rollback flow is implemented. | Do not use |

Unsupported tags and conflicting combinations fail validation. The `prepare`,
`upgrade`, and `rollback` placeholder tags are accepted by the playbook but do
not perform an operational lifecycle action in the current release.

### Clean up Discovery data

Run cleanup through the main domain CLI:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run discovery --tags cleanup
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/discovery
    ansible-playbook playbooks/discovery.yml --tags cleanup
    ```

Full cleanup removes every artifact from
`$OMNIA_DATA_PATH/discovery/output/$OMNIA_PROJECT_NAME/` and leaves the empty
output directory in place. It also removes `discovery_credentials.yml` and
`.discovery_credentials_key` by default. All other Discovery input files and
Discovery log files are preserved.

!!! warning

    Copy any mapping required by Orchestrator to the Orchestrator input project
    directory before running full Discovery cleanup.

Preserve the credential file and Vault key while removing Discovery outputs:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run discovery --tags cleanup -e cleanup_credentials=false
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/discovery
    ansible-playbook playbooks/discovery.yml --tags cleanup -e cleanup_credentials=false
    ```

Remove only the credential file and Vault key without changing Discovery
outputs:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run discovery --tags cleanup_credentials
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/discovery
    ansible-playbook playbooks/discovery.yml --tags cleanup_credentials
    ```

## Execution flow

1. Resolve the data path and project and create the project output directory.
2. Load and validate `discovery_config.yml`.
3. Create or load `discovery_credentials.yml` and its Vault key.
4. Connect to OME, collect the server and network-interface inventory, and
   evaluate OME static-group membership.
5. Generate the timestamped mapping and NIC-status report.
6. Write `discovery_status.yml` after the OME execution role starts.

## Output contract

Discovery writes the following files to
`$OMNIA_DATA_PATH/discovery/output/$OMNIA_PROJECT_NAME/`:

| Output | Purpose |
|--------|---------|
| `bmc_pxe_mapping_file_<timestamp>.csv` | Timestamped node mapping generated from OME inventory. |
| `bmc_pxe_mapping_file.csv` | Symbolic link to the latest timestamped mapping. |
| `bmc_discovery_report_<timestamp>.csv` | BMC, Ethernet, and InfiniBand NIC-status report. |
| `discovery_status.yml` | OME execution result, mapping path, discovered-server count, timestamp, and failure details when applicable. |

The BMC discovery report is a read-only, point-in-time inventory for checking
BMC details and OME-reported Ethernet and InfiniBand link states before
provisioning. Its timestamp matches the mapping created by the same Discovery
run. See [Review the BMC discovery
report](discover_nodes.md#bmc-discovery-report) for the eight report columns,
sample output, status interpretation, pre-provisioning checks, troubleshooting,
and comparison with the PXE mapping.

The mapping contains the following columns:

```text
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
```

View the latest generated mapping on the OIM:

```bash title="Run on: OIM host"
cat /opt/omnia/discovery/output/project_default/bmc_pxe_mapping_file.csv
```

Complete the [server attribute verification
checklist](discover_nodes.md#verification), including
`FUNCTIONAL_GROUP_NAME`, `ADMIN_MAC`, `BMC_IP`, and `HOSTNAME`, before copying
the stable mapping to the Orchestrator-owned input path:

```bash title="Run on: OIM host"
source /etc/profile.d/omnia-env.sh
discovery_path="${OMNIA_DATA_PATH}/discovery"
orchestrator_path="${ORCHESTRATOR_DATA_PATH:-${OMNIA_DATA_PATH}/orchestrator}"
cp "${discovery_path}/output/${OMNIA_PROJECT_NAME}/bmc_pxe_mapping_file.csv" \
  "${orchestrator_path}/input/${OMNIA_PROJECT_NAME}/pxe_mapping_file.csv"
```

See the [Discovery contract](../../Reference/domain_contracts/discovery_contract.md)
for the complete input and output contract.

## Related guides

- [Discover nodes using OME](discover_nodes.md)
- [Understand NIC MAC address selection](discover_nodes.md#nic-mac-address-selection)
- [Review the BMC discovery report](discover_nodes.md#bmc-discovery-report)
- [Verify the generated mapping](discover_nodes.md#verification)
- [Create a mapping file](create_mapping_file.md)
- [Provision nodes](../orchestrator/provision_nodes.md)
- [Troubleshoot OME connectivity](discover_nodes.md#ome-is-unreachable)
- [Troubleshoot Ethernet NIC selection](discover_nodes.md#the-admin-mac-address-is-unexpected-or-empty)
- [Troubleshoot iDRAC hostnames and group values](discover_nodes.md#group-names-or-parent-service-tags-are-incorrect)
- [Additional Discovery issues](../../Troubleshooting/discovery/discovery.md)
