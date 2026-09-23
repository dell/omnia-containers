# Glossary

This glossary defines terminology used by Omnia's modular deployment
architecture. A deployment module's internal domain identifier, shown in code
formatting, is also its directory name under `src/` and the value accepted by
`omnia.sh --run`.

**Ansible entry playbook**
:   The top-level playbook for a deployment module. Its source path is
    `src/<domain>/playbooks/<domain>.yml`. The playbook selects module operations
    through tags.

**BMC**
:   Baseboard Management Controller. It provides out-of-band server management
    independently of the host operating system. Dell PowerEdge servers expose
    this functionality through iDRAC.

**BSS**
:   A compatibility name retained by the `ochami bss` CLI and API namespace
    for boot-configuration operations. The current OpenCHAMI deployment runs
    `boot-service`; it does not deploy a standalone Boot Script Service.

**BuildStreaM**
:   The deployment module identified as `build_stream`. It deploys PostgreSQL, the BuildStreaM Manager
    API, a playbook-watcher service, GitLab integration, and a managed project
    runner. A change to the project catalog starts the build pipeline; a change
    to the Orchestrator PXE mapping starts the deploy pipeline. See
    [BuildStreaM](../HowTo/build_stream/index.md). In public-facing text, use
    the exact capitalization **BuildStreaM**. Use `build_stream` only for the
    internal domain identifier, source paths, commands, and configuration
    identifiers.

**BuildStreaM Manager (BSM)**
:   The FastAPI service that accepts authenticated pipeline requests, records
    jobs in PostgreSQL, and writes playbook requests for the watcher.

**Build status**
:   `build_status.yml`, the Image Build Manager output contract. It records the
    producing image engine, S3 endpoint information, and the kernel, initramfs,
    and root-image paths for built functional groups.

**Catalog**
:   A JSON document containing functional layers, groups, packages, and
    package sources. Repository Manager uses it to determine content to
    synchronize; Image Build Manager can use it to resolve packages for each
    functional-group image; Orchestrator uses its functional layers and package
    metadata to select supported features. A catalog does not define the PXE
    mapping, network configuration, or module invocation order.

**cloud-init**
:   The first-boot configuration consumed by provisioned nodes. Orchestrator
    renders common, functional-group, and per-node metadata for OpenCHAMI to
    serve.

**CoreDHCP**
:   The DHCP service deployed with OpenCHAMI for PXE provisioning. Its
    configuration is generated from the Orchestrator network specification.

**CoreDNS**
:   The DNS server used by the OpenCHAMI `coresmd` plugin. When
    `dns_enabled: true`, provisioned nodes use the OIM admin address as their
    nameserver and service Kubernetes CoreDNS forwards the Omnia cluster domain
    to it. See [Cluster DNS](cluster_dns.md). Use **CoreDNS** for the product or
    service name. Use `coredns` only when reproducing a literal Kubernetes
    resource, command, container, configuration key, or filename.

**coresmd**
:   An OpenCHAMI CoreDNS plugin that reads SMD inventory and creates DNS
    records. The supplied Corefile refreshes its SMD cache every 30 seconds and
    generates `nid` names with three digits.

**CRI-O**
:   The container runtime configured by the current Orchestrator source for
    service Kubernetes nodes. Its storage size is selected through
    `k8s_crio_storage_size`.

**Discovery**
:   The deployment module identified as `discovery`. It queries OpenManage Enterprise and writes a BMC
    discovery report and an Orchestrator-compatible PXE mapping.

**Domain**
:   An independently executable Omnia deployment unit implemented as an
    Ansible collection. Each domain has its own playbook, inputs, validation,
    dependencies, logs, and output contract. Domains exchange contract files
    instead of importing one another's source code. This meaning is distinct
    from the DNS domain configured by `SYSTEM_DOMAIN_NAME`.

**Domain identifier**
:   The internal name accepted by `omnia.sh --run` and used in source paths,
    such as `repo_manager` or `orchestrator`. This implementation term is
    retained in CLI parameters, paths, and `domain-init.sh`; the customer-facing
    architectural unit is a deployment module.

**Deployment module**
:   A capability-based unit of deployment responsibility with its own
    initialization script, dependencies, inputs, entry playbook, logs, and
    outputs. Omnia has seven modules: Repository Manager, Image Build Manager,
    Discovery, Orchestrator, Telemetry, BuildStreaM, and Utils. `main` is the
    common controller, not a deployment module.

