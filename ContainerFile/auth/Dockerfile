FROM docker.io/chainguard/wolfi-base:latest

# Install OpenLDAP server and clients
RUN apk add --no-cache \
    openldap \
    openldap-back-mdb \
    openldap-clients \
    ca-certificates-bundle \
    ca-certificates

# Create ldap user/group — Wolfi does NOT auto-create this
# BusyBox syntax: addgroup/adduser (not groupadd/useradd)
RUN addgroup -S ldap && adduser -S -D -H -G ldap ldap

RUN mkdir -p /var/lib/openldap/openldap-data \
             /usr/local/share/ca-certificates \
             /container-init && \
    chown -R ldap:ldap /var/lib/openldap && \
    chown ldap:ldap /var/run/openldap

EXPOSE 389 636

CMD ["/bin/sh", "-c", "\
  mkdir -p /var/lib/openldap/openldap-data && \
  chown ldap:ldap /var/lib/openldap/openldap-data; \
  if [ ! -f /var/lib/openldap/openldap-data/__initialized ]; then \
    slapadd -f /etc/openldap/slapd.conf -l /container-init/bootstrap.ldif && \
    chown -R ldap:ldap /var/lib/openldap && \
    touch /var/lib/openldap/openldap-data/__initialized; \
  fi; \
  chmod 644 /etc/openldap/certs/ldapserver.key 2>/dev/null; \
  cp /etc/openldap/certs/ldapserver.crt /usr/local/share/ca-certificates/ldapserver.crt && \
  update-ca-certificates; \
  exec /usr/sbin/slapd -f /etc/openldap/slapd.conf -h 'ldap:/// ldaps:///' -u ldap -g ldap -d 0 \
"]