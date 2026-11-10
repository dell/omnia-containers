# Operating Systems (OS) Matrix

!!! note
    Omnia supports the RHEL operating system with the **Server with GUI**
    Base Environment on the Omnia Infrastructure Manager (OIM) and the
    **minimal** version on cluster nodes.

## Red Hat Enterprise Linux (RHEL)

The OIM operating system and the cluster-node operating system are separate
support axes. A catalog selects the operating system used to build cluster-node
images; it does not change or qualify the operating system running on the OIM.
Support also depends on the node architecture.

### Validated RHEL versions by node architecture

| Node architecture | RHEL 10.0 | RHEL 10.2 |
|---|---|---|
| x86_64 | Validated | Validated |
| aarch64 | Validated | Not supported |

### OIM and cluster-node combinations

The OIM operating system version does not affect catalog resolution,
repository synchronization, image builds, or node provisioning. The catalog
controls which OS versions and architectures are used for cluster-node images.
RHEL 10.2 is the validated OIM platform.

| OIM OS | x86_64 cluster-node OS | aarch64 cluster-node OS | Omnia 2.3.0.0-rc3 status |
|---|---|---|---|
| RHEL 10.2 | RHEL 10.2 | RHEL 10.0 | Validated |

!!! important
    Use the same RHEL minor version for every Kubernetes control-plane and
    worker node. Do not combine different RHEL minor versions in one
    Kubernetes cluster. RHEL 10.2 is not supported on aarch64 nodes; use
    RHEL 10.0 for aarch64.

### Validated catalogs

The following catalogs have been validated for this release. If a different
catalog is selected, update the PXE mapping functional-group names to match
the selected catalog's functional layers.

| # | Catalog | Topology |
|---|---|---|
| 1 | `catalog_rhel.json` (default) | Slurm controller and login on RHEL 10.2 x86_64, Slurm compute and login-compiler on RHEL 10.0 aarch64, Kubernetes on RHEL 10.2 x86_64 |
| 2 | `hybrid/slurm_hybrid_10_2_10_0_x86_64_aarch64_no_vast.json` | Slurm controller and login on RHEL 10.2 x86_64, Slurm compute and login-compiler on RHEL 10.0 aarch64 |
| 3 | `hybrid/slurm_service_k8s_hybrid_10_2_10_0_combined_no_vast.json` | Slurm controller and login on RHEL 10.2 x86_64, Slurm compute and login-compiler on RHEL 10.0 aarch64, Kubernetes on RHEL 10.2 x86_64 |
| 4 | `rhel/10.2/slurm_x86_64_no_vast.json` | Slurm (all roles) on RHEL 10.2 x86_64 |
| 5 | `rhel/10.2/slurm_service_k8s_x86_64_no_vast.json` | Slurm (all roles) and Kubernetes on RHEL 10.2 x86_64 |
| 6 | `rhel/10.2/service_k8s_x86_64.json` | Kubernetes on RHEL 10.2 x86_64 |

Catalogs outside this list are shipped for future use but are not validated.

### Repository Support by Architecture and Node Type

| RHEL Version | Architecture | Supported Node Types | Catalog Type |
|--------------|--------------|---------------------|--------------|
| RHEL 10.2 + RHEL 10.0 | x86_64 + aarch64 | Kubernetes functional groups, Slurm controller, Slurm login (x86_64) on RHEL 10.2, Slurm compute, Slurm login/compiler (aarch64) on RHEL 10.0 | Hybrid multi-version |
| RHEL 10.2 | x86_64 | Kubernetes functional groups, Slurm controller, Slurm login, Slurm compute | Single OS version |
| RHEL 10.0 | x86_64 + aarch64 | Kubernetes functional groups, Slurm controller, Slurm login (x86_64), Slurm compute, Slurm login/compiler (aarch64) | Single OS version |
