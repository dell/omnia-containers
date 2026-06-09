Kernel Version Override Support in Omnia
==========================================

Omnia now supports a kernel version override capability, allowing you to deploy a newer, validated kernel without requiring a full base operating system upgrade. This feature helps accelerate the adoption of critical security fixes and bug patches while maintaining OS stability.

Key Capabilities
----------------

Independent Kernel Deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Deploy a newer kernel and initrd independently of the base OS version.

Preserved OS Environment
~~~~~~~~~~~~~~~~~~~~~~~~~

The root filesystem and all OS packages remain unchanged, ensuring consistency with the validated operating environment.

Pre-validated Components
~~~~~~~~~~~~~~~~~~~~~~~~~

The override kernel and initrd are validated in advance and reused during provisioning, ensuring reliability and reducing configuration complexity.

Functional Enhancements
-----------------------

Two-Phase Validation Mechanism
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ensures the specified kernel override is validated, with an automatic fallback mechanism to locate a suitable kernel if needed.

Streamlined Configuration Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Simplifies deployment by relying on pre-validated inputs, reducing manual intervention and potential errors.