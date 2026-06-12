Additional Cloud-Init Configuration
=====================================

Omnia allows administrators to inject custom cloud-init directives into the node provisioning pipeline. This enables boot-time customization such as writing configuration files or running setup commands on cluster nodes without modifying platform-managed templates.

Apply customizations cluster-wide to all nodes or target specific functional groups, for example, only Slurm compute nodes or only login nodes.

.. note::
   Platform-managed cloud-init settings (networking, boot commands, package installation) always take precedence. User-provided directives are **appended** to the platform defaults and do not override them.

Overview
--------

The additional cloud-init feature supports two scopes:

* **common**: Directives applied to **all** provisioned nodes.
* **groups**: Directives applied only to nodes belonging to a specific functional group as defined in the PXE mapping file.

Both scopes support the following cloud-init directives:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Directive
     - Description
   * - ``write_files``
     - Create or append files on the node at boot time. Each entry must include a ``path``.
   * - ``runcmd``
     - Run shell commands during the final stage of cloud-init. Each entry must be a string.

The following cloud-init keys are **prohibited** and cause validation to fail if available:

* ``bootcmd``
* ``network``
* ``network-config``
* ``packages``

These keys are platform-managed by Omnia and do not allow overrides.

Prerequisites
-------------

* Omnia Infrastructure Manager (OIM) is deployed and the ``omnia_core`` container is running.
* ``prepare_oim.yml`` and ``local_repo.yml`` are executed successfully.
* Cluster node images are built using the build image playbook.
* A valid PXE mapping file is configured in ``provision_config.yml``.

Configuration
-------------

Step 1: Enable additional cloud-init in provision_config.yml
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Edit the provision configuration file:

.. code-block:: bash

   /opt/omnia/input/project_default/provision_config.yml

Set the ``additional_cloud_init_config_file`` parameter to the path of your configuration file:

.. code-block:: yaml

   additional_cloud_init_config_file: "input/additional_cloud_init.yml"

To disable additional cloud-init, leave the value empty:

.. code-block:: yaml

   additional_cloud_init_config_file: ""

Step 2: Create the additional cloud-init configuration file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A sample file is provided at ``/omnia/input/additional_cloud_init.yml``. Edit this file or create a new one with the following structure:

.. code-block:: yaml

   ---
   # Common cloud-init applied to ALL nodes
   common:
     write_files:
       - path: /etc/motd
         content: "Welcome to the HPC cluster\n"
         permissions: '0644'
     runcmd:
       - echo "Custom node setup complete" >> /var/log/custom_setup.log

   # Per-functional-group cloud-init
   groups:
     slurm_node_x86_64:
       runcmd:
         - echo "Slurm compute node initialized" >> /var/log/custom.log
     login_node_x86_64:
       write_files:
         - path: /etc/profile.d/cluster.sh
           content: |
             export CLUSTER_NAME=mycluster
           permissions: '0644'

**File structure details:**

.. list-table::
   :header-rows: 1
   :widths: 15 15 70

   * - Key
     - Type
     - Description
   * - ``common``
     - Dictionary
     - Cloud-init directives applied to all provisioned nodes.
   * - ``groups``
     - Dictionary of dictionaries
     - Each key is a functional group name and must match a ``FUNCTIONAL_GROUP_NAME`` in the PXE mapping file. Each value contains the cloud-init directives for that group.

**write_files entry fields:**

.. list-table::
   :header-rows: 1
   :widths: 15 15 10 60

   * - Field
     - Type
     - Required
     - Description
   * - ``path``
     - String
     - Yes
     - Absolute path where the file is created on the node.
   * - ``content``
     - String
     - No
     - Content to write to the file.
   * - ``permissions``
     - String
     - No
     - File permissions in octal format, for example, ``'0644'``.
   * - ``owner``
     - String
     - No
     - File owner in ``user:group`` format.
   * - ``append``
     - Boolean
     - No
     - If ``true``, append content to an existing file instead of overwriting.
   * - ``encoding``
     - String
     - No
     - Content encoding, for example, ``base64``. Default is plain text.

