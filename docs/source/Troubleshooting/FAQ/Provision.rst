Provision
==========


⦾ **What to do if root user login fails when accessing a cluster node?**

.. image:: ../../../images/UserLoginError.png

**Potential Cause**: 
    * SSH key on the OIM may be outdated.
    * cloud-init might not be rendered.

**Resolution**:

   * Refresh the key using ``ssh-keygen -R <hostname/server IP>``.
   * Retry login.
   * If cloud-init is not rendered, retry the cluster node reprovision.

⦾ **How is the gracefull shutdown of an Omnia cluster achieved?**

**Potential Cause**: Manage OIM reboot/shutdown scenario.

**Resolution**: In the case of a planned shutdown, ensure that the OIM is shut down after the compute nodes. When powering back up, the OIM should be powered on and OpenCHAMI is resumed before bringing up the compute nodes. In short, have the OIM as the first node up and the last node down.

For more information, `click here <https://github.com/xcat2/xcat-core/issues/7374>`_

⦾ **What to do if the Lifecycle Controller (LC) is not ready?**

**Resolution**:

* Verify that the LC is in a ready state for all servers using: ``racadm getremoteservicesstatus``
* PXE boot the target server.



