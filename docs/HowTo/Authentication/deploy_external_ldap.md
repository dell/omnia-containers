# Deploy External LDAP Server

Deploy and configure a Bitnami OpenLDAP server using Podman on an external
server to provide centralized authentication for your Omnia cluster.

## Overview

This guide walks you through deploying a containerized OpenLDAP server using
the Bitnami OpenLDAP image. The LDAP server provides centralized user
authentication and directory services for cluster nodes. Once deployed, you
can integrate this LDAP server with Omnia-managed nodes for unified user
management.

The deployment includes:

- Bitnami OpenLDAP container running via Podman
- LDAP directory structure (organizational units, users, groups)
- User authentication configuration
- Integration with Omnia cluster nodes

## Prerequisites

- An external server (physical or virtual) with Podman installed.
- Network connectivity between the LDAP server and Omnia cluster nodes.
- Root or sudo access on the LDAP server.
- Firewall rules allowing LDAP ports (1389 for LDAP, 1636 for LDAPS).

!!! note

    In the examples below, the domain components used are `dc=omnia,dc=test`,
    corresponding to the domain name `omnia.test`. Replace these values with
    your own domain components (for example, `dc=example,dc=com` or
    `dc=mycompany,dc=local`). Similarly, replace `<admin_password>` with a
    secure password of your choice.

## Procedure

1. **Deploy the OpenLDAP container**:

    ```bash title="Run on: LDAP server"
    podman run -d --name openldap \
      -p 0.0.0.0:1389:1389 \
      -p 0.0.0.0:1636:1636 \
      -e LDAP_ADMIN_USERNAME=admin \
      -e LDAP_ADMIN_PASSWORD=<admin_password> \
      -e LDAP_ROOT=dc=omnia,dc=test \
      -v openldap_data:/bitnami/openldap \
      docker.io/bitnamilegacy/openldap:latest
    ```

    | Parameter | Description |
    |-----------|-------------|
    | `-d` | Run container in detached mode |
    | `--name openldap` | Assigns a container name |
    | `-p` | Maps host ports to container ports |
    | `-e` | Sets environment variables for admin credentials and domain root |
    | `-v` | Persists data in a local volume |
    | `docker.io/bitnamilegacy/openldap:latest` | Specifies the image |

2. **Verify the container is running**:

    ```bash title="Run on: LDAP server"
    podman ps
    ```

3. **Create the organizational unit LDIF file** -- Create a file named
   `ou_people.ldif`:

    ```ldif title="File: ou_people.ldif"
    dn: ou=People,dc=omnia,dc=test
    objectClass: top
    objectClass: organizationalUnit
    ou: People
    ```

4. **Create the user LDIF file** -- Create a file named `ldapuser.ldif`:

    ```ldif title="File: ldapuser.ldif"
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
    ```

5. **Create the group LDIF file** -- Create a file named
   `ldapuser_grp.ldif`:

    ```ldif title="File: ldapuser_grp.ldif"
    dn: cn=ldapuser,ou=groups,dc=omnia,dc=test
    objectClass: posixGroup
    cn: ldapuser
    gidNumber: 2000
    memberUid: ldapuser
    ```

6. **Copy the LDIF files into the container**:

    ```bash title="Run on: LDAP server"
    podman cp ou_people.ldif openldap:/
    podman cp ldapuser.ldif openldap:/
    podman cp ldapuser_grp.ldif openldap:/
    ```

7. **Access the container shell**:

    ```bash title="Run on: LDAP server"
    podman exec -it openldap /bin/bash
    ```

8. **Import the LDIF files into OpenLDAP**:

    ```bash title="Run on: openldap container"
    ldapadd -x -H ldap://localhost:1389 -D "cn=admin,dc=omnia,dc=test" -w <admin_password> -f ou_people.ldif
    ldapadd -x -H ldap://localhost:1389 -D "cn=admin,dc=omnia,dc=test" -w <admin_password> -f ldapuser.ldif
    ldapadd -x -H ldap://localhost:1389 -D "cn=admin,dc=omnia,dc=test" -w <admin_password> -f ldapuser_grp.ldif
    ```

    | Parameter | Description |
    |-----------|-------------|
    | `-x` | Use simple authentication |
    | `-H` | LDAP server URL |
    | `-D` | Bind DN (admin distinguished name) |
    | `-w` | Admin password |
    | `-f` | File to import |

9. **Set the password for the LDAP user**:

    ```bash title="Run on: openldap container"
    ldappasswd -x -D "cn=admin,dc=omnia,dc=test" -W -S -H ldap://localhost:1389 "uid=ldapuser,ou=People,dc=omnia,dc=test"
    ```

    | Parameter | Description |
    |-----------|-------------|
    | `-x` | Use simple authentication |
    | `-D` | Bind DN (admin distinguished name) |
    | `-W` | Prompt for the admin password |
    | `-S` | Prompt for the new password to assign |

!!! tip

    To add more users, repeat steps 4, 6, 7, 8, and 9 with a new LDIF file
    for each user. Increment the `uidNumber` and `gidNumber` values to
    ensure they are unique across the directory.

## Verification

Run the following command to list all entries in the LDAP directory and
confirm your user was created:

```bash title="Run on: openldap container"
ldapsearch -x -H ldap://localhost:1389 -D "cn=admin,dc=omnia,dc=test" -W -b "dc=omnia,dc=test"
```

The output should include the `ldapuser` entry with the POSIX attributes
you configured in the LDIF file.

## Troubleshooting

### Container fails to start or ports are unreachable

Verify the container is running and ports `1389` and `1636` are not blocked
by a firewall:

```bash title="Run on: LDAP server"
podman ps
podman logs openldap
```

### LDIF import fails with schema or DN errors

Validate the LDIF file syntax before importing:

```bash title="Run on: LDAP server"
slaptest -f <ldif-file>
```

### Common error messages

| Error | Cause | Resolution |
|-------|-------|------------|
| `No such object` | The parent organizational unit does not exist | Create `ou=People` and `ou=groups` before adding child entries |
| `File not found` | LDIF files were not copied into the container | Re-run the `podman cp` commands in step 6 |
| `Connection refused` | Container is not running or ports are not mapped | Run `podman ps` to verify the container is up |
| `Invalid credentials` | Admin password or DN format is incorrect | Verify the password and DN match the values used in step 1 |