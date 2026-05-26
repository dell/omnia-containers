# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Discovery Module - LDAP Variables.

LDAP slapd.conf template and configuration constants.
"""

# =============================================================================
# LDAP CONTAINER
# =============================================================================

LDAP_CONTAINER_NAME = "omnia_auth"

# =============================================================================
# LDAP CONTAINER STABILITY CONSTANTS
# =============================================================================

CONTAINER_STABLE_WAIT_SECONDS = 30
CONTAINER_CHECK_INTERVAL = 3

# =============================================================================
# SLAPD.CONF TEMPLATE
# =============================================================================
# Variables to replace:
# - {ldap_suffix} - e.g., dc=chola,dc=test
# - {ldap_rootdn} - e.g., cn=admin,dc=chola,dc=test
# - {ldap_rootpw} - e.g., Dell1234
# - {ldap_uri} - e.g., ldap://100.98.72.114:1389/dc=chola,dc=test
# - {ldap_suffixmassage_local} - e.g., dc=chola,dc=test
# - {ldap_suffixmassage_remote} - e.g., dc=omnia,dc=test
# - {ldap_bind_dn} - e.g., cn=admin,dc=omnia,dc=test
# - {ldap_bind_credentials} - e.g., Dell1234

SLAPD_CONF_TEMPLATE = """include        /etc/openldap/schema/core.schema
include        /etc/openldap/schema/cosine.schema
include        /etc/openldap/schema/nis.schema
include        /etc/openldap/schema/inetorgperson.schema

pidfile         /run/openldap/slapd.pid
argsfile        /run/openldap/slapd.args

# Load dynamic backend modules:
modulepath      /usr/lib64/openldap
moduleload      back_ldap.la
moduleload      back_meta.la

###############################################################################
# Meta database definitions
###############################################################################
database        meta
suffix          "{ldap_suffix}"
rootdn          {ldap_rootdn}
rootpw          {ldap_rootpw}

uri             "{ldap_uri}"
suffixmassage   "{ldap_suffixmassage_local}" "{ldap_suffixmassage_remote}"
idassert-bind
 bindmethod=simple
 binddn="{ldap_bind_dn}"
 credentials="{ldap_bind_credentials}"
 flags=override
 mode=none
TLSCACertificateFile    /etc/openldap/certs/ldapserver.crt
TLSCertificateFile      /etc/openldap/certs/ldapserver.crt
TLSCertificateKeyFile   /etc/openldap/certs/ldapserver.key
"""
