Local Repository
===================

⦾ **Why does the** ``local_repo.yml`` **playbook execution fail at** ``TASK [parse_and_download : Display Failed Packages]`` **?**

.. image:: ../../../images/package_failure_local_repo.png

**Potential Cause**: This issue is encountered if Omnia fails to download any software package while executing ``local_repo.yml`` playbook. Download failures can occur if:

    * The URL to download the software packages mentioned in the ``<cluster_os_type>/<cluster_os_version>/<software>.json`` is incorrect or the repository is unreachable.
    * The provided Docker credentials are incorrect or if you encounter a Docker pull limit issue. For more information, `click here <https://www.docker.com/increase-rate-limits/#:~:text=You%20have%20reached%20your%20pull%20rate%20limit.%20You,account%20to%20a%20Docker%20Pro%20or%20Team%20subscription.>`_.
    * If disk space is insufficient while downloading the package.

**Resolution**: Re-run the ``local_repo.yml`` playbook while ensuring the following:

    * URL to download the software packages mentioned in ``<arch>/<cluster_os_type>/<cluster_os_version>/<software>.json`` is correct, and the repository is reachable.
    * Docker credentials provided in ``input/omnia_config_credentials.yml`` are correct.
    * Sufficient disk space is available while downloading the package. For disk space considerations, see the `Omnia installation guide <../../../OmniaInstallGuide/RHEL_new/RHELSpace.html>`_.

If the ``local_repo.yml`` is executed successfully without any package download failures, a ``Successful`` message is displayed as shown below:

.. image:: ../../../images/local_repo_success.png