Deploy and Configure Bitnami OpenLDAP Using Podman on External Servers
======================================================================
This section describes how to deploy and configure Bitnami OpenLDAP using Podman on external servers.

Steps
------

1. Pull the Bitnami OpenLDAP Image using the following command::
    
    podman run -d --name openldap \
      -p 0.0.0.0:1389:1389 \
      -p 0.0.0.0:1636:1636 \
      -e LDAP_ADMIN_USERNAME=admin \
      -e LDAP_ADMIN_PASSWORD=Dell1234\
      -e LDAP_ROOT=dc=omnia,dc=test \
      -v openldap_data:/bitnami/openldap \
      docker.io/bitnamilegacy/openldap:latest

.. note::
        
   * In this example, the domain components used are: ``dc=omnia,dc=test``. This corresponds to the sample domain name ``omnia.test``. When following this guide, replace these values with your own domain components (for example, ``dc=example,dc=com`` or ``dc=mycompany,dc=local``).
   
   * The LDAP admin username in the examples is set as: ``LDAP_ADMIN_USERNAME=admin``. You can replace this value with any username of your choice.
   
   * The LDAP admin password in the examples is set as: ``LDAP_ADMIN_PASSWORD=Dell1234``. You can replace this value with any secure password of your choice.


The following are the parameters used in the command:

    - **-d**: Run container in detached mode.
    - **--name openldap**: Assigns a container name.
    - **-p**: Maps host ports to container ports.
    - **-e**: Sets environment variables for admin credentials and domain root.
    - **-v**: Persists data in a local volume.
    - **docker.io/bitnamilegacy/openldap:latest**: Specifies the image.

2. Check the status of the container by running the following command::

    podman ps

3. Perform the following steps to create LDIF Files. The LDIF (LDAP Data Interchange Format) files define the structure of the LDAP directory. 
   The entries in the LDIF files include organization units, users, and groups.

    a. For the organizational unit, create a file named ``ou_people.ldif`` with the following content::

            dn: ou=People,dc=omnia,dc=test
            objectClass: top
            objectClass: organizationalUnit
            ou: People
    
    This creates an organizational unit named People under the base domain.

    b. For the user entry, create a file named ``ldapuser.ldif`` with the following content::

        dn: uid=ldapuser,ou=People,dc=omnia,dc=test
        objectClass: inetOrgPerson
        objectClass: posixAccount
        objectClass: shadowAccount
        cn: ldapuser
        sn: ldapuser
        loginShell: /bin/bash
        uidNumber: 2000
        gidNumber: 2000
        homeDirectory: /home/ldapuser
        shadowLastChange: 0
        shadowMax: 0
        shadowWarning: 0

    This creates a user named ``ldapuser`` with standard POSIX attributes.

    c. For the group entry, create a file named ``ldapuser_grp.ldif`` with the following content::

        dn: cn=ldapuser,ou=groups,dc=omnia,dc=test
        objectClass: posixGroup
        cn: ldapuser
        gidNumber: 2000
        memberUid: ldapuser


    This creates a group named ``ldapuser`` and adds the user as a member.

4. Once you have created the LDIF files (ou_people.ldif, ou_groups.ldif, ldapuser.ldif, ldapuser_grp.ldif), copy them 
   into the running OpenLDAP container using the following commands::

        podman cp ou_people.ldif openldap:/
        podman cp ldapuser.ldif openldap:/
        podman cp ldapuser_grp.ldif openldap:/
        

   This command copies all LDIF files into the running OpenLDAP container under the ``/`` directory, making them accessible for LDAP operations. 

5. Execute the following commands to import the LDIF files into OpenLDAP. 

    a. First, access the container shell::

        podman exec -it openldap /bin/bash

    b. Then run the ldapadd commands from inside the container::

        ldapadd -x -H ldap://localhost:1389 -D "cn=admin,dc=omnia,dc=test" -w Dell1234 -f ou_people.ldif
        ldapadd -x -H ldap://localhost:1389 -D "cn=admin,dc=omnia,dc=test" -w Dell1234 -f ldapuser.ldif
        ldapadd -x -H ldap://localhost:1389 -D "cn=admin,dc=omnia,dc=test" -w Dell1234 -f ldapuser_grp.ldif

    The following are the parameters used in this command:

        - **-x**: Use simple authentication.
        - **-H**: LDAP server URL.
        - **-D**: Bind DN (admin distinguished name).
        - **-w**: Admin password.
        - **-f**: File to import.

    Each command loads one LDIF file into the directory.

6. Set the password for the OpenLDAP user with the following command::

    ldappasswd -x -D "cn=admin,dc=omnia,dc=test" -W -S -H ldap://localhost:1389 "uid=ldapuser,ou=People,dc=omnia,dc=test"

   The following are the parameters used in the command:

        - **-x**: Use simple authentication.
        - **-D**: Bind DN (admin distinguished name).
        - **-W**: Prompt for the admin password.
        - **-S**: Prompt for the new password to assign.
        - The user's full DN identifies which entry to modify.

7. Verify the user within the LDAP directory with the following command::

    ldapsearch -x -H ldap://localhost:1389 -D "cn=admin,dc=omnia,dc=test" -W -b "dc=omnia,dc=test"

   The following are the parameters used in the command:
        - **-b**: Search base DN.
        - **-H**: Host and port of the LDAP service.
        - This command lists all entries, including your newly created ldapuser.


Troubleshooting
----------------
If you encounter any issues, follow these steps:

1. **Check Container and Network Status**
   
   Ensure the container ports (1389 and 1636) are open and not blocked by firewalls. Check container logs with the following command::

       podman logs openldap

2. **Validate LDIF File Syntax**
   
   If you encounter schema or DN errors, validate your LDIF syntax using the following command::

       slaptest -f <ldif-file>

3. **Common Issues and Solutions:**

   - **"No such object" error**: Ensure you created the ``ou=groups`` organizational unit before adding the group entry.
   - **"File not found" error**: Verify the LDIF files are copied to the correct ``/`` directory inside the container.
   - **"Connection refused" error**: Check if the container is running and ports are properly mapped.
   - **"Invalid credentials" error**: Verify the admin password and DN format match your configuration.
