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
OpenLDAP Module - Variables.

Constants and default configuration values for OpenLDAP setup automation.
"""

# =============================================================================
# Container Defaults
# =============================================================================

OPENLDAP_CONTAINER_IMAGE = "docker.io/bitnamilegacy/openldap:latest"
OPENLDAP_CONTAINER_NAME = "openldap"
OPENLDAP_VOLUME_NAME = "openldap_data"

# =============================================================================
# Port Defaults
# =============================================================================

OPENLDAP_LDAP_PORT = 1389
OPENLDAP_LDAPS_PORT = 1636

# =============================================================================
# LDAP Defaults
# =============================================================================

OPENLDAP_DEFAULT_ADMIN_USERNAME = "admin"
OPENLDAP_DEFAULT_DOMAIN = "omnia.test"
OPENLDAP_DEFAULT_LOGIN_SHELL = "/bin/bash"
OPENLDAP_DEFAULT_UID_START = 2000

# =============================================================================
# Organizational Units
# =============================================================================

OPENLDAP_OU_PEOPLE = "People"
OPENLDAP_OU_GROUPS = "groups"
