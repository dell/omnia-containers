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

| OIM OS | x86_64 cluster-node OS | aarch64 cluster-node OS | Omnia 2.3.0.0-rc3 status |
|---|---|---|---|
| RHEL 10.0 | RHEL 10.0 | RHEL 10.0 | Validated |
| RHEL 10.2 | RHEL 10.2 | RHEL 10.0 | Validated |

!!! important
    Use the same RHEL minor version for every Kubernetes control-plane and
    worker node. Do not combine different RHEL minor versions in one
    Kubernetes cluster. RHEL 10.2 is not supported on aarch64 nodes; use
    RHEL 10.0 for aarch64.

### Repository Support by Architecture and Node Type

| RHEL Version | Architecture | Supported Node Types | Catalog Type |
|--------------|--------------|---------------------|--------------|
| RHEL 10.2 + RHEL 10.0 | x86_64 + aarch64 | Kubernetes functional groups, Slurm controller, Slurm login (x86_64) on RHEL 10.2, Slurm compute, Slurm login/compiler (aarch64) on RHEL 10.0 | Hybrid multi-version |
| RHEL 10.2 | x86_64 | Kubernetes functional groups, Slurm controller, Slurm login, Slurm compute | Single OS version |
| RHEL 10.0 | x86_64 + aarch64 | Kubernetes functional groups, Slurm controller, Slurm login (x86_64), Slurm compute, Slurm login/compiler (aarch64) | Single OS version |
