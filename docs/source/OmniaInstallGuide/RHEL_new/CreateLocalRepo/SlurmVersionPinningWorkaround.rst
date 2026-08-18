Slurm Version Pinning Workaround for Omnia v2.1.0.0
===================================================

**Related Documentation**

* `Prerequisites <Prerequisite.html>`_ - General prerequisites for creating local repositories
* `Input Parameters <InputParameters.html>`_ - Configuration parameters for local repositories
* `Step 11: Set up Slurm on nodes <../OmniaCluster/BuildingCluster/install_slurm.html>`_ - Slurm installation and configuration

---

**Known Issue**

EPEL repositories now ship **Slurm 26.x** packages. This conflicts with the **Slurm 25.05.2** packages expected by Omnia v2.1.0.0. Since v2.1.0.0 is a released tag with no code changes permitted, users must replace the contents of ``slurm_custom.json`` on both architecture paths **before** running `Step 9: Create Local Repositories <index.html>`_.

Failure to apply this fix may result in version mismatch and installation failures during `Step 11: Set up Slurm on nodes <../OmniaCluster/BuildingCluster/install_slurm.html>`_.

---

**Affected Files**

+----------------+-------------------------------------------------------------------------------------------------------------------+
| Architecture   | File Path                                                                                                         |
+================+===================================================================================================================+
| x86_64         | ``/opt/omnia/input/project_default/config/x86_64/rhel/10.0/slurm_custom.json``                                   |
+----------------+-------------------------------------------------------------------------------------------------------------------+
| aarch64        | ``/opt/omnia/input/project_default/config/aarch64/rhel/10.0/slurm_custom.json``                                  |
+----------------+-------------------------------------------------------------------------------------------------------------------+

---

**Required User Action (Before Step 9)**

Replace the contents of **both** files with the complete JSON provided below. No further modification is needed — simply copy and paste.

**Step 1: Update the x86_64 Configuration**

.. code-block:: bash

    vi /opt/omnia/input/project_default/config/x86_64/rhel/10.0/slurm_custom.json

Replace the entire file contents with:

.. code-block:: json

    {
        "slurm_custom": {
            "cluster": [
                {"package": "munge", "type": "rpm", "repo_name": "appstream"},
                {"package": "firewalld", "type": "rpm", "repo_name": "baseos"},
                {"package": "python3-firewall", "type": "rpm", "repo_name": "baseos"},
                {"package": "pmix", "type": "rpm", "repo_name": "appstream"},
                {"package": "nvcr.io/nvidia/hpc-benchmarks", "tag": "25.09", "type": "image"},
                {"package": "apptainer", "type": "rpm", "repo_name": "epel"},
                {"package": "doca-ofed", "type": "rpm_repo", "repo_name": "doca"},
                {"package": "iscsi-initiator-utils", "type": "rpm", "repo_name": "baseos"},
                {"package": "device-mapper-multipath", "type": "rpm", "repo_name": "baseos"},
                {"package": "sg3_utils", "type": "rpm", "repo_name": "baseos"},
                {"package": "lsscsi", "type": "rpm", "repo_name": "baseos"},
                {"package": "imb", "type": "tarball", "url": "https://github.com/intel/mpi-benchmarks/archive/refs/tags/IMB-v2021.8.tar.gz"},
                {"package": "osu-micro-benchmarks", "type": "tarball", "url": "https://mvapich.cse.ohio-state.edu/download/mvapich/osu-micro-benchmarks-7.5.tar.gz"},
                {"package": "likwid", "type": "tarball", "url": "https://github.com/RRZE-HPC/likwid/archive/refs/tags/v5.4.1.tar.gz"},
                {"package": "geopm", "type": "tarball", "url": "https://github.com/geopm/geopm/archive/refs/tags/v3.1.0.tar.gz"},
                {"package": "papi", "type": "tarball", "url": "https://github.com/icl-utk-edu/papi/releases/download/papi-7-2-0-t/papi-7.2.0.tar.gz"},
                {"package": "sionlib", "type": "tarball", "url": "https://apps.fz-juelich.de/jsc/sionlib/download.php?version=1.7.7"}
            ]
        },
        "slurm_control_node": {
            "cluster": [
                {"package": "slurm-slurmctld-25.05.2", "type": "rpm", "repo_name": "slurm_custom"},
                {"package": "slurm-slurmdbd-25.05.2", "type": "rpm", "repo_name": "slurm_custom"},
                {"package": "python3-PyMySQL", "type": "rpm", "repo_name": "appstream"},
                {"package": "mariadb-server", "type": "rpm", "repo_name": "appstream"}
            ]
        },
        "slurm_node": {
            "cluster": [
                {"package": "slurm-slurmd-25.05.2", "type": "rpm", "repo_name": "slurm_custom"},
                {"package": "slurm-pam_slurm-25.05.2", "type": "rpm", "repo_name": "slurm_custom"},
                {"package": "kernel-devel", "type": "rpm", "repo_name": "appstream"},
                {"package": "kernel-headers", "type": "rpm", "repo_name": "appstream"}
            ]
        },
        "login_node": {
            "cluster": [
                {"package": "slurm-slurmd-25.05.2", "type": "rpm", "repo_name": "slurm_custom"},
                {"package": "slurm-25.05.2", "type": "rpm", "repo_name": "slurm_custom"}
            ]
        },
        "login_compiler_node": {
            "cluster": [
                {"package": "slurm-25.05.2", "type": "rpm", "repo_name": "slurm_custom"},
                {"package": "slurm-slurmd-25.05.2", "type": "rpm", "repo_name": "slurm_custom"}
            ]
        }
    }

**Step 2: Update the aarch64 Configuration**