**Module contract**
:   The documented input or output interface of a deployment module. Contracts
    include YAML configuration and status files, JSON catalogs and job data,
    CSV node mappings and reports, and deployed services or artifacts. See
    [Module Contracts](../Reference/index.md#module-contracts).

**Module initialization**
:   Execution of a module's `domain-init.sh`. It installs the module's declared
    Python and Ansible collection dependencies, creates runtime directories,
    and stages input templates unless input staging is skipped.

**Functional group**
:   A named node role selected in the catalog and PXE mapping. The mapping can
    use a Discovery-style role-and-architecture name, such as
    `slurm_node_aarch64`, or a matching catalog-qualified name, such as
    `slurm_node_rhel_10_0_aarch64`. Image Build Manager builds the corresponding
    images and Orchestrator applies the relevant boot and cluster configuration.
    An explicit OS/version segment must match the active catalog.

**iDRAC**
:   Integrated Dell Remote Access Controller. Omnia uses iDRAC through Redfish
    for supported PXE-boot, unattended installation, and hardware-management
    operations. The Telemetry module also supports iDRAC as a hardware-metrics
    source.

**Image Build Manager**
:   The deployment module identified as `image_build_manager`. It validates Repository Manager output,
    deploys the selected S3 and registry services, builds functional-group OS
    images, and writes `build_status.yml`.

**Input contract**
:   The complete set of environment variables, configuration files,
    credentials, upstream outputs, and other artifacts that a module reads.

**Kafka**
:   A Telemetry sink and message bus. LDMS writes to Kafka and the Vector-LDMS
    bridge routes that data to VictoriaMetrics. iDRAC can send to Kafka,
    VictoriaMetrics, or both, according to its configured collection targets.

**LDMS**
:   Lightweight Distributed Metric Service. The Telemetry module configures
    LDMS samplers on reachable Slurm nodes and deploys its aggregation and
    bridge workloads. LDMS requires Slurm control and compute nodes.

**main**
:   The source area containing `omnia.env`, `omnia.sh`, and catalog samples.
    It prepares the common runtime and invokes modules but is not itself a
    deployment module.

**MinIO**
:   The default S3-compatible service deployed by Image Build Manager for boot
    image storage when the selected provider is MinIO.

**OIM**
:   Omnia Infrastructure Manager. The Linux management host from which Omnia
    setup and module playbooks run. It stores the shared runtime and hosts
    module-owned management services such as Pulp, MinIO, the registry,
    OpenCHAMI, and BuildStreaM services when selected.

**OpenCHAMI**
:   The bare-metal provisioning services deployed by Orchestrator. Omnia uses
    OpenCHAMI inventory, boot-script, cloud-init metadata, DHCP, and DNS
    services to register and provision mapped nodes.

**OpenLDAP**
:   The directory service deployed by Orchestrator when selected by the
    catalog and configuration.

**OpenManage Enterprise (OME)**
:   The management system queried by the Discovery module for server and BMC
    inventory. OME can also integrate with the Telemetry module.

**Orchestrator**
:   The deployment module identified as `orchestrator`. It consumes repository, image, catalog, network,
    storage, and PXE-mapping inputs; deploys OpenCHAMI and optional OpenLDAP;
    provisions selected Slurm and service Kubernetes groups; and can initiate
    physical-node PXE boot.

**Orchestrator inventory**
:   `orchestrator_inventory.yml`, an output generated from the provisioned
    mapping. Telemetry consumes it to locate the service Kubernetes virtual IP
    and, when LDMS is enabled, Slurm nodes.

**Output contract**
:   The status files, inventories, reports, service endpoints, runtime
    resources, or other artifacts that a module produces for administrators or
    downstream modules.

**Playbook tag**
:   A named module operation selected with `--tags`, such as `validate`,
    `prepare`, `execute`, `build`, `download`, `provision`, or `collect`.
    Supported tags and default behavior are defined by each module entry
    playbook; they are not identical across every module.

**Pulp**
:   The content service deployed by Repository Manager. It stores and serves
    the catalog-selected RPM, container, Python, and file content used by later
    modules.

**PXE mapping**
:   `pxe_mapping_file.csv`, the node-to-functional-group contract consumed by
    Orchestrator. Discovery produces `bmc_pxe_mapping_file.csv`, which an
    administrator reviews and places at the Orchestrator input location, or the
    administrator supplies a mapping directly.

**Repository Manager**
:   The deployment module identified as `repo_manager`. It deploys Pulp, synchronizes catalog content,
    and writes `repo_status.yml`. In public-facing text, use the full name
    **Repository Manager**. Use `repo_manager` only for the internal domain
    identifier, source paths, commands, environment variables, and
    configuration identifiers.

**Repository status**
:   `repo_status.yml`, the Repository Manager output contract containing the
    overall synchronization state, local repository and content endpoints, and
    the Pulp server certificate path required by downstream consumers.

**SMD**
:   State Management Daemon, the OpenCHAMI inventory service used to store
    registered components, groups, and node state.

**Telemetry**
:   The deployment module identified as `telemetry`. It consumes Telemetry
    configuration, storage, package, and credential inputs together with the
    Orchestrator inventory and BMC group data; deploys the selected iDRAC,
    LDMS, OME, PowerScale, UFM, and VAST collection integrations and their
    Kafka, VictoriaMetrics, VictoriaLogs, and Vector workloads on service
    Kubernetes; and writes `telemetry_status.yml` and requested external Kafka
    and Victoria connection exports.

**Telemetry bridge**
:   A workload that transforms or routes source data to a sink. The current
    configuration includes Vector bridges for LDMS and OME data.

**Telemetry sink**
:   A destination for collected data. The current Telemetry module supports
    Kafka, VictoriaMetrics, and VictoriaLogs sink configuration.

**Telemetry source**
:   A metrics or logs producer enabled in `telemetry_config.yml`. Current
    source configuration covers iDRAC, LDMS, PowerScale, UFM, VAST, and OME;
    generated external connection information also supports integrations such
    as SFM.

**Utils**
:   The deployment module identified as `utils`. It provides operations selected with utility-specific
    tags, including `collect` for cluster log collection and `install_os` for
    unattended operating-system installation through iDRAC. The
    `backup_oim_logs` operation archives Omnia domain logs stored on the OIM to
    local or NFS storage.

**VictoriaLogs**
:   The log-storage sink deployed by Telemetry when required by enabled log
    sources.

**VictoriaMetrics**
:   The time-series metrics sink deployed by Telemetry when required by enabled
    metrics sources.
