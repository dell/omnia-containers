# Deploy Slurm

## Overview

Orchestrator prepares a Slurm cluster for functional groups whose names begin
with `slurm_` and includes `login_node_` and `login_compiler_node_` groups in
the same provisioning path. It registers the nodes in OpenCHAMI, generates
their boot and cloud-init data, creates shared Slurm configuration and Munge
material on the configured storage, and reconfigures a running controller when
the generated configuration changes.

The source provides cloud-init templates for an x86_64 controller, x86_64 and
aarch64 compute nodes, and x86_64 and aarch64 login and compiler-login nodes.
Slurm feature enablement is derived from the Repository Manager catalog; it is not
configured with a `deploy_slurm` boolean.

## Prerequisites

- Complete Repository Manager and Image Build Manager with Slurm content and an image
  for every Slurm and login functional group in the mapping.
- Include at least one functional group whose name starts with
  `slurm_control_node_`. Slurm provisioning stops if it cannot build a
  controller list.
- Provide reachable BMC addresses for physical-server PXE boot and reachable
  admin IPs for node registration.
- Make an NFS export available to the OIM and cluster nodes. The
  `nfs_storage_name` in `omnia_config.yml` must exactly match a mount `name` in
  `storage_config.yml`, and the NFS source must be reachable from the OIM.
- If you configure a separate `vast_storage_name`, it must also match a mount
  entry. When it is omitted, the source uses the Slurm NFS storage for the HPC
  tools path.
- If you configure VAST storage, select a with-VAST catalog that supplies the
  `vastnfs` package for every targeted architecture. The shipped default
  catalog is a no-VAST catalog.
- If the catalog enables OpenLDAP, complete its credential and deployment
  preparation before provisioning.

### Slurm storage architecture

The `nfs_storage_name` mount holds the generated Slurm directory structure,
configuration, per-node files, the Munge key, controller tracking data, and the
Pulp certificate. The optional `vast_storage_name` mount supplies the
`hpc_tools` location; when it is absent, the role reuses the NFS storage.

## Mixed RHEL 10 minor-version nodes

A Slurm cluster can contain nodes running different supported minor releases of
the same RHEL major version. For example, a controller can run RHEL 10.2 while
compute nodes run RHEL 10.0 or RHEL 10.2.

The operating-system version for each node is selected by the functional group
assigned to that node in `pxe_mapping_file.csv`. Repository Manager and Image
Build Manager must complete successfully for every functional group and
operating-system version used in the mapping.

All nodes in the cluster must use a compatible Slurm version. Omnia does not
automatically validate that user-provided Slurm packages have the same version
across operating-system repositories.

> **Important**
>
> This workflow supports different minor versions within the same supported
> RHEL major version. It does not declare support for mixing different RHEL
> major versions, such as RHEL 9 and RHEL 10, in the same Slurm cluster.

### Example PXE mapping

The following example uses a RHEL 10.2 controller, a RHEL 10.0 compute node,
and a RHEL 10.2 compute node:

```csv title="Example: pxe_mapping_file.csv"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_control_node_rhel_10_2_x86_64,controller,SLM001,,slurmcp,02:00:00:00:01:01,172.16.0.10,02:00:00:00:02:01,172.17.0.10,,
slurm_node_rhel_10_0_x86_64,compute,SLM002,,slurmnode01,02:00:00:00:01:02,172.16.0.11,02:00:00:00:02:02,172.17.0.11,,
slurm_node_rhel_10_2_x86_64,compute,SLM003,,slurmnode02,02:00:00:00:01:03,172.16.0.12,02:00:00:00:02:03,172.17.0.12,,
```

The functional-group names in this example are illustrative. Every group must
exist in the selected catalog and must have a successful image entry in
`build_status.yml`.

Changing the functional group in `pxe_mapping_file.csv` does not change an
already installed operating system. The node must be reprovisioned and PXE
booted with the newly selected image.