**runcmd entries:**

Each entry in the ``runcmd`` list must be a string. Commands execute during the final stage of cloud-init, after all ``write_files`` directives are processed.

Step 3: Run the provisioning playbook
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   ssh omnia_core
   cd /omnia/provision
   ansible-playbook provision.yml

The provisioning playbook:

1. Validates the additional cloud-init configuration file (structure, allowed keys, functional group names).
2. Creates SMD groups for common and per-functional-group cloud-init.
3. Renders and registers the cloud-init configurations with the Boot Script Service (BSS).
4. When nodes PXE boot, cloud-init merges: platform defaults → common additional → per-functional-group additional.

Merge Behavior
--------------

Omnia uses the following cloud-init merge strategy:

* **Dictionaries**: ``no_replace`` — platform-defined values are not overridden by user entries.
* **Lists**: ``append`` — user entries (``write_files``, ``runcmd``) are appended to platform lists.
* **Order**: Platform defaults are applied first, then common additional cloud-init, then per-functional-group additional cloud-init.

This ensures that platform-critical configurations (networking, boot parameters) are not accidentally overridden.

Validation
----------

The following validations are performed automatically when ``provision.yml`` runs. All validation errors are reported in a single pass.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Check
     - Description
   * - File existence
     - The specified configuration file must exist.
   * - YAML syntax
     - The file must be valid YAML.
   * - Top-level keys
     - Only ``common`` and ``groups`` are allowed at the top level.
   * - Prohibited keys
     - ``bootcmd``, ``network``, ``network-config``, and ``packages`` are not allowed in any section.
   * - Allowed keys
     - Only ``write_files`` and ``runcmd`` are allowed within each section.
   * - write_files path
     - Every ``write_files`` entry must include a ``path`` field.
   * - runcmd type
     - Every ``runcmd`` entry must be a string.
   * - Functional group names
     - Group names under ``groups`` must match a ``FUNCTIONAL_GROUP_NAME`` in the PXE mapping file.

Examples
--------

Example 1: Common configuration only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apply an MOTD banner and a setup script to all nodes:

.. code-block:: yaml

   common:
     write_files:
       - path: /etc/motd
         content: |
           ========================================
           Dell HPC Cluster - Authorized Users Only
           ========================================
         permissions: '0644'
     runcmd:
       - echo "Node provisioned at $(date)" >> /var/log/provision.log

   groups: {}

Example 2: Per-functional-group configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run different setup commands on Slurm compute nodes versus login nodes:

.. code-block:: yaml

   common: {}

   groups:
     slurm_node_x86_64:
       runcmd:
         - systemctl enable slurmd
         - echo "Slurm compute node ready" >> /var/log/custom.log
     login_node_x86_64:
       write_files:
         - path: /etc/profile.d/cluster_env.sh
           content: |
             export CLUSTER_NAME=myhpc
             export SCHEDULER=slurm
           permissions: '0644'
       runcmd:
         - echo "Login node ready" >> /var/log/custom.log

Example 3: Mixed common and per-group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apply a common log entry to all nodes, plus additional Slurm-specific commands:

.. code-block:: yaml

   common:
     runcmd:
       - echo "Cluster node initialized" >> /var/log/custom_setup.log

   groups:
     slurm_node_x86_64:
       runcmd:
         - echo "Slurm-specific setup complete" >> /var/log/custom_setup.log

In this case, Slurm compute nodes have both the common ``runcmd`` and the group-specific ``runcmd`` appended.

Limitations
-----------

* Customization granularity is at the functional-group level. Per-node cloud-init customization is not supported.
* Only ``write_files`` and ``runcmd`` (config and final stage directives) are supported. Early-boot keys remain platform-managed.
* If a functional group name in the ``groups`` section does not match any entry in the PXE mapping file, validation fails.
