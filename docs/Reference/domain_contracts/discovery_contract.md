# Discovery Domain Contract

**Deployment module**: Discovery | **CLI identifier**: `discovery`

## Upstream domain contract

Discovery does not require another deployment domain's status output.

## External connectivity contract

| Connection | Requirement |
|---|---|
| OIM to OME | HTTPS on TCP port 443 must be routable from the OIM to `ome_ip`. |
| OME to target BMC/iDRAC | Every target BMC/iDRAC must have working network connectivity and must already be discovered and managed by OME as a server device. |
| OIM to target BMC/iDRAC | Discovery does not use a direct connection. It reads BMC/iDRAC management and NIC inventory through OME. Other Omnia workflows can require this connectivity. |

The OME account must have administrative access or equivalent permissions to
create an API session and read devices, static groups and their members,
device-management details, and server network-interface inventory. Discovery
does not add devices to OME or configure BMC/iDRAC networking.

## Output contract

Discovery writes its customer-readable artifacts to:

```text
$OMNIA_DATA_PATH/discovery/output/$OMNIA_PROJECT_NAME/
```

| Output | Purpose |
|---|---|
| `bmc_pxe_mapping_file_<timestamp>.csv` | Timestamped mapping generated from OME inventory. |
| `bmc_pxe_mapping_file.csv` | Symbolic link to the latest timestamped mapping. |
| `bmc_discovery_report_<timestamp>.csv` | Informational server and NIC discovery report. |
| `discovery_status.yml` | Machine-readable execution result. |

### Mapping-file schema

The generated CSV uses these columns:

```text
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
```

For OME discovery, `FUNCTIONAL_GROUP_NAME` is derived from the server's
supported, case-sensitive OME static-group name. A server without a static
group uses `slurm_node_aarch64`; a server in an unsupported nonempty group is
omitted from the mapping file; and membership in multiple processed groups
causes Discovery to stop. See [Create OME static
groups](../../HowTo/discovery/discover_nodes.md#create-ome-static-groups) for
the supported names and OME procedure.

Discovery derives `GROUP_NAME` from the `SU` sequence in the OME-reported
iDRAC hostname and uses `grp0` when no recognized sequence is present. For the
recommended hostname convention and the sequence recognized by the current
mapping generator, see [Plan iDRAC
hostnames](../../HowTo/discovery/discover_nodes.md#plan-idrac-hostnames).

Discovery generates `HOSTNAME` as `nid` followed by a three-digit sequence.
The supported range is `nid000` through `nid999`, and automatic generation
normally begins with `nid001`.

Review and correct the generated values before copying the file to:

```text
$ORCHESTRATOR_DATA_PATH/input/$OMNIA_PROJECT_NAME/pxe_mapping_file.csv
```

When `ORCHESTRATOR_DATA_PATH` is unset, it defaults to
`$OMNIA_DATA_PATH/orchestrator`.

For `slurm_node_x86_64` and `slurm_node_aarch64`, Discovery may populate
optional `PARENT_SERVICE_TAG` metadata in generated rows. It otherwise leaves
the field empty. This is Discovery generation behavior, not an Orchestrator
input constraint. Orchestrator does not require a parent value or validate it
against `GROUP_NAME`; review both values before handing the mapping to
Orchestrator.

### `discovery_status.yml`

| Field | Purpose |
|---|---|
| `overall_status` | `success` or `failed`. |
| `discovery_mechanism` | Records `ome` for the current executable flow. |
| `bmc_pxe_mapping_file` | Absolute path to the timestamped mapping output. |
| `servers_discovered` | Number of servers returned by discovery. |
| `timestamp` | Execution timestamp. |
| `failed_task` | Present after a failed execution. |
| `failure_reason` | Present after a failed execution. |

The status file is written only after the OME discovery role starts. Setup,
input-validation, and credential failures can leave it absent or unchanged
from an earlier run.

## Execution contract

Run the domain from `src/main` with `./omnia.sh --run discovery`. The supported
tags are `precheck`, `validate`, `credentials`, `prepare`, `execute`,
`discovery`, `cleanup`, `cleanup_credentials`, `upgrade`, and `rollback`. Use
one tag at a time, except for the supported `cleanup,cleanup_credentials`
combination.

The operational tags are:

| Tag | Behavior |
|---|---|
| *(none)* | Runs validation, credentials, and OME execution. |
| `precheck` | Validates the resolved data path, warns if `/etc/omnia/omnia.env` is absent, and, when BMC discovery is enabled, checks TCP connectivity to the configured OME endpoint on port 443. It does not authenticate to OME or query its API. |
| `validate` | Validates the Discovery domain settings without credential prompting. |
| `credentials` | Creates or updates the encrypted OME credential file. |
| `execute` | Runs the OME discovery flow. |
| `discovery` | Alias of `execute`. |
| `cleanup` | Empties the current project's Discovery output directory and removes credentials by default. |
| `cleanup_credentials` | Removes only the Discovery credential file and Vault key. |

`prepare`, `upgrade`, and `rollback` are accepted placeholders in the current
source. They do not perform the named lifecycle operation.

Full cleanup preserves the current project output directory but removes every
entry inside it, including timestamped mappings, the latest-mapping symbolic
link, discovery reports, and the status file. It also removes
`discovery_credentials.yml` and `.discovery_credentials_key` by default. Pass
`-e cleanup_credentials=false` with the `cleanup` tag to preserve both
credential artifacts. Discovery logs and all other input files are preserved.

Copy any mapping required by Orchestrator to the Orchestrator input project
directory before cleanup. See [Clean up Discovery
data](../../HowTo/discovery/index.md#clean-up-discovery-data) for the supported
commands and warning.

## Related documentation

- [Discovery](../../HowTo/discovery/index.md)
- [Discover nodes using OME](../../HowTo/discovery/discover_nodes.md)
- [Discovery configuration](../Configuration/discovery_config.md)
- [PXE mapping file](../SampleFiles/pxe_mapping_file.md)
