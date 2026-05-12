Log Collector
=============

Omnia provides a one-shot log collection playbook for gathering cluster logs from Kubernetes and Slurm nodes for debugging and support handoff.

**Usage**

To collect logs from the cluster, execute the following commands::

    ssh omnia_core
    cd omnia/log_collector
    ansible-playbook collect.yml

**Collection modes**

* **Full mode** (default): Collects all logs from target nodes

::

    ansible-playbook collect.yml

* **Curated support mode**: Excludes temporary and stale log files

::

    ansible-playbook collect.yml --tags curated_support

**What is collected**

* Kubernetes master nodes: Container logs, pod logs, CNI logs, runtime logs, system logs
* Kubernetes worker nodes: System logs, bootstrap logs
* Slurm controller nodes: Scheduler logs, service logs, database logs, system logs
* Slurm compute nodes: Job logs, system logs
* Login nodes: System logs, authentication logs
* Login compiler nodes: System logs, authentication logs

**Output artifacts**

* Workspace: ``/opt/omnia/logs/``
* Bundle: ``omnia-logs-<identifier>-<YYYYMMDD-HHMMSS-IST>.tar.gz``
* Metadata: ``metadata.json`` (included in bundle)
* Checksum: ``.sha256`` file for integrity verification

**Verification**

To verify the log collection output::

    # Check output
    ls -l /opt/omnia/logs/

    # Verify bundle integrity
    sha256sum omnia-logs-*.tar.gz

    # View metadata
    tar -xzf omnia-logs-*.tar.gz metadata.json
    cat metadata.json

**Prerequisites**

* PXE mapping file must exist at ``/opt/omnia/input/project_default/pxe_mapping_file.csv``
* Nodes must be reachable from OIM
* Write permissions on ``/opt/omnia/logs``
