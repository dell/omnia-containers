Limitations
===========

General Limitations
-------------------

- Omnia supports only diskless provisioning of servers.
- Omnia supports node discovery only through the mapping file.
- Dell Technologies provides support only for Dell-developed Omnia components. Third-party software deployed by Omnia is not covered under Dell support.
- Containerized benchmark jobs are not supported on Slurm clusters.
- All iDRACs must be configured with the same username and password.

InfiniBand Restrictions
^^^^^^^^^^^^^^^^^^^^^^^

As described in the Red Hat documentation for InfiniBand and RDMA networking, Mellanox ConnectX-4 and newer adapters running RHEL 8 or later use Enhanced IPoIB mode by default. Enhanced IPoIB supports only datagram mode; connected mode is not supported.

Local Repository GPG Validation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``local_repo.yml`` playbook completes successfully even when an invalid GPG key is provided during repository configuration. GPG key validation is currently not enforced during Pulp remote creation. Although local repositories support GPG keys, this functionality is not yet enabled in Pulp.

For tracking, see:

https://github.com/pulp/pulp_rpm/issues/4241

BuildStream Limitations
^^^^^^^^^^^^^^^^^^^^^^^

- BuildStream does not support customization of ``catalog_rhel.json``.
- BuildStream does not support installation of additional packages through the catalog.
- BuildStream does not support automatic retry of failed pipeline jobs.

GPU Software Deployment Limitations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- DCGM and CUDA Toolkit are deployed only on Slurm compute nodes where NVIDIA GPUs are detected during provisioning.
- Nodes provisioned without GPUs will not have DCGM or CUDA configured and cannot be converted into GPU-enabled nodes without reprovisioning.
- DCGM installation depends on successful detection of the CUDA major version from an initialized NVIDIA driver. If driver initialization is incomplete during provisioning, DCGM deployment is deferred and must be completed manually as described in the *Manual Recovery* section.

Upgrade and Rollback Limitations
--------------------------------

- Omnia supports in-place upgrades only from **v2.1.0.0** to **v2.2.0.0**. Direct upgrades that skip releases (for example, **v2.0.0.0** to **v2.2.0.0**) are not supported. Upgrade one version at a time.
- Rollback is intended for recovery from failed or partially completed upgrades. Rolling back a successfully completed upgrade is not recommended and is blocked by default. It can be forced using:

::

   -e force_rollback=true

  However, consistency across all components cannot be guaranteed.

- New VAST storage mounts added after an upgrade are not retained during rollback.
- Slurm and Kubernetes upgrade or rollback operations reboot all affected nodes simultaneously, resulting in temporary cluster downtime. Schedule these operations during a maintenance window.

BuildStream Upgrade Restrictions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When BuildStream is enabled during an upgrade:

- Kubernetes, Slurm, Telemetry, and related components are redeployed as new clusters through the GitLab CI/CD pipeline.
- Existing cluster state, jobs, and custom configurations are not preserved.
- The GitLab pipeline must be triggered manually after the upgrade.
- BuildStream is intended primarily for test-bed environments.

Additionally:

- Disabling BuildStream during upgrade is not supported if it was enabled in Omnia 2.1.0.0.
- Selective execution using ``--tags`` is not supported for upgrade or rollback operations. The complete playbook must be executed. On reruns, previously completed components are automatically skipped.

Telemetry and GitLab Rollback Restrictions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Telemetry data stored in VictoriaMetrics and Kafka is not preserved during rollback. Any telemetry collected after the upgrade is lost when the telemetry stack is reverted.
- GitLab project rollback requires the upgrade commit to be the latest commit in the repository. If additional commits exist after the upgrade, automatic rollback will not restore GitLab content. In such cases, manually revert GitLab repository changes before performing the rollback.

BMC Discovery Limitations
-------------------------

OS NIC MAC Address Retrieval Limitation on Belton Platforms
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Affected Configurations
~~~~~~~~~~~~~~~~~~~~~~~

This limitation applies to:

- Dell Belton platforms
- Shared LOM (LAN on Motherboard) configurations
- Mellanox ConnectX-6 and ConnectX-7 network adapters
- Systems in a bare-metal state (no operating system installed)

Issue
~~~~~

When the system is in a bare-metal state, the host operating system NIC MAC address cannot be retrieved using standard management interfaces, including:

- iDRAC GUI
- OpenManage Enterprise (OME)
- Redfish APIs
- RACADM CLI
- Lifecycle Controller inventory

.. note::

   The iDRAC MAC address remains visible and is reported correctly through iDRAC and OME. NIC devices are detected, but their host MAC address fields remain empty or unavailable.

Workarounds
~~~~~~~~~~~

To obtain the host NIC MAC address, use one of the following methods:

- Monitor DHCP or PXE boot traffic
- Check network switch MAC address tables
- Use factory-provided MAC address inventories
- Review PXE boot logs

Example
~~~~~~~~

Capture DHCP discovery traffic:

::

   tcpdump -i <interface> -nne port 67 or port 68

Sample output:

::

   DHCPDISCOVER from 3c:ec:ef:12:34:56

In this example, ``3c:ec:ef:12:34:56`` is the host operating system NIC MAC address.

Documentation Feedback
----------------------

For feedback on Omnia documentation, contact:

``omnia.readme@dell.com``
