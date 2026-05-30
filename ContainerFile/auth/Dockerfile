FROM fedora:42

# Update system packages to fix CVEs: openssl, libssh, curl, libxml2, systemd, vim, etc.
RUN dnf -y update && \
    dnf -y install openldap-servers openldap-clients && \
    dnf clean all


RUN mkdir -p /var/lib/openldap/openldap-data && \
    chown -R ldap:ldap /var/lib/openldap
EXPOSE 389 636
CMD ["/bin/sh", "-c", "\
  mkdir -p /var/lib/openldap/openldap-data && \
  chown ldap:ldap /var/lib/openldap/openldap-data; \
  if [ ! -f /var/lib/openldap/openldap-data/__initialized ]; then \
    slapadd -f /etc/openldap/slapd.conf -l /container-init/bootstrap.ldif && \
    chown -R ldap:ldap /var/lib/openldap && \
    touch /var/lib/openldap/openldap-data/__initialized; \
  fi; \
  cp /etc/openldap/certs/ldapserver.crt /etc/pki/ca-trust/source/anchors/ && \
  update-ca-trust; \
  exec /usr/sbin/slapd -f /etc/openldap/slapd.conf -h 'ldap:/// ldaps:///' -d 0 \
"]
