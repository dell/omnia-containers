Step 4: Setup OpenLDAP for Centralized Authentication 
======================================================

Set up OpenLDAP to allow or deny access to the user(s).

**Prerequisites**

* To set up OpenLDAP, ensure that the following entry is present in the ``/opt/omnia/input/project_default/software_config.json``: ::

    {"name": "openldap", "arch": ["x86_64"]}

* Run ``prepare_oim.yml`` to start the Omnia Auth container.

* Run ``local_repo.yml`` to create offline repositories of OpenLDAP. For more information, See :doc:`Create Local Repository <../CreateLocalRepo/index>`.

* Run  ``build_image_x86_64.yml``/ ``build_image_aarch64.yml`` to build the images with OpenLDAP packages on the login node, slurm node, and slurm control node image.


Create a New User on OpenLDAP
-----------------------------

1. Create an LDIF file (eg: ``create_user.ldif``) on the auth server containing the following information:

    * DN: The distinguished name that indicates where the user will be created.
    * objectClass: The object class specifies the mandatory and optional attributes that can be associated with an entry of that class. Here, the values are ``inetOrgPerson``, ``posixAccount``, and ``shadowAccount``.
    * UID: The username of the replication user.
    * sn: The surname of the intended user.
    * cn: The given name of the intended user.

Below is a sample file: ::

    # User Creation
    dn: uid=ldapuser,ou=People,dc=omnia,dc=test
    objectClass: inetOrgPerson
    objectClass: posixAccount
    objectClass: shadowAccount
    cn: ldapuser
    sn: ldapuser
    loginShell:/bin/bash
    uidNumber: 2000
    gidNumber: 2000
    homeDirectory: /home/ldapuser
    shadowLastChange: 0
    shadowMax: 0
    shadowWarning: 0

    # Group Creation
    dn: cn=ldapuser,ou=Group,dc=omnia,dc=test
    objectClass: posixGroup
    cn: ldapuser
    gidNumber: 2000
    memberUid: ldapuser

.. note:: Avoid whitespaces when using an LDIF file for user creation. Extra spaces in the input data may be encrypted by OpenLDAP and cause access failures.

2. Run the command ``ldapadd -D <enter admin binddn > -w < bind_password > -f create_user.ldif`` to execute the LDIF file and create the account.
3. To set up a password for this account, use the command ``ldappasswd -D <enter admin binddn > -w < bind_password > -S <user_dn>``. The value of ``user_dn`` is the distinguished name that indicates where the user was created. (In this example, ``uid=ldapuser,ou=People,dc=omnia,dc=test``)


Configure OpenLDAP Connection Type
--------------------------------------

Omnia authenticates users against OpenLDAP using TLS-only connection. The connection type is predefined to TLS in the ``security_config.yml`` available at ``/opt/omnia/input/project_default/`` directory.


.. csv-table:: Parameters for Authentication
   :file: ../../../../Tables/security_config_ldap.csv
   :header-rows: 1
   :keepspace:


Configure OpenLDAP as a Proxy Server
--------------------------------------

Omnia allows the internal OpenLDAP server to be configured as a proxy, where it utilizes the external LDAP servers as a backend database to store user data and acts as an authentication entity to allow/deny them access to the cluster. OpenLDAP client will be configured through the proxy server which means that there won't be any direct communication between OpenLDAP client and the external LDAP server.

.. note:: If the OpenLDAP server is set up as a proxy, the user database is not replicated onto the server.

Perform the following steps to configure OpenLDAP as a proxy server:

1. Locate the config file present in ``/opt/omnia/auth/``.

