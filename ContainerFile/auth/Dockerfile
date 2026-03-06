FROM fedora:40

# Update system and install OpenLDAP with security patches
RUN dnf -y update && \
    dnf -y install openldap-servers openldap-clients && \
    dnf clean all && \
    rm -rf /var/cache/dnf


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
