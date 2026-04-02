New Features
=============

The following sections describe the new features and enhancements introduced in Omnia 2.1 releases.


BuildStream: Catalog-Driven Build Automation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia BuildStreaM provides a comprehensive automation solution for managing infrastructure build workflows. It uses a catalog-driven approach where you define your build requirements in a structured catalog file, and BuildStreaM executes automated pipelines to create and deploy images according to your specifications.

BuildStreaM addresses the key challenges in HPC cluster image management:

* Automation: Eliminates manual build and deployment processes
* Integration: Works seamlessly with existing Omnia deployments
* Traceability: Provides complete audit trails for all build operations


Support for Installation of Additional Packages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Enables the installation of additional packages on the cluster nodes, allowing to extend cluster functionality with custom software and tools.

Add and Remove Slurm Compute Nodes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Provides the ability to add and remove Slurm compute nodes from the cluster, allowing for dynamic scaling of the cluster.

Support for Apptainer
^^^^^^^^^^^^^^^^^^^^^

Run apptainer pull to store the SIF container image on the cluster's NFS-mounted shared storage. This ensures uniform access across all compute nodes, enabling them to run jobs from the same SIF file.


Telemetry Collection from OME and SFM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Enables collection of telemetry data from OpenManage Enterprise (OME) and Smart Fabric Manager (SFM), providing insights into cluster health, performance, and resource utilization.


PowerVault Storage Integration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The PowerVault integration, with a preconfigured volume, provides persistent storage for critical Slurm controller components using iSCSI block storage with multipath support. This ensures data persistence for Slurm’s StateSaveLocation and the MariaDB/MySQL database.

InfiniBand Networking Support
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Provides comprehensive support for InfiniBand (IB) networking in HPC clusters, including automatic DOCA-OFED driver installation for Mellanox InfiniBand cards, and static IP assignment for IB interfaces. InfiniBand Networking requires an InfiniBand subnet manager (SM) configured and running to manage the IB fabric.