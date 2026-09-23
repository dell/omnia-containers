# Reference

The **Reference** section provides authoritative technical information for Omnia. This content is intended for targeted lookup and operational guidance rather than sequential reading. Use the search function or browse the navigation structure to quickly locate the required specification, compatibility information, or configuration detail.

## Support Matrix

Compatibility matrices covering validated hardware platforms, operating systems, software dependencies, and supported deployment topologies. These tables define the certified operating boundaries and supported configurations for Omnia environments.

- [Software Compatibility Matrix](software_compatibility_matrix.md) - Validated external software products and firmware versions for the current Omnia release

## Configuration File Reference

Comprehensive documentation for all Omnia configuration parameters, including descriptions, supported values, defaults, dependencies, and usage considerations for files located under module-specific input directories:

```text
/opt/omnia/<domain>/input/project_default/
```

Here, `<domain>` is the internal identifier for one of these deployment
modules: `build_stream`, `discovery`, `repo_manager`, `image_build_manager`,
`orchestrator`, `telemetry`, or `utils`. Main installs the shared environment
instead of using this module input layout.

For Utils-specific configuration, see the
[OIM Log Backup Configuration](Configuration/backup_oim_logs_config.md) and
[Slurm Config Utility Configuration](Configuration/slurm_config_util_config.md).

## Module Contracts

Domain contracts document upstream domain handoffs, produced artifacts, and
runtime or lifecycle behavior. Domain-owned input configuration is documented
separately in the configuration reference and how-to guides.

- [BuildStreaM Contract](domain_contracts/build_stream_contract.md) - GitLab and BSM readiness status and pipeline interfaces
- [Discovery Contract](domain_contracts/discovery_contract.md) - BMC discovery and PXE mapping file generation
- [Repository Manager Contract](domain_contracts/repo_manager_contract.md) - Local repository creation and package management
- [Image Build Manager Contract](domain_contracts/image_build_manager_contract.md) - Diskless OS image building
- [Orchestrator Contract](domain_contracts/orchestrator_contract.md) - Node provisioning and cluster setup
- [Telemetry Contract](domain_contracts/telemetry_contract.md) - Telemetry pipeline deployment
- [Utils Contract](domain_contracts/utils_contract.md) - Utility operations

## Sample Files

Curated and annotated examples of commonly used configuration and input files. These samples can be used as implementation references and customized to meet deployment-specific requirements.

- [catalog_rhel.json](SampleFiles/catalog_json.md) - Shared software and image-content catalog
- [pxe_boot_inventory.csv](SampleFiles/pxe_boot_inventory.md) - PXE boot inventory for node provisioning
- [pxe_mapping_file.csv](SampleFiles/pxe_mapping_file.md) - PXE mapping file for network boot
- [slurm.conf](SampleFiles/slurm_conf.md) - Slurm job scheduler configuration
- [slurmdbd.conf](SampleFiles/slurmdbd_conf.md) - Slurm database daemon configuration

## Cluster Requirements

Detailed infrastructure prerequisites for supported deployment scenarios, including minimum and recommended requirements for compute, memory, storage, networking, and firewall configuration.

## Module Playbook Entry Points

The [Module Playbook Entry Points](Playbooks/playbook_reference.md) page maps each
module to its executable top-level playbook, supported customer operations, and
input/output contract. It also shows the `omnia.sh` and direct
`ansible-playbook` invocation forms.

## Telemetry Metrics Reference

Complete catalog of telemetry metrics collected and exposed by Omnia. Metrics are organized by source and component, with descriptions, units, collection intervals, and operational relevance.

## Appendices

Supplementary reference information, including naming conventions, filesystem layouts, directory structures, configuration standards, and other supporting technical specifications.










