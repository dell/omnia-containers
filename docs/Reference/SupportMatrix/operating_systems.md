# Operating Systems (OS) Matrix

!!! note
    Omnia supports the RHEL operating system with the **Server with GUI**
    Base Environment on the Omnia Infrastructure Manager (OIM) and the
    **minimal** version on cluster nodes.

## Red Hat Enterprise Linux (RHEL)

The OIM operating system and the cluster-node operating system are separate
support axes. A catalog selects the operating system used to build cluster-node
images; it does not change or qualify the operating system running on the OIM.

| OIM OS | Cluster-node OS | Omnia 2.3.0.0-rc1 status |
|---|---|---|
| RHEL 10.0 | RHEL 10.0 | Validated |

The source distribution also contains RHEL 10.2 cluster-node catalogs. Their
presence and acceptance by the catalog selector do not establish that RHEL
10.2 is supported, validated, or a technology preview on either axis. No RHEL
10.2 combination has a published product classification for this release.
Until Engineering publishes that classification, use the validated RHEL 10.0
OIM and RHEL 10.0 cluster-node combination.












