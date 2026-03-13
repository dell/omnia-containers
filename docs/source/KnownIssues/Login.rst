Permissions
=============

⦾ **After successful execution of the** ``omnia.sh`` **script, a message is displayed indicating that you can log in to the** ``omnia_core`` **container using** ``ssh omnia_core`` **. However, this will fail if you had initially logged in to the OIM node as a non-root user and then switched to the root user using the  ``sudo`` command.**

**Potential Cause**: SSH access to the ``omnia_core`` container depends on direct root login. When a user logs in as a non-root user and switches to root using the ``sudo`` command, the SSH session may not have the required permissions or environment configuration to access the container using ``ssh omnia_core``.

**Resolution**: To enable root-based SSH access and ensure proper functionality, perform the following steps:

1. Edit the SSH configuration file:

   Open ``/etc/ssh/sshd_config`` and set: ::

      PermitRootLogin yes

2. Restart the SSH service: ::

      systemctl restart sshd

3. Log out and re-login to the OIM node directly as the ``root`` user.

4. Restart the ``omnia_core`` container: ::

      podman restart omnia_core