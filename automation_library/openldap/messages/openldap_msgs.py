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
OpenLDAP Module - Messages.

Test names, log messages, and assertion messages for OpenLDAP setup tests.
"""

from typing import Dict

# =============================================================================
# TEST NAMES — displayed in reports and TestLogger
# =============================================================================

TEST_NAMES: Dict[str, str] = {
    "container_running": "Verify OpenLDAP container is running",
    "container_ports": "Verify OpenLDAP container ports are mapped correctly",
    "ou_people_exists": "Verify organizational unit 'People' exists in LDAP",
    "ou_groups_exists": "Verify organizational unit 'groups' exists in LDAP",
    "user_exists": "Verify LDAP user '{username}' exists in directory",
    "user_posix_attrs": "Verify LDAP user '{username}' has correct POSIX attributes",
    "group_exists": "Verify LDAP group '{username}' exists in directory",
    "user_password_set": "Verify LDAP user '{username}' password is set",
    "ldap_search_works": "Verify ldapsearch returns entries from directory",
    "config_valid": "Verify OpenLDAP configuration is valid",
}

# =============================================================================
# LOG MESSAGES — for TestLogger during test execution
# =============================================================================

TEST_LOG_MSGS: Dict[str, str] = {
    # Container
    "container_running": "OpenLDAP container '{container_name}' is running",
    "container_not_running": "OpenLDAP container '{container_name}' is NOT running",
    "container_ports_ok": "Container ports mapped correctly: {ldap_port}->1389, {ldaps_port}->1636",

    # Organizational units
    "ou_exists": "Organizational unit '{ou_name}' exists in LDAP directory",
    "ou_not_found": "Organizational unit '{ou_name}' NOT found in LDAP directory",

    # Users
    "user_exists": "LDAP user '{username}' exists in directory",
    "user_not_found": "LDAP user '{username}' NOT found in directory",
    "user_attrs_ok": "LDAP user '{username}' has correct POSIX attributes (uid={uid_number}, gid={gid_number})",
    "user_attrs_mismatch": "LDAP user '{username}' attribute mismatch: {details}",
    "user_password_ok": "LDAP user '{username}' password is set and valid",
    "user_password_missing": "LDAP user '{username}' password is NOT set",

    # Groups
    "group_exists": "LDAP group '{group_name}' exists with gidNumber={gid_number}",
    "group_not_found": "LDAP group '{group_name}' NOT found in directory",

    # Search
    "search_ok": "ldapsearch returned {entry_count} entries from directory",
    "search_failed": "ldapsearch failed: {error}",

    # Config
    "config_valid": "OpenLDAP configuration is valid",
    "config_invalid": "OpenLDAP configuration is invalid: {error}",
}

# =============================================================================
# ASSERTION MESSAGES — shown when tests fail (include HOW TO FIX)
# =============================================================================

TEST_ASSERT_MSGS: Dict[str, str] = {
    "container_not_running": (
        "OpenLDAP container '{container_name}' is not running.\n\n"
        "HOW TO FIX:\n"
        "  1. Check container status: podman ps -a --filter name={container_name}\n"
        "  2. Check container logs: podman logs {container_name}\n"
        "  3. Re-run the openldap converge: ./run_molecule.sh openldap converge\n"
        "  4. Verify the image was pulled: podman images | grep openldap"
    ),

    "container_ports_failed": (
        "OpenLDAP container port mapping is incorrect.\n"
        "Expected: {ldap_port}->1389, {ldaps_port}->1636\n"
        "Actual: {actual_ports}\n\n"
        "HOW TO FIX:\n"
        "  1. Remove and recreate the container with correct port mappings\n"
        "  2. Check for port conflicts: ss -tlnp | grep -E '{ldap_port}|{ldaps_port}'\n"
        "  3. Re-run: ./run_molecule.sh openldap converge"
    ),

    "ou_not_found": (
        "Organizational unit '{ou_name}' not found in LDAP directory.\n"
        "Base DN: {base_dn}\n\n"
        "HOW TO FIX:\n"
        "  1. Check LDAP directory: ldapsearch -x -H ldap://localhost:{port} "
        "-D \"cn=admin,{base_dn}\" -w <password> -b \"{base_dn}\"\n"
        "  2. Re-run converge to create OUs: ./run_molecule.sh openldap converge\n"
        "  3. Check container logs: podman logs {container_name}"
    ),

    "user_not_found": (
        "LDAP user '{username}' not found in directory.\n"
        "Expected DN: uid={username},ou=People,{base_dn}\n\n"
        "HOW TO FIX:\n"
        "  1. Search for the user: ldapsearch -x -H ldap://localhost:{port} "
        "-D \"cn=admin,{base_dn}\" -w <password> -b \"ou=People,{base_dn}\" \"(uid={username})\"\n"
        "  2. Re-run converge: ./run_molecule.sh openldap converge\n"
        "  3. Check LDIF import errors in converge output"
    ),

    "user_attrs_mismatch": (
        "LDAP user '{username}' POSIX attributes do not match expected values.\n"
        "Mismatches: {details}\n\n"
        "HOW TO FIX:\n"
        "  1. Check user attributes: ldapsearch -x -H ldap://localhost:{port} "
        "-D \"cn=admin,{base_dn}\" -w <password> \"(uid={username})\"\n"
        "  2. Delete and recreate the user by re-running converge\n"
        "  3. Verify omnia_test_config.yml openldap_users settings"
    ),

    "group_not_found": (
        "LDAP group '{group_name}' not found in directory.\n"
        "Expected DN: cn={group_name},ou=groups,{base_dn}\n\n"
        "HOW TO FIX:\n"
        "  1. Search for group: ldapsearch -x -H ldap://localhost:{port} "
        "-D \"cn=admin,{base_dn}\" -w <password> -b \"ou=groups,{base_dn}\" \"(cn={group_name})\"\n"
        "  2. Re-run converge: ./run_molecule.sh openldap converge\n"
        "  3. Check LDIF import errors in converge output"
    ),

    "user_password_not_set": (
        "LDAP user '{username}' password is not set.\n\n"
        "HOW TO FIX:\n"
        "  1. Set password manually: podman exec {container_name} ldappasswd -x "
        "-D \"cn=admin,{base_dn}\" -w <admin_password> -S "
        "\"uid={username},ou=People,{base_dn}\"\n"
        "  2. Re-run converge: ./run_molecule.sh openldap converge\n"
        "  3. Check ldappasswd errors in converge output"
    ),

    "config_invalid": (
        "OpenLDAP configuration in omnia_test_config.yml is invalid.\n"
        "Errors: {errors}\n\n"
        "HOW TO FIX:\n"
        "  1. Set openldap_admin_password in omnia_test_config.yml\n"
        "  2. Add at least one user to openldap_users list\n"
        "  3. Each user must have 'username' and 'password' fields\n"
        "  4. Verify openldap_domain is a valid domain (e.g., 'omnia.test')"
    ),
}

# =============================================================================
# SKIP MESSAGES — for pytest.skip() calls
# =============================================================================

SKIP_MSGS: Dict[str, str] = {
    "no_admin_password": "OpenLDAP admin password not configured in omnia_test_config.yml",
    "no_users_configured": "No LDAP users configured in omnia_test_config.yml openldap_users",
    "container_not_running": "OpenLDAP container is not running — run converge first",
    "openldap_not_configured": "OpenLDAP setup not configured (openldap_admin_password is empty)",
}
