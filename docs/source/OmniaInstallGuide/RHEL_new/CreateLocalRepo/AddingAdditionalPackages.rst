.. _adding_additional_packages:
Add Additional Packages
==========================

This section explains how to download and deploy additional software packages and container images on the cluster nodes using Omnia local repositories.

Prerequisites
-------------

Configure additional container Images from User Registry to Local Repository. Omnia supports configuring additional container images from specified user registries to Omnia Local Repository, so that these images are available and can be pulled by Service Kubernetes Cluster nodes as per requirement. User registries may be hosted either on OIM or on an external server, and both HTTP and HTTPS registries are supported.

* To view the steps to set up an **HTTP** user registry, see `Set Up an HTTP User Registry <SetUpHTTPUserRegistry.html>`_.

* To view the steps to set up an **HTTPS** user registry, see `Set Up an HTTPS User Registry <SetUpHTTPS_UserRegistry.html>`_.

After the registry is ready, mention the inputs in ``local_repo_config.yml``, see `Input Parameters for Local Repositories <InputParameters.html>`_.

Steps
-----
To add additional packages, follow these steps:

1. Open ``/opt/omnia/input/project_default/software_config.json``.

    .. csv-table:: Parameters for Software Configuration
        :file: ../../../Tables/software_config_rhel.csv
        :header-rows: 1
        :keepspace:
        :widths: auto

2. Under ``softwares``, add the ``additional_packages`` entry. 

    .. note:: Ensure the architecture list matches your cluster: ::
        
        {"name": "additional_packages", "arch": ["x86_64","aarch64"]}

The following is a sample ``software_config.json`` snippet with ``additional_packages`` enabled: ::

            {
            "cluster_os_type": "rhel",
            "cluster_os_version": "10.0",
            "repo_config": "always",
            "softwares": [
                {"name": "default_packages", "arch": ["x86_64","aarch64"]},
                {"name": "additional_packages", "arch": ["x86_64","aarch64"]}
            ],
            "additional_packages": [
                {"name": "slurm_control_node"},
                {"name": "slurm_node"},
                {"name": "login_node"},
                {"name": "login_compiler_node"},
                {"name": "service_kube_control_plane"},
                {"name": "service_kube_node"},
                {"name": "os"}
            ]
            }

3. Save the ``software_config.json`` file.

4. Update the ``additional_packages.json`` file available at ``/opt/omnia/input/project_default/config/<architecture>/rhel/10.0/`` with the required packages/images.

.. note:: All container images specified in ``additional_packages.json`` under any given subgroup are configured in Omnia local repository and can be pulled on all Service Kubernetes Cluster nodes.


.. csv-table:: Additional software packages
   :file: ../../../Tables/additional_software_packages.csv
   :header-rows: 1
   :keepspace:
   :widths: auto


The following is a sample ``additional_packages.json`` file: ::

        {
        "additional_packages": {
            "cluster": [
            { "package": "fuse-overlayfs", "type": "rpm", "repo_name": "appstream" },
            { "package": "python3-PyMySQL", "type": "rpm", "repo_name": "appstream" },
            { "package": "sssd", "type": "rpm", "repo_name": "x86_64_baseos" },
            { "package": "oddjob-mkhomedir", "type": "rpm", "repo_name": "appstream" },
            { "package": "quay.io/strimzi/kafka-bridge", "type": "image", "tag": "0.33.1" },
            { "package": "registry.k8s.io/pause", "type": "image", "digest": "sha256:7031c1b283388c2c47cc389c74e7a6a1f91e3c23f7f9c2d9e25f7c8b1a2d3e4f" },
            { "package": "172.16.0.254:7000/ubuntu/squid", "type": "image", "tag": "latest" }
            ]
        },
        "os": {
            "cluster": [
            { "package": "podman", "type": "rpm", "repo_name": "appstream" },
            { "package": "curl", "type": "rpm", "repo_name": "x86_64_baseos" },
            { "package": "wget", "type": "rpm", "repo_name": "appstream" },
            { "package": "podman", "type": "rpm", "repo_name": "appstream" },
            { "package": "curl", "type": "rpm", "repo_name": "arm64_baseos" },
            { "package": "wget", "type": "rpm", "repo_name": "appstream" }
            ]
        }
        }

2. Ensure you provide the correct package type (``rpm`` or ``image``) and the repository name/tag/digest, based on your requirement.
3. Save the ``additional_packages.json`` file.


Guidelines for Configuring Additional Packages for Specific Architectures
-------------------------------------------------------------------------

.. note:: The ``additional_packages`` feature has architecture-specific functional group support. Users must configure both ``software_config.json`` and the architecture-specific ``additional_packages.json`` files according to the supported groups for their target architecture.

**Supported Functional Groups by Architecture:**

- **x86_64**: ``slurm_control_node``, ``slurm_node``, ``login_node``, ``login_compiler_node``, ``service_kube_control_plane``, ``service_kube_control_plane_first``, ``service_kube_node``, ``os``
- **aarch64**: ``slurm_node``, ``login_node``, ``login_compiler_node``, ``os``

**Configuration Steps:**

1. **Edit ``software_config.json``**: Define the ``additional_packages`` entry with the desired functional groups and specify the appropriate architecture(s) in the ``arch`` field.

2. **Edit architecture-specific JSON files**: Update the corresponding architecture-specific JSON files located at:

   - ``/opt/omnia/input/<project_name>/config/x86_64/rhel/<version>/additional_packages.json``
   - ``/opt/omnia/input/<project_name>/config/aarch64/rhel/<version>/additional_packages.json``

   Ensure these files contain only the functional groups that are supported for that architecture.

.. important::

- Kubernetes-related functional groups (``service_kube_*``) and ``slurm_control_node`` are **only supported on x86_64** architecture.
- The architecture-specific ``additional_packages.json`` files must include an ``additional_packages`` parent key and contain only supported functional groups for that architecture.
- Declare only supported functional groups for each architecture in both ``software_config.json`` and the architecture-specific JSON files.
- Validation logs warnings (not errors) for unsupported groups and continues execution.
- Review validation logs at ``/opt/omnia/log/core/playbooks/validation_omnia_<project_name>.log`` for configuration warnings.
