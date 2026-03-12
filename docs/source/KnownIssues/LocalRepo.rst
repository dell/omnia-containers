Local Repositories
===================

⦾ **The** ``local_repo.yml`` **playbook fails at** ``TASK: [parse_and_download : Process URL mirrors from local_repo_config]`` **if it is run multiple times.**

**Potential cause**: This occurs due to resource saturation on the Pulp container.

**Resolution**: If you are running ``local_repo.yml`` playbook multiple times and encounter a failure at the task ``Process URL mirrors from local_repo_config``, it is recommended to let the system remain idle for approximately one hour before re-running the ``local_repo.yml`` playbook.


⦾ **The** ``local_repo.yml`` **playbook passes even when an incorrect GPG key is provided during repository configuration.**

**Potential cause**: GPG key validation is currently not enforced during Pulp remote creation. Although ``localrepo`` includes support for GPG keys, this functionality is not yet enabled in Pulp.

**Resolution**: This is a known limitation. Once GPG key support is enabled in Pulp, ``localrepo`` will be able to utilize this feature for proper validation. The issue has been raised with the Pulp team for tracking:
`https://github.com/pulp/pulp_rpm/issues/4241 <https://github.com/pulp/pulp_rpm/issues/4241>`_