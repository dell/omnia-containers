Cleanup Local Pulp Repositories
===============================

Removes unused content from the Pulp container to free up disk space. This includes RPM repositories, files (tarball, git, pip, manifest...), and container images. Active repositories and their associated content are preserved during the cleanup process.

Below are some commands that can be used to cleanup local repo artifacts:

Cleanup a specific RPM repository:

.. code-block:: bash

    ansible-playbook pulp_cleanup.yml -e cleanup_repos=x86_64_appstream

Cleanup a specific file:

.. code-block:: bash

    ansible-playbook pulp_cleanup.yml -e cleanup_files=calico-v3.30.3

Cleanup a specific container image (force cleanup):

.. code-block:: bash

    ansible-playbook pulp_cleanup.yml -e cleanup_containers=docker.io/library/busybox -e force=true

Cleanup all content:

.. code-block:: bash

    ansible-playbook pulp_cleanup.yml -e cleanup_repos=all -e cleanup_files=all -e cleanup_containers=all

.. note::
    If the deleted artifact(s) is required by any software, user must rerun ``local_repo.yml`` to sync the artifact(s) again. If the artifact(s) is not synced in local repo, subsequent playbooks having dependency may fail.

Logs
-----

Cleanup logs are generated in a version-aware directory structure under ``/opt/omnia/log/local_repo/``.

.. code-block:: text

    /opt/omnia/log/local_repo/
    └── rhel/
        ├── 10.0/cleanup/
        │   ├── standard.log
        │   └── cleanup_status.csv
        └── 10.1/cleanup/
            ├── standard.log
            └── cleanup_status.csv

* ``standard.log`` – Contains detailed execution logs of the cleanup operation.
* ``cleanup_status.csv`` – Provides a summary of cleanup actions and their status.

.. note::

    The ``force=true`` option forces the cleanup operation to proceed even if the repository or content is currently referenced by older metadata or publications. Use this option with caution, as the cleanup process permanently removes the specified content and cannot be reversed.

