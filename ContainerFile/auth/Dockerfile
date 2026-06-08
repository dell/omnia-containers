FROM cgr.dev/chainguard/wolfi-base

# Install OpenLDAP server and clients
RUN apk update && apk add --no-cache \
    openldap \
    openldap-back-mdb \
    openldap-clients \
    ca-certificates-bundle

# Create ldap user/group — Wolfi does NOT auto-create this
# BusyBox syntax: addgroup/adduser (not groupadd/useradd)
RUN addgroup -S ldap && adduser -S -D -H -G ldap ldap

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
  cp /etc/openldap/certs/ldapserver.crt /usr/local/share/ca-certificates/ldapserver.crt && \
  update-ca-certificates; \
  exec /usr/sbin/slapd -f /etc/openldap/slapd.conf -h 'ldap:/// ldaps:///' -d 0 \
"]