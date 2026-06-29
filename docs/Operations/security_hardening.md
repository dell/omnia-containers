
# Security Hardening


After deploying an Omnia cluster, apply these security hardening measures to
protect the environment against unauthorized access, data exposure, and
configuration drift. These procedures complement the security built into
Omnia's default deployment (AES-256 encrypted credentials, OpenLDAP, TLS via
step-ca).

## Credential rotation


Omnia stores sensitive credentials (database passwords, LDAP bind passwords,
iDRAC credentials) in Ansible Vault files encrypted with AES-256. Rotate these
credentials periodically to limit the impact of any potential exposure.

### Rotate vault passwords


1. Access the `omnia_core` container:

   ```bash
   ssh omnia_core
   ```


2. Re-key the vault file with a new password:

   ```bash
   cd /omnia
   ansible-vault rekey input/credentials.yml
   ```


   Enter the current vault password, then provide the new password twice.

3. Update any scripts or CI/CD pipelines that reference the old vault password.

!!! warning

    Store vault passwords in a secure location (hardware security module,
    enterprise password manager). Do not commit vault passwords to version
    control.

### Rotate service credentials


To rotate individual service credentials (for example, the Slurm database
password or LDAP admin password):

1. Edit the encrypted credentials file:

   ```bash
   ansible-vault edit input/credentials.yml
   ```


2. Update the relevant password fields.

3. Re-run the appropriate playbook to propagate the new credentials:

   ```bash
   # For Slurm credentials
   ansible-playbook playbooks/omnia.yml --tags slurm

   # For LDAP credentials
   ansible-playbook playbooks/auth.yml
   ```



## TLS certificate management


Omnia uses [step-ca](https://smallstep.com/docs/step-ca/) as an internal
certificate authority (CA) to issue TLS certificates for inter-service
communication.

### Check certificate expiry


```bash title="Run on: OIM host"
# List certificates and their expiry dates
step certificate inspect /etc/step/certs/server.crt --short

# Check days until expiry
step certificate needs-renewal /etc/step/certs/server.crt
```


### Renew certificates


Certificates issued by step-ca are typically short-lived and auto-renewed.
If automatic renewal fails:

```bash title="Run on: OIM host"
# Manually renew
step ca renew /etc/step/certs/server.crt /etc/step/certs/server.key

# Restart affected services to pick up the new certificate
podman restart <service_container>
```


!!! tip

    Configure monitoring to alert when certificates are within 7 days of expiry.
    The `step certificate needs-renewal` command exits with code 0 when renewal
    is needed, making it easy to integrate into a cron job or monitoring script.

## Firewall rules


The OIM and cluster nodes should restrict network access to only the ports
required by Omnia services.

### OIM firewall configuration


```bash title="Run on: OIM host"
# Allow SSH (management)
firewall-cmd --permanent --add-service=ssh

# Allow DHCP (provisioning)
firewall-cmd --permanent --add-service=dhcp

# Allow TFTP (PXE boot)
firewall-cmd --permanent --add-service=tftp

# Allow HTTP/HTTPS (Pulp repositories, AWX)
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https

# Reload to apply
firewall-cmd --reload

# Verify active rules
firewall-cmd --list-all
```


### Compute node firewall configuration


```bash title="Run on: compute node"
# Allow Slurm communication
firewall-cmd --permanent --add-port=6817-6819/tcp

# Allow SSH (inter-node communication for MPI)
firewall-cmd --permanent --add-service=ssh

# Allow LDAP client connections
firewall-cmd --permanent --add-port=389/tcp
firewall-cmd --permanent --add-port=636/tcp

# Reload to apply
firewall-cmd --reload
```


!!! note

    Omnia configures basic firewall rules during deployment. The commands above
    are for verification and for adding additional restrictions beyond the
    defaults.

## LDAP hardening


If you are using OpenLDAP for centralized authentication, apply these hardening
measures:

1. **Enforce TLS for all LDAP connections:**

   Ensure `ldaps://` (port 636) is used instead of unencrypted `ldap://`
   (port 389). Update the LDAP client configuration on all nodes:

   ```bash title="File: /etc/openldap/ldap.conf"
   # /etc/openldap/ldap.conf
   URI ldaps://auth-server.example.com
   TLS_CACERT /etc/openldap/certs/ca.crt
   TLS_REQCERT demand
   ```


2. **Restrict anonymous binds:**

   Configure the LDAP server to disallow anonymous access:

   ```bash title="Run on: OIM host"
   ldapmodify -Y EXTERNAL -H ldapi:/// <<EOF
   dn: cn=config
   changetype: modify
   replace: olcDisallows
   olcDisallows: bind_anon
   EOF
   ```


3. **Set strong password policies:**

   Configure password complexity, lockout, and expiry in the LDAP password
   policy overlay.

4. **Limit LDAP admin access:**

   Restrict the LDAP admin bind DN to connections originating from the OIM and
   authentication server only.


## Disable unnecessary services


Review running services on all nodes and disable anything not required:

```bash title="Run on: compute node"
# List all enabled services
systemctl list-unit-files --state=enabled

# Disable services not needed on compute nodes
systemctl disable --now cups.service
systemctl disable --now avahi-daemon.service
systemctl disable --now bluetooth.service

# Verify
systemctl list-unit-files --state=enabled | wc -l
```



## Routine security updates


Apply security patches regularly on the OIM and all cluster nodes:

```bash title="Run on: OIM host"
# Install only security updates (RHEL/Rocky)
yum update --security -y

# Check for available security updates without installing
yum updateinfo list security

# Schedule automatic security updates (optional)
yum install -y dnf-automatic
systemctl enable --now dnf-automatic-install.timer
```


!!! important

    Schedule security updates during maintenance windows to avoid disrupting
    running jobs. Drain Slurm nodes before applying updates, and verify cluster
    health afterward (see [Add Remove Nodes](add_remove_nodes.md) for drain procedures).

## Additional recommendations


- **Audit logging** -- Enable `auditd` on all nodes to track privileged
  operations and file access.
- **SSH hardening** -- Disable password-based SSH authentication and require
  key-based login. Limit SSH access to specific user groups.
- **SELinux** -- Keep SELinux in `enforcing` mode. Omnia playbooks are
  designed to work with SELinux enabled.
- **iDRAC security** -- Change default iDRAC passwords, disable unused
  protocols (Telnet, IPMI-over-LAN if not needed), and keep iDRAC firmware
  current.


!!! info

    - [Best Practices Checklist](best_practices_checklist.md) -- Consolidated checklist including
      security items.
    - [Authentication](../Troubleshooting/authentication.md) -- Troubleshoot LDAP and
      authentication issues.
    - [Log Management](log_management.md) -- Log monitoring for security events.
