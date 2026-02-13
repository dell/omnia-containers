Input Parameters for Local Repositories
==========================================

The ``local_repo.yml`` playbook is dependent on the inputs provided to the following input files:

* ``/opt/omnia/input/project_default/software_config.json``
* ``/opt/omnia/input/project_default/local_repo_config.yml``
* ``/opt/omnia/input/project_default/additional_packages.json``

``/opt/omnia/input/project_default/software_config.json``
----------------------------------------------------------

Based on the inputs provided to the ``/opt/omnia/input/project_default/software_config.json``, the software packages/images are accessed from the Pulp container and the desired software stack is deployed on the cluster nodes.

.. note::
    * To download a software with both x86_64 and aarch64 architectures, the arch key input is mandatory. Ensure that you check if the .json files for all the specified architectures are available in the input or configuration file. Else, update the .json files. 
       
    * For additional_software support, update the input/config/{arch}/rhel/10.0/additional_packages.json file with the required {arch} data, where {arch} can either be x86_64 or aarch64, or a combination of both.

.. csv-table:: Parameters for Software Configuration
   :file: ../../../Tables/software_config_rhel.csv
   :header-rows: 1
   :keepspace:
   :widths: auto

The following is the sample ``software_config.json`` file:

::

    {
    "cluster_os_type": "rhel",
    "cluster_os_version": "10.0",
    "repo_config": "always",
    "softwares": [
        {"name": "default_packages", "arch": ["x86_64","aarch64"]},
        {"name": "admin_debug_packages", "arch": ["x86_64","aarch64"]},
        {"name": "openldap", "arch": ["x86_64"]},
        {"name": "nfs", "arch": ["x86_64","aarch64"]},
        {"name": "service_k8s","version": "1.31.4", "arch": ["x86_64"]},
        {"name": "slurm_custom", "arch": ["x86_64","aarch64"]},
        {"name": "additional_packages", "arch": ["x86_64","aarch64"]}
    ],
    "slurm_custom": [
        {"name": "slurm_control_node"},
        {"name": "slurm_node"},
        {"name": "login_node"},
        {"name": "login_compiler_node"}
    ],
    "service_k8s": [
        {"name": "service_kube_control_plane_first"},
        {"name": "service_kube_control_plane"},
        {"name": "service_kube_node"}
    ]
    "additional_packages": [
        {"name": "slurm_control_node"},
        {"name": "slurm_node"},
        {"name": "login_node"},
        {"name": "login_compiler_node"},
        {"name": "service_kube_control_plane_first"},
        {"name": "service_kube_control_plane"},
        {"name": "service_kube_node"}
    ]
    }

For a list of packages included in ``admin_debug_packages``, see `Default Admin Debug Packages <AdminDebugPackages.html>`_.

To deploy additional software packages on the cluster nodes, update the ``additional_packages.json`` available at ``/opt/omnia/input/project_default/``. For detailed steps on how to deploy additional packages, see `Deploy Additional Packages <../../AdvancedConfigurations/DeployAdditionalPackages.html>`_.

.. csv-table:: Additional software packages
   :file: ../../../Tables/additional_software_packages.csv
   :header-rows: 1
   :keepspace:
   :widths: auto

The following is the sample ``additional_packages.json`` file:

::

    
    {
    "additional_packages": {
        "cluster": [
        { "package": "fuse-overlayfs", "type": "rpm", "repo_name": "x86_64_appstream" },
        { "package": "python3-PyMySQL", "type": "rpm", "repo_name": "x86_64_appstream" },
        { "package": "sssd", "type": "rpm", "repo_name": "x86_64_baseos" },
        { "package": "oddjob-mkhomedir", "type": "rpm", "repo_name": "x86_64_appstream" },
        { "package": "quay.io/strimzi/kafka-bridge", "type": "image", "tag": "0.33.1" },
        { "package": "registry.k8s.io/pause", "type": "image", "digest": "sha256:7031c1b283388c2c47cc389c74e7a6a1f91e3c23f7f9c2d9e25f7c8b1a2d3e4f" }
        ]
    },
    "service_kube_control_plane": {
        "cluster": [
        { "package": "git", "type": "rpm", "repo_name": "x86_64_appstream" },
        { "package": "docker.io/curlimages/curl", "type": "image", "tag": "8.17.0" },
        { "package": "docker.io/mohr/activemq", "type": "image", "tag": "5.15.9" }
        ]
    },
    "service_kube_control_plane_first": {
        "cluster": [
        { "package": "kernel-devel", "type": "rpm", "repo_name": "x86_64_appstream" },
        { "package": "kernel-headers", "type": "rpm", "repo_name": "x86_64_appstream" }
        ]
    }
    }





.. csv-table:: Architecture information for softwares
   :file: ../../../Tables/Software_arch.csv
   :header-rows: 1
   :keepspace:
   :widths: auto



.. note::

    * For a list of accepted ``softwares``, go to the ``/opt/omnia/input/project_default/config/<cluster_os_type>/<cluster_os_version>`` and view the list of JSON files available. The filenames present in this location are the list of accepted softwares. For a cluster running RHEL 10.0, go to ``/opt/omnia/input/project_default/config/<architecture>/rhel/10.0/`` and view the file list for accepted softwares.
    * Omnia supports a single version of any software packages in the ``software_config.json`` file. Ensure that multiple versions of the same package are not mentioned.
    
``/opt/omnia/input/project_default/local_repo_config.yml``
-----------------------------------------------------------

.. csv-table:: Parameters for Local Repository Configuration
   :file: ../../../Tables/local_repo_config_rhel.csv
   :header-rows: 1
   :keepspace:
   :widths: auto

.. note::

    * For systems with RedHat subscription, subscription URLs override ``rhel_os_urls`` and are processed automatically by the ``local_repo.yml`` playbook.