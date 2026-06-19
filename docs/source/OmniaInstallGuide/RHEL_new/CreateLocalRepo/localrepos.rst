Configuring Specific Local Repositories
-----------------------------------------


**Kubernetes**

    To install Kubernetes, include the following line under ``softwares`` in ``software_config.json``: ::

            {"name": "service_k8s", "version":"1.31.4", "arch": ["x86_64"]},

    For more information about installing Kubernetes, `click here <../HighAvailability/service_cluster_k8s.html>`_.

.. note:: The version of ``service_k8s`` provided above is the only version of the package that Omnia supports.

**Slurm**

    To install Slurm, include the following line under ``softwares`` in ``software_config.json``: ::

            {"name": "slurm_custom", "arch": ["x86_64","aarch64"]},

    For more information about installing Slurm, `click here <../OmniaCluster/BuildingCluster/install_slurm.html>`_.

.. note:: If ``slurm_custom`` is defined in ``software_config.json``, provide the corresponding repository information in the ``user_repo_url_<arch>`` field of ``local_repo_config.yml``.


**OpenLDAP**

    To install OpenLDAP, include the following line under ``softwares`` in ``software_config.json``: ::

            {"name": "openldap","arch": ["x86_64"]},

    For more information on OpenLDAP, `click here <../OmniaCluster/BuildingCluster/Authentication.html#configuring-freeipa-openldap-security>`_.


**OpenMPI**

    To install OpenMPI, include the following line under ``softwares`` in ``software_config.json``: ::

            {"name": "openmpi", "version":"5.0.8","arch": ["x86_64"]},

    OpenMPI is deployed on the cluster when the above configurations are complete and `omnia.yml <../OmniaCluster/BuildingCluster/installscheduler.html>`_ playbook is executed.

    For more information on OpenMPI configurations, `click here <../../AdvancedConfigurations/install_ucx_openmpi.html>`_.

.. note:: The default OpenMPI version for Omnia is 4.1.6. If you change the version in the ``software_config.json`` file, make sure to update it in the ``openmpi.json`` file in the ``config`` directory as well.


**Unified Communication X**

    To install UCX, include the following line under ``softwares`` in ``software_config.json``: ::

            {"name": "ucx", "version":"1.19.0", "arch": ["x86_64"]},

    UCX is deployed on the cluster when ``local_repo.yml`` playbook is executed, followed by the execution of `omnia.yml <../OmniaCluster/BuildingCluster/installscheduler.html>`_.


**Dell CSI PowerScale driver**

    To install Dell CSI PowerScale driver, include the following line under ``softwares`` in ``software_config.json``: ::

            {"name": "csi_driver_powerscale", "version":"v2.17.0", "arch": ["x86_64"]},

For more information on deploying Dell CSI PowerScale driver, see `Deploy CSI drivers for Dell PowerScale Storage Solutions <../../AdvancedConfigurations/PowerScale_CSI.html>`_ 
    