### Platform-specific shared storage

During provisioning, Orchestrator deploys the following platform resolver:

```text
/hpc_tools/scripts/omnia_platform.sh
```

Slurm HPC scripts use the operating system actually running on the node. They
read `ID` and `VERSION_ID` from `/etc/os-release` and detect the node
architecture at runtime.

Platform-specific content is stored under:

```text
/hpc_tools/platforms/<os>/<version>/<architecture>/
```

Example layout:

```text
/hpc_tools/platforms/
└── rhel/
    ├── 10.0/
    │   └── x86_64/
    └── 10.2/
        └── x86_64/
```

Nodes using the same operating-system version and architecture share the same
directory. Nodes using another version or architecture use a separate
directory on the same shared filesystem.

Users do not need to run the platform resolver manually during normal
operation. The benchmark, custom UCX/OpenMPI, and CUDA scripts call it
automatically.

### Verify node platform selection

Run the following on each provisioned Slurm compute, login, or login-compiler
node that mounts `/hpc_tools`.

On a controller where `/hpc_tools` is not mounted, verify the installed
operating system using `/etc/os-release` and verify its selected image through
`pxe_mapping_file.csv` and `build_status.yml`.

```bash
cat /etc/os-release

source /hpc_tools/scripts/omnia_platform.sh
omnia_detect_platform

echo "$OMNIA_OS_TYPE"
echo "$OMNIA_OS_VERSION"
echo "$OMNIA_ARCH"
echo "$OMNIA_PLATFORM_ROOT"
echo "$OMNIA_PULP_PLATFORM_PATH"
```

Example output on a RHEL 10.2 x86_64 node:

```text
rhel
10.2
x86_64
/hpc_tools/platforms/rhel/10.2/x86_64
x86_64/rhel/10.2
```

## Procedure

1. Add the Slurm nodes to `pxe_mapping_file.csv` using functional-group names
   supported by both the source templates and the active catalog. OS and
   version segments may appear before the architecture suffix.

    ```text title="pxe_mapping_file.csv — functional-group examples"
    slurm_control_node_rhel_10_0_x86_64
    slurm_node_rhel_10_0_x86_64
    slurm_node_rhel_10_0_aarch64
    login_node_rhel_10_0_x86_64
    login_node_rhel_10_0_aarch64
    login_compiler_node_rhel_10_0_x86_64
    login_compiler_node_rhel_10_0_aarch64
    ```

   The source has templates for all seven combinations shown above, but the
   shipped default RHEL 10.0 catalog supplies only the x86_64 Slurm controller
   and login roles plus the aarch64 Slurm compute and compiler-login roles.
   Select another supplied catalog when the mapping requires a different
   role-and-architecture combination.

   Retain the complete CSV row for every server, including the `SERVICE_TAG`
   column. The service-tag value may be empty; every nonempty value must be
   unique. Provide the group, hostname, admin MAC and IP, and BMC data, and
   configure the optional InfiniBand values when used.

2. Configure the first `slurm_cluster` entry in `omnia_config.yml`. The source
   reads the first cluster entry during provisioning.

    ```yaml title="omnia_config.yml"
    slurm_cluster:
      - cluster_name: slurm_cluster
        nfs_storage_name: nfs_slurm
        vast_storage_name: vast_storage
        node_discovery_mode: heterogeneous
    ```

   `node_discovery_mode` accepts the source-documented `heterogeneous` or
   `homogeneous` behavior. For homogeneous groups, optional
   `node_hardware_defaults` entries are keyed by `GROUP_NAME` and can define
   sockets, cores per socket, threads per core, real memory, and optional GRES.

   To customize Slurm configuration, add `config_sources` as mappings or
   absolute file paths. The supported configuration names are `slurm`,
   `slurmdbd`, `cgroup`, `gres`, `acct_gather`, `helpers`, `job_container`,
   `mpi`, `oci`, `topology`, and `burst_buffer`. Set `skip_merge: true` when a
   file-path configuration must replace the generated defaults. Inline
   mappings continue to merge with defaults.

