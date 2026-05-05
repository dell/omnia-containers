
Preparing aarch64 Node
========================

To prepare aarch64 node, you need to install RHEL 10 OS.


Install RHEL 10 on aarch64 Bare-metal Node
--------------------------------------------

**Prerequisites:** Ensure that a disk is available to the aarch64 node for OS installation.

1. Manually install the **full Red Hat Enterprise Linux 10 OS** on one of the aarch64 nodes with the root password enabled.

  .. note:: 
      * The root password must be at least 8 characters long, contain alphanumeric characters, and must not include commas (,), hyphens (-), single quotes ('), double quotes ("), or backslashes (\).
      * During RHEL installation on an aarch64 node, ensure that the password set during installation is supplied as ``provision_password`` when running ``discovery.yml``.

2. Use the **host IP address** of the node in the ``admin_aarch64`` inventory file. 

   **Sample aarch64 inventory:**

   ::

      [admin_aarch64]
      <host IP address>


