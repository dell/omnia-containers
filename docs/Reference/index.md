# Reference

The **Reference** section provides authoritative technical information for Omnia. This content is intended for targeted lookup and operational guidance rather than sequential reading. Use the search function or browse the navigation structure to quickly locate the required specification, compatibility information, or configuration detail.

## Support Matrix

Compatibility matrices covering validated hardware platforms, operating systems, software dependencies, and supported deployment topologies. These tables define the certified operating boundaries and supported configurations for Omnia environments.

- [Software Compatibility Matrix](software_compatibility_matrix.md) - Validated external software products and firmware versions for the current Omnia release

## Configuration File Reference

Comprehensive documentation for all Omnia configuration parameters, including descriptions, supported values, defaults, dependencies, and usage considerations for files located under domain-specific input directories:

```text
/opt/omnia/<domain>/input/project_default/
```

Where `<domain>` is one of: `main`, `discovery`, `repo_manager`, `image_build_manager`, `orchestrator`, `telemetry`, `utils`

## Domain Contracts

Input/output contracts for each Omnia domain, documenting the required input files, parameters, and expected outputs. These contracts define the interface between domains and ensure proper data flow during deployment.

- [Discovery Contract](domain_contracts/discovery_contract.md) - BMC discovery and PXE mapping file generation
- [Repo Manager Contract](domain_contracts/repo_manager_contract.md) - Local repository creation and package management
- [Image Build Manager Contract](domain_contracts/image_build_manager_contract.md) - Diskless OS image building
- [Orchestrator Contract](domain_contracts/orchestrator_contract.md) - Node provisioning and cluster setup
- [Telemetry Contract](domain_contracts/telemetry_contract.md) - Telemetry pipeline deployment
- [Utils Contract](domain_contracts/utils_contract.md) - Utility operations

## Sample Files

Curated and annotated examples of commonly used configuration and input files. These samples can be used as implementation references and customized to meet deployment-specific requirements.

- [catalog.json](SampleFiles/catalog_json.md) - Build Stream catalog for CI/CD-driven deployments
- [pxe_boot_inventory.csv](SampleFiles/pxe_boot_inventory.md) - PXE boot inventory for node provisioning
- [pxe_mapping_file.csv](SampleFiles/pxe_mapping_file.md) - PXE mapping file for network boot
- [slurm.conf](SampleFiles/slurm_conf.md) - Slurm job scheduler configuration
- [slurmdbd.conf](SampleFiles/slurmdbd_conf.md) - Slurm database daemon configuration
- [software_config.json](SampleFiles/software_config_json.md) - Software package configuration

## Cluster Requirements

Detailed infrastructure prerequisites for supported deployment scenarios, including minimum and recommended requirements for compute, memory, storage, networking, and firewall configuration.

## Playbook Reference

A consolidated reference of all Omnia playbooks, including their purpose, execution scope, target nodes, required inputs, dependencies, and expected outcomes.

## Telemetry Metrics Reference

Complete catalog of telemetry metrics collected and exposed by Omnia. Metrics are organized by source and component, with descriptions, units, collection intervals, and operational relevance.

## Appendices

Supplementary reference information, including naming conventions, filesystem layouts, directory structures, configuration standards, and other supporting technical specifications.


















