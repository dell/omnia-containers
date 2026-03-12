Local Repositories
===================

⦾ **Why does running** ``local_repo.yml`` **fail with connectivity errors?**

**Potential Cause**: The OIM was unable to reach a required online resource due to a network glitch.

**Resolution**: Verify all connectivity and re-run the playbook.


⦾ **Why does any script that installs software fail with** ``The checksum for <software repository path> did not match.`` **error?**

**Potential Cause**: A local repository for the software has not been configured by the ``local_repo.yml`` playbook.

**Resolution**: Follow the steps below to resolve this issue:

    1. Re-run the ``local_repo.yml`` playbook with proper inputs to download the software package to the Pulp repository.
    2. Once the local repository has been configured successfully, re-run the failed installation script.


⦾ **The**  ``local_repo.yml`` **playbook execution fails if the Epel repository is unstable.**

**Potential Cause**: If the external Epel repository link mentioned in ``omnia_repo_url_rhel`` is not stable, then it can cause failures in ``local_repo.yml`` playbook execution.

**Resolution**:

1. Check if the Epel repository link mentioned in ``omnia_repo_url_rhel`` is accessible.

2. Verify the required software listed in ``software_config.json``, by examining the corresponding ``<software>.json`` files located in the ``input/config/rhel/`` directory. Users can do either of the following, based on the findings:

    - If none of the packages are dependent on the Epel repository, users can remove the Epel repository URL from ``omnia_repo_url_rhel``.

    - If any package required from the Epel repository is listed in the ``software_config.json`` file, it's advisable to either wait for the Epel repository to stabilize or host those Epel repository packages locally. Afterward, remove the Epel repository link from ``omnia_repo_url_rhel`` and provide the locally hosted URL for the Epel repository packages via the ``user_repo_url`` variable.


⦾ **The** ``local_repo.yml`` **playbook fails at** ``TASK: [parse_and_download : Process URL mirrors from local_repo_config]`` **if it is run multiple times.**

**Potential cause**: This occurs due to resource saturation on the Pulp container.

**Resolution**: If you are running ``local_repo.yml`` playbook multiple times and encounter a failure at the task ``Process URL mirrors from local_repo_config``, it is recommended to let the system remain idle for approximately one hour before re-running the ``local_repo.yml`` playbook.


⦾ **The** ``local_repo.yml`` **playbook passes even when an incorrect GPG key is provided during repository configuration.**

**Potential cause**: GPG key validation is currently not enforced during Pulp remote creation. Although ``localrepo`` includes support for GPG keys, this functionality is not yet enabled in Pulp.

**Resolution**: This is a known limitation. Once GPG key support is enabled in Pulp, ``localrepo`` will be able to utilize this feature for proper validation. The issue has been raised with the Pulp team for tracking:
`https://github.com/pulp/pulp_rpm/issues/4241 <https://github.com/pulp/pulp_rpm/issues/4241>`_