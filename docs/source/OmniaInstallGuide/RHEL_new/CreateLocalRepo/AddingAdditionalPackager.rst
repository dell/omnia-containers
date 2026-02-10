Add Additional Packages
==========================

To download and deploy additional software packages and container images using Omnia local repositories, update the required Omnia input files and execute the playbooks.

Configure Additional Container Images from User Registry to Local Repository
---------------------------------------------------------------------------------

Omnia supports configuring additional container images from specified user registries to Omnia Local Repository, so that these images are available and can be pulled by cluster nodes as per requirement. User registries may be hosted either on OIM or on an external server, and both HTTP and HTTPS registries are supported.

To view the steps to set up an HTTP user registry, see `Set Up an HTTP User Registry <SetUpHTTPUserRegistry.html>`_.

To view the steps to prepare an HTTPS user registry, see `Set Up an HTTPS User Registry <SetUpHTTPS_UserRegistry.html>`_.

After the registry is ready, mention the inputs in ``local_repo_config.yml``, see `Input Parameters for Local Repositories <InputParameters.html>`_.

Proceed to provide the remaining inputs.

Update ``software_config.json``
------------------------------

.. csv-table:: Parameters for Software Configuration
   :file: ../../../Tables/software_config_rhel.csv
   :header-rows: 1
   :keepspace:
   :widths: auto

1. Open ``/opt/omnia/input/project_default/software_config.json``.
2. Under ``softwares``, add the ``additional_packages`` entry. Ensure the architecture list matches your cluster: ::

    {"name": "additional_packages", "arch": ["x86_64","aarch64"]}

3. Save the file.

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
        {"name": "service_kube_control_plane_first"},
        {"name": "service_kube_control_plane"},
        {"name": "service_kube_node"}
    ]
    }

Update ``additional_packages.json``
----------------------------------

.. csv-table:: Additional software packages
   :file: ../../../Tables/additional_software_packages.csv
   :header-rows: 1
   :keepspace:
   :widths: auto

.. note:: All container images specified in ``additional_packages.json`` under any given subgroup are configured in Omnia local repository and can be pulled on all cluster nodes (Slurm, K8s etc).

1. Update the ``additional_packages.json`` file available at ``/opt/omnia/input/project_default/`` with the required packages/images.
2. Ensure you provide the correct package type (``rpm`` or ``image``) and the repository name/tag/digest, based on your requirement.

The following is a sample ``additional_packages.json`` file: ::

    {
    "additional_packages": {
        "cluster": [
        { "package": "fuse-overlayfs", "type": "rpm", "repo_name": "x86_64_appstream" },
        { "package": "python3-PyMySQL", "type": "rpm", "repo_name": "x86_64_appstream" },
        { "package": "sssd", "type": "rpm", "repo_name": "x86_64_baseos" },
        { "package": "oddjob-mkhomedir", "type": "rpm", "repo_name": "x86_64_appstream" },
        { "package": "quay.io/strimzi/kafka-bridge", "type": "image", "tag": "0.33.1" },
        { "package": "registry.k8s.io/pause", "type": "image", "digest": "sha256:7031c1b283388c2c47cc389c74e7a6a1f91e3c23f7f9c2d9e25f7c8b1a2d3e4f" }
        { "package": "172.16.0.254:7000/ubuntu/squid", "type": "image", "tag": "latest" }
        ]
    }
    }

Download packages/images to the Pulp container
----------------------------------------------

After updating the input files, execute the ``local_repo.yml`` playbook from inside the ``omnia_core`` container to download packages and container images to the **Pulp container**: ::

    ssh omnia_core
    cd /omnia/local_repo
    ansible-playbook local_repo.yml

For more information about executing the playbook, see `Execute the Local Repo Playbook <RunningLocalRepo.html>`_.
