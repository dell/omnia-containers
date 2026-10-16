# Operating Systems (OS) Matrix

!!! note
    Omnia supports the RHEL operating system with the **Server with GUI**
    Base Environment on the Omnia Infrastructure Manager (OIM) and the
    **minimal** version on cluster nodes.

## Red Hat Enterprise Linux (RHEL)

The OIM operating system and the cluster-node operating system are separate
support axes. A catalog selects the operating system used to build cluster-node
images; it does not change or qualify the operating system running on the OIM.

| OIM OS | Cluster-node OS | Omnia 2.3.0.0-rc2 status |
|---|---|---|
| RHEL 10.0 | RHEL 10.0 | Validated |
| RHEL 10.2 | RHEL 10.2 | Validated |

### Repository Support by Architecture and Node Type

| RHEL Version | Architecture | Supported Node Types | Catalog Type |
|--------------|--------------|---------------------|--------------|
| RHEL 10.2 + RHEL 10.0 | x86_64 + aarch64 | Kubernetes functional groups, Slurm controller, Slurm login (x86_64) on RHEL 10.2, Slurm compute, Slurm login/compiler (aarch64) on RHEL 10.0 | Hybrid multi-version |
| RHEL 10.0 | aarch64 | Kubernetes functional groups, Slurm controller, Slurm login (x86_64), Slurm compute, Slurm login/compiler (aarch64) | Single OS version |












