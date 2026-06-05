Limitations
===========

- Omnia supports only diskless provisioning of servers.
- Omnia supports nodes discovered only through the mapping file. 
- Dell Technologies provides support only for the Dell-developed modules of Omnia. Third-party tools deployed by Omnia are not covered by Dell support.
- Containerized benchmark jobs are not supported on Slurm clusters.
- All iDRACs must use the same username and password.
- As per the RedHat documentation, `Configuring InfiniBand and RDMA networks <https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/10/html/configuring_and_managing_networking/configuring-infiniband-and-rdma-networks>`_, on RHEL 8 and later, Mellanox InfiniBand adapters starting from ConnectX-4 and newer use Enhanced IPoIB mode by default, which supports datagram mode only. Connected mode is not supported on these devices.
- The ``local_repo.yml`` playbook passes even when an incorrect GPG key is provided during repository configuration. GPG key validation is currently not enforced during Pulp remote creation. Although ``localrepo`` includes support for GPG keys, this functionality is not yet enabled in Pulp. This issue has been raised with the Pulp team for tracking: `https://github.com/pulp/pulp_rpm/issues/4241 <https://github.com/pulp/pulp_rpm/issues/4241>`_.
- BuildStream does not support customization of catalog ``catalog_rhel.json`` or additional package installations.
- BuildStream does not support retry of failed pipeline jobs.
- DCGM setup and CUDA toolkit distribution are executed only on Slurm compute nodes where NVIDIA
  GPU hardware is detected at provisioning time. Nodes provisioned without GPU hardware will not
  have DCGM or CUDA configured and cannot be brought into GPU operation without reprovisioning.
- ``nvidia-peermem`` installation requires kernel header packages to be available in the configured
  repository at provisioning time. Nodes where kernel headers are absent will skip
  ``nvidia-peermem`` installation with a non-fatal warning.
- DCGM installation depends on the CUDA major version being detectable from a running driver. On
  nodes where driver initialization has not completed at provisioning time, DCGM setup will be
  deferred and must be triggered manually as described in the Manual Recovery section.

Upgrade and Rollback Limitations
---------------------------------

- Omnia supports in-place upgrade only from version 2.1.0.0 to 2.2.0.0. Upgrades that skip
  versions (for example, 2.0.0.0 to 2.2.0.0) are not supported; upgrade one version at a time.
- Rollback is intended for recovering from a failed or partial upgrade. Rolling back a fully
  completed upgrade is blocked by default and is not recommended; it can be forced with
  ``-e force_rollback=true`` but consistency across components is not guaranteed.
- New VAST mounts will not be supported during upgrade, Any mounts added post upgrade are not retained after a rollback. 
- Slurm and Kubernetes upgrade and rollback reboot all affected nodes simultaneously, causing
  temporary cluster unavailability. Plan the operation during a maintenance window.
- When BuildStreaM is enabled during the upgrade, Kubernetes, Slurm, telemetry, and related
  downstream components are deployed as fresh clusters through the GitLab CI/CD pipeline.
  Existing cluster state, jobs, and configurations are not preserved, and the pipeline must be
  triggered manually after the upgrade. BuildStreaM is intended for test-bed clusters.
- Disabling BuildStreaM during an upgrade (when it was enabled in 2.1.0.0) is not supported.
- Selective component execution using ``--tags`` is not supported for upgrade or rollback in
  Omnia 2.2. The full upgrade or rollback playbook must be run; already-completed components
  are skipped automatically on rerun.
- Telemetry data (metrics stored in VictoriaMetrics and Kafka) is not preserved during rollback.
  Rolling back the telemetry component resets the telemetry stack to its pre-upgrade state, and
  any metrics collected after the upgrade are lost.

jo