.. code-block:: bash

    vi /opt/omnia/input/project_default/config/aarch64/rhel/10.0/slurm_custom.json

Replace the entire file contents with:

.. code-block:: json

    {
        "slurm_custom": {
            "cluster": [
                {"package": "munge", "type": "rpm", "repo_name": "appstream"},
                {"package": "firewalld", "type": "rpm", "repo_name": "baseos"},
                {"package": "python3-firewall", "type": "rpm", "repo_name": "baseos"},
                {"package": "pmix", "type": "rpm", "repo_name": "appstream"},
                {"package": "nvcr.io/nvidia/hpc-benchmarks", "tag": "25.09", "type": "image"},
                {"package": "apptainer", "type": "rpm", "repo_name": "epel"},
                {"package": "doca-ofed", "type": "rpm_repo", "repo_name": "doca"},
                {"package": "iscsi-initiator-utils", "type": "rpm", "repo_name": "baseos"},
                {"package": "device-mapper-multipath", "type": "rpm", "repo_name": "baseos"},
                {"package": "sg3_utils", "type": "rpm", "repo_name": "baseos"},
                {"package": "lsscsi", "type": "rpm", "repo_name": "baseos"},
                {"package": "imb", "type": "tarball", "url": "https://github.com/intel/mpi-benchmarks/archive/refs/tags/IMB-v2021.8.tar.gz"},
                {"package": "osu-micro-benchmarks", "type": "tarball", "url": "https://mvapich.cse.ohio-state.edu/download/mvapich/osu-micro-benchmarks-7.5.tar.gz"},
                {"package": "likwid", "type": "tarball", "url": "https://github.com/RRZE-HPC/likwid/archive/refs/tags/v5.4.1.tar.gz"},
                {"package": "geopm", "type": "tarball", "url": "https://github.com/geopm/geopm/archive/refs/tags/v3.1.0.tar.gz"},
                {"package": "papi", "type": "tarball", "url": "https://github.com/icl-utk-edu/papi/releases/download/papi-7-2-0-t/papi-7.2.0.tar.gz"},
                {"package": "msr-safe", "type": "tarball", "url": "https://github.com/llnl/msr-safe/archive/refs/tags/v1.7.0.tar.gz"},
                {"package": "sionlib", "type": "tarball", "url": "https://apps.fz-juelich.de/jsc/sionlib/download.php?version=1.7.7"}
            ]
        },
        "slurm_control_node": {
            "cluster": [
                {"package": "slurm-slurmctld-25.05.2", "type": "rpm", "repo_name": "slurm_custom"},
                {"package": "slurm-slurmdbd-25.05.2", "type": "rpm", "repo_name": "slurm_custom"},
                {"package": "python3-PyMySQL", "type": "rpm", "repo_name": "appstream"},
                {"package": "mariadb-server", "type": "rpm", "repo_name": "appstream"}
            ]
        },
        "slurm_node": {
            "cluster": [
                {"package": "slurm-slurmd-25.05.2", "type": "rpm", "repo_name": "slurm_custom"},
                {"package": "slurm-pam_slurm-25.05.2", "type": "rpm", "repo_name": "slurm_custom"},
                {"package": "kernel-devel", "type": "rpm", "repo_name": "appstream"},
                {"package": "kernel-headers", "type": "rpm", "repo_name": "appstream"}
            ]
        },
        "login_node": {
            "cluster": [
                {"package": "slurm-slurmd-25.05.2", "type": "rpm", "repo_name": "slurm_custom"},
                {"package": "slurm-25.05.2", "type": "rpm", "repo_name": "slurm_custom"}
            ]
        },
        "login_compiler_node": {
            "cluster": [
                {"package": "slurm-25.05.2", "type": "rpm", "repo_name": "slurm_custom"},
                {"package": "slurm-slurmd-25.05.2", "type": "rpm", "repo_name": "slurm_custom"}
            ]
        }
    }

.. note:: The ``x86_64`` and ``aarch64`` files differ slightly. The ``aarch64`` version includes the ``msr-safe`` tarball package in the ``slurm_custom`` cluster section. Ensure you use the correct JSON for each path.

**Step 3: Verify Both Files**

.. code-block:: bash

    grep -c "25.05.2" /opt/omnia/input/project_default/config/x86_64/rhel/10.0/slurm_custom.json
    grep -c "25.05.2" /opt/omnia/input/project_default/config/aarch64/rhel/10.0/slurm_custom.json

**Expected output for both commands:**

.. code-block:: bash

    8

This confirms all 8 Slurm package entries across all node roles are pinned to version ``25.05.2``.

---

**Proceed With Deployment**

After applying the workaround, continue with:

**Step 9 — Create Local Repositories**

.. code-block:: bash

    cd /omnia
    ansible-playbook local_repo/local_repo.yml

**Step 11 — Set up Slurm on Nodes**

After completing the Slurm installation, verify the version on the nodes:

.. code-block:: bash

    # On the slurm_control_node
    slurmctld --version
    # Expected output: slurm 25.05.2

    # On slurm_node
    slurmd --version
    # Expected output: slurm 25.05.2

---

**References**

* `Step 9: Create Local Repositories — Dell/Omnia v2.1.0.0 <index.html>`_
* `Step 11: Set up Slurm on nodes — Dell/Omnia v2.1.0.0 <../OmniaCluster/BuildingCluster/install_slurm.html>`_
* `Input Parameters for Local Repositories <InputParameters.html>`_ - Software configuration and repository setup
* `Troubleshooting Guide — Slurm Version Mismatch <../../../../troubleshootingguide.html#slurm-version-mismatch-26-x-vs-25-05-2>`_ - Troubleshooting steps for Slurm version issues
