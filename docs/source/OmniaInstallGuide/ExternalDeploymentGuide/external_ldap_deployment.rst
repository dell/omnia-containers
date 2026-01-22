Deploy and Configure Bitnami OpenLDAP Using Podman on External Servers
=====================================================================
This section describes how to deploy and configure Bitnami OpenLDAP using Podman on external servers.

Step 1: Pull and Run the Bitnami OpenLDAP Image
------------------------------------------------
To pull the Bitnami OpenLDAP image, run the following command::

    podman run -d --name openldap \
    -p 0.0.0.0:1389:1389 \
    -p 0.0.0.0:1636:1636 \
    -e LDAP_ADMIN_USERNAME=admin \
    -e LDAP_ADMIN_PASSWORD=Dell1234\
    -e LDAP_ROOT=dc=omnia,dc=test \
    -v openldap_data:/bitnami/openldap \
    docker.io/bitnamilegacy/openldap:latest

The following are the parameters used in the command:

    - **-d**: Run container in detached mode.
    - **--name openldap**: Assigns a container name.
    - **-p**: Maps host ports to container ports.
    - **-e**: Sets environment variables for admin credentials and domain root.
    - **-v**: Persists data in a local volume.
    - **docker.io/bitnamilegacy/openldap:latest**: Specifies the image.

Step 2: Check the Status of the Container
-----------------------------------------
To check the status of the container, run the following command::

    podman ps

Step 3: Create LDIF File
-------------------------
The LDIF (LDAP Data Interchange Format) file is used to define the structure of the LDAP directory. The 
entries in the LDIF file include organization units, users, and groups.

1. To create an Organization Unit (OU) for users and groups, use the following content::

    dn: ou=People,dc=omnia,dc=test
    objectClass: top
    objectClass: organizationalUnit
    ou: People

This creates an organizational unit named People under the base domain.

2. To create a user, use the following content::

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

3. To create a group, use the following content::

    dn: cn=ldapuser,ou=groups,dc=omnia,dc=test
    objectClass: posixGroup
    cn: ldapuser
    gidNumber: 2000
    memberUid: ldapuser

This creates a group named ``ldapuser`` with a GID of 2000 and adds the user ``ldapuser`` to the group.

Step 4: Copy the LDIF Files into the Container
-----------------------------------------------
Once you have created the LDIF files (ou_people.ldif, ldapuser.ldif, ldapuser_grp.ldif), copy them 
into the running OpenLDAP container using the following commands:

::

    podman cp ou_people.ldif openldap:/
    podman cp ldapuser.ldif openldap:/
    podman cp ldapuser_grp.ldif openldap:/

This command copies all LDIF files into the running OpenLDAP container under the /tmp directory. 

Step 5: Add LDIF Files to the Directory
----------------------------------------

To import the LDIF files into the OpenLDAP directory, run the following commands::

    ldapadd -x -H ldap://localhost:1389 -D "cn=admin,dc=omnia,dc=test" -w Dell1234 -f ou_people.ldif
    ldapadd -x -H ldap://localhost:1389 -D "cn=admin,dc=omnia,dc=test" -w Dell1234 -f ldapuser.ldif
    ldapadd -x -H ldap://localhost:1389 -D "cn=admin,dc=omnia,dc=test" -w Dell1234 -f ldapuser_grp.ldif

The following are the parameters used in this command:

    - **-x**: Use simple authentication.
    - **-H**: LDAP server URL.
    - **-D**: Bind DN (admin distinguished name).
    - **-w**: Admin password.
    - **-f**: File to import.

Step 6: Set Password for OpenLDAP user
--------------------------------------

To set the password for the OpenLDAP user, run the following command::

    ldappasswd -x -D "cn=admin,dc=omnia,dc=test" -W -S -H ldap://localhost:1389 "uid=ldapuser,ou=People,dc=omnia,dc=test"

The following are the parameters used in the command:

    - **-x**: Use simple authentication.
    - **-D**: Bind DN (admin distinguished name).
    - **-W**: Prompt for the admin password.
    - **-S**: Prompt for the new password to assign.
    - The user's full DN identifies which entry to modify.

Step 7: Verify the User in LDAP
--------------------------------

To verify the user within the LDAP directory, run the following command::

    ldapsearch -x -H ldap://100.98.68.19:1389 -D "cn=admin,dc=omnia,dc=test" -W -b "dc=omnia,dc=test"

The following are the parameters used in the command:

    - **-b**: Search base DN.
    - **-H**: Host and port of the LDAP service.
    - This command lists all entries, including your newly created ldapuser.


Troubleshooting
----------------
If you encounter any issues, follow these steps:

- Ensure the container ports (1389 and 1636) are open and not blocked by firewalls.
- Check container logs with the following command::

    podman logs openldap

- If you encounter schema or DN errors, validate your LDIF syntax using the following command::

    slaptest -f <ldif-file>
