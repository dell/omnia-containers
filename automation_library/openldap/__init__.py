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
OpenLDAP Module

This module provides functions for deploying a Bitnami OpenLDAP container
and creating LDAP users automatically using Podman.

Capabilities:
- Deploy Bitnami OpenLDAP container via Podman
- Create organizational units, users, and groups via LDIF
- Set user passwords
- Verify LDAP entries via ldapsearch
"""

from .functions import (
    load_openldap_config,
    domain_to_dc,
    validate_openldap_config,
    check_openldap_container,
    check_ldap_user_exists,
    check_ldap_ou_exists,
    check_ldap_group_exists,
)
from .vars import (
    OPENLDAP_CONTAINER_IMAGE,
    OPENLDAP_CONTAINER_NAME,
    OPENLDAP_LDAP_PORT,
    OPENLDAP_LDAPS_PORT,
    OPENLDAP_DEFAULT_ADMIN_USERNAME,
    OPENLDAP_DEFAULT_DOMAIN,
    OPENLDAP_DEFAULT_LOGIN_SHELL,
    OPENLDAP_DEFAULT_UID_START,
    OPENLDAP_VOLUME_NAME,
    OPENLDAP_OU_PEOPLE,
    OPENLDAP_OU_GROUPS,
)
from .messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SKIP_MSGS,
)
