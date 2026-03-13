Centralized Authentication
=============================

⦾ **Why am I unable to login using LDAP credentials after successfully creating a user account?**

**Potential Cause**: Whitespaces in the LDIF file may have caused an encryption error. Verify whether there are any whitespaces in the file by running ``cat -vet <filename>``.

**Resolution**: Remove the whitespaces and re-run the LDIF file.

⦾ **What to do if OpenLDAP user login fails when accessing a cluster node?**

.. image:: ../../../images/UserLoginError.png

**Potential Cause**: 
    * SSH key on the OIM may be outdated.
    

**Resolution**:

   * Refresh the key using ``ssh-keygen -R <hostname/server IP>``.
   * Retry login.