2. Add the following lines to the ``slapd.conf`` file based on the operating system running on the cluster:

    For RHEL: ::

        include        /etc/openldap/schema/core.schema
        include        /etc/openldap/schema/cosine.schema
        include        /etc/openldap/schema/nis.schema
        include        /etc/openldap/schema/inetorgperson.schema
        
        
        pidfile         /run/openldap/slapd.pid
        argsfile        /run/openldap/slapd.args
        
        # Load dynamic backend modules:
        modulepath      /usr/lib64/openldap
        moduleload      back_ldap.la
        moduleload      back_meta.la

        #######################################################################
        # Meta database definitions
        #######################################################################
        database        meta
        suffix          "dc=phantom,dc=test"
        rootdn          cn=admin,dc=phantom,dc=test
        rootpw          Dell1234

        uri             "ldap://10.5.0.104:389/dc=phantom,dc=test"
        suffixmassage   "dc=phantom,dc=test" "dc=perf,dc=test"
        idassert-bind
         bindmethod=simple
         binddn="cn=admin,dc=perf,dc=test"
         credentials="Dell1234"
         flags=override
         mode=none
        TLSCACertificateFile    /etc/openldap/certs/ldapserver.crt
        TLSCertificateFile      /etc/openldap/certs/ldapserver.crt
        TLSCertificateKeyFile   /etc/openldap/certs/ldapserver.key

Change the **<parameter>** values in the config file, as described below:

* **database**: Database used in the ``slapd.conf`` file, that captures the details of the external LDAP server to be used. For example, ``meta``.
* **suffix**: Captures the domain name of internal OpenLDAP user, to refine the user search while attempting to authenticate the user. For example, ``"dc=omnia,dc=test"``.
* **rootdn**: Admin or root username of the internal OpenLDAP server set up by Omnia. For example, ``cn=admin,dc=omnia,dc=test``.
* **rootpw**: Admin password for the internal OpenLDAP server. For example, ``Dell1234``.

* **uri**: Captures the IP of the external LDAP server along with the port and the domain of the user in ``"ldap://<IP  of external LDAP server>:<Port number>/<suffix>"`` format. For example, ``"ldap://10.5.0.104:389/dc=omnia,dc=test"``.
* **suffixmassage**: ``suffixmassage`` allows you to dynamically move the LDAP client information from the existing internal OpenLDAP server to the external LDAP server that you want to configure as a proxy. This is provided in the ``suffixmassage <suffix1> <suffix2>`` format.

        * ``<suffix1>`` is the internal OpenLDAP server suffix (base DN).
        * ``<suffix2>`` is the external LDAP server suffix (base DN).

* **binddn**: Admin username and domain of the external LDAP server.
* **credentials**: Admin password for the external LDAP server.

* **TLSCACertificateFile**: Omnia, by default, creates the TLSA certificate in ``/etc/openldap/certs/ldapserver.crt``.
* **TLSCertificateFile**: Omnia, by default, creates the TLS certificate in ``/etc/openldap/certs/ldapserver.crt``.
* **TLSCertificateKeyFile**: Omnia, by default, creates the certificate key file in ``/etc/pki/tls/certs/ldapserver.key``.

.. note::
   * The values for ``suffix`` and ``rootdn`` parameters in the ``slapd.conf`` file must be the same as those provided in the ``get_config_credentials.yml`` file.

   * Multiple external LDAP servers can also be configured on the proxy server. The OpenLDAP proxy server allows users from multiple external LDAP servers to authenticate onto the cluster. You can provide two sets of external LDAP server details as shown below: ::

            uri "ldap://10.5.0.104:389/dc=omnia1,dc=test"
            idassert-bind
             bindmethod=simple
             binddn="cn=admin,dc=omnia,dc=test"
             credentials="Dell1234"
             flags=override
             mode=none

            uri "ldap://10.5.0.105:389/dc=omnia2,dc=test"
            idassert-bind
             bindmethod=simple
             binddn="cn=admin,dc=omnia,dc=test"
             credentials="Dell12345"
             flags=override
             mode=none

3. Once the new configurations are present in the ``slapd.conf`` file, restart the ``omnia_auth`` service: ::

    sudo systemctl restart omnia_auth.service

Once these configurations are applied on the internal OpenLDAP server, it sets up the external LDAP server as an authentication server. The internal OpenLDAP server doesn't store any kind of user data and no users can be created/modified from here.