3. Create matching mounts in `storage_config.yml`. This structure follows the
   staged source input; replace its addresses and exports with your environment.

    ```yaml title="storage_config.yml"
    mounts:
      - name: "nfs_slurm"
        source: "<nfs-server>:<export>"
        mount_point: "/share_omnia"
        fs_type: "nfs"
        mnt_opts: "nosuid,rw,sync,hard,intr"
        mount_on_oim: true
        functional_group_prefix: ["slurm", "login"]

      - name: "vast_storage"
        source: "<vast-server>:<export>"
        mount_point: "/mnt/vast"
        mount_params: "vast_rdma"
        mount_on_oim: true
        functional_group_prefix: ["slurm_node", "login"]
    ```

   Use the standard `name: "vast_storage"` for the optional VAST entry. Set
   `vast_storage_name: vast_storage` to enable it. If `vast_storage_name` is
   empty or omitted, Orchestrator excludes the standard `vast_storage` entry
   and reuses `nfs_storage_name`; therefore an unused VAST endpoint is not
   contacted during precheck or provisioning. When enabled, the VAST mount
   must exist and be reachable or validation fails.

4. Validate and provision. The `provision` tag processes all functional-group
   categories in the mapping, not only Slurm.

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags validate
        ./omnia.sh --run orchestrator --tags precheck
        ./omnia.sh --run orchestrator --tags prepare
        ./omnia.sh --run orchestrator --tags provision
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags validate
        ansible-playbook orchestrator.yml --tags precheck
        ansible-playbook orchestrator.yml --tags prepare
        ansible-playbook orchestrator.yml --tags provision
        ```

5. For physical nodes, PXE boot the mapped inventory after provisioning:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags pxeboot
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags pxeboot
        ```

## Verification

First confirm that Orchestrator registered all expected nodes and configured
all functional groups:

```bash title="Run on: OIM"
source /etc/profile.d/omnia-env.sh
orchestrator_path="${OMNIA_DATA_PATH}/orchestrator"
cat "$orchestrator_path/output/$OMNIA_PROJECT_NAME/provisioning_report.yml"
cat "$orchestrator_path/output/$OMNIA_PROJECT_NAME/orchestrator_status.yml"
```

After the nodes complete cloud-init, check Slurm from a controller:

```bash title="Run on: Slurm controller"
sinfo
scontrol show node <compute-hostname>
```

The generated Slurm configuration is placed beneath the selected NFS mount in
its `slurm` directory. The source runs `scontrol reconfigure` on a reachable,
running controller when controller configuration files change.

## Next steps

- Use [Add Nodes](../../Operations/add_nodes.md) to extend the mapped inventory.
- Use [Remove Slurm Nodes](../../Operations/remove_slurm_nodes.md) to remove compute nodes with the
  source's active-job protection.
- Use [Configure Slurm](configure_slurm.md) for additional
  source-backed Slurm configuration examples.

## Troubleshooting

**The controller list is empty**

Add a `slurm_control_node_...` functional group to the mapping and rerun the
workflow. The Slurm role fails deliberately when it cannot identify a
controller.

**Storage validation fails**

Confirm that every `nfs_storage_name` exactly matches a mount `name`, that its
`source` contains the `server:export` separator, and that the server is
reachable from the OIM. If directory creation fails, correct the export
permissions and rerun the playbook.

**Slurm does not pick up changed configuration**

Confirm that `slurmctld` is running on a reachable controller and run the same
check used by the source:

```bash title="Run on: Slurm controller"
scontrol reconfigure
sinfo
```

**A custom configuration fails validation**

Use only supported `config_sources` names and absolute values for path
parameters. Review the failed `slurm_conf` task in
`/var/log/omnia/orchestrator/orchestrator.log`.
