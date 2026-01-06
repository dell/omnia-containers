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
Prepare OIM - Messages and Test Variables.

This module contains all messages, status strings, error instructions,
and test variables for the prepare_oim automation.

Author: Dell Technologies
"""

from typing import Dict
# is_ldap_enabled imported for potential future use
# pylint: disable=unused-import
from automation_library.prepare_oim.vars.prepare_oim_vars import (
    PREPARE_OIM_VARS,
    OPENCHAMI_CONTAINERS,
    CORE_CONTAINERS,
    AUTH_CONTAINER,
    is_ldap_enabled,  # noqa: F401
)

# =============================================================================
# TEST VARIABLES (for molecule/pytest tests)
# =============================================================================

TEST_VARS = {
    "omnia_target": PREPARE_OIM_VARS["omnia_target"],
    "openchami_target": PREPARE_OIM_VARS["openchami_target"],
    "ssh_alias": PREPARE_OIM_VARS["ssh_alias"],
    "oim_server_ip": PREPARE_OIM_VARS["oim_server_ip"],
    "openchami_containers": OPENCHAMI_CONTAINERS,
    "core_containers": CORE_CONTAINERS,
    "auth_container": AUTH_CONTAINER,
    "ssh_timeout": 5,
}

# Test names (displayed in test output header)
TEST_NAMES = {
    # Container verification
    "container_running": "Verify container {container} is running",
    "container_healthy": "Verify container {container} is healthy",
    "all_containers_running": "Verify all required containers are running",
    "openchami_containers": "Verify OpenChami containers are running",
    "core_containers": "Verify core infrastructure containers are running",
    "auth_container": "Verify auth container (LDAP enabled)",
    "auth_container_skipped": "Auth container check (LDAP not configured - SKIPPED)",
    # Service verification
    "omnia_target_active": "Verify omnia.target is active",
    "openchami_target_active": "Verify openchami.target is active",
    "service_dependencies": "Verify service dependencies",
    "bss_service_active": "Verify ochami BSS service is running",
    "smd_service_active": "Verify ochami SMD service is healthy",
    # OpenChami verification
    "ochami_bss_status": "Verify OpenChami BSS service status",
    "ochami_smd_status": "Verify OpenChami SMD service status",
    # Pulp verification
    "pulp_api_status": "Verify Pulp API password is correctly configured",
    "pulp_certificate": "Verify Pulp webserver certificate exists",
    # LDAP certificate verification
    "ldap_auth_certificate": "Verify LDAP auth certificate exists",
    "ldap_auth_certificate_skipped": "LDAP auth certificate check (LDAP not configured - SKIPPED)",
}

# Test log messages
TEST_LOG_MSGS = {
    # Container messages
    "container_running": "Container {container} is running",
    "container_not_running": "Container {container} is NOT running",
    "container_healthy": "Container {container} is healthy",
    "container_unhealthy": "Container {container} is unhealthy: {status}",
    "all_containers_running": "All required containers are running",
    "containers_failed": "{count} container(s) not running",
    "auth_skipped": "Auth container check skipped (LDAP not in software_config.json)",
    # Service messages
    "service_active": "Service {service} is active",
    "service_inactive": "Service {service} is {status}",
    "target_active": "{target} is active",
    "target_inactive": "{target} is {status}",
    "dependencies_ok": "All service dependencies are running",
    "dependencies_failed": "Some service dependencies are not running",
    "bss_service_active": "ochami BSS service is running",
    "bss_service_inactive": "ochami BSS service is {status}",
    "smd_service_active": "ochami SMD service is healthy",
    "smd_service_inactive": "ochami SMD service is {status}",
    # OpenChami messages
    "ochami_bss_ok": "OpenChami BSS service is running",
    "ochami_bss_fail": "OpenChami BSS service check failed",
    "ochami_smd_ok": "OpenChami SMD service is running",
    "ochami_smd_fail": "OpenChami SMD service check failed",
    # Pulp messages
    "pulp_api_ok": "Pulp API password is correctly configured",
    "pulp_api_fail": "Pulp API password validation failed",
    "pulp_cert_exists": "Pulp webserver certificate exists",
    "pulp_cert_not_found": "Pulp webserver certificate not found",
    # LDAP certificate messages
    "ldap_cert_exists": "LDAP auth certificate exists",
    "ldap_cert_not_found": "LDAP auth certificate not found",
    "ldap_cert_skipped": "LDAP auth certificate check skipped (LDAP not in software_config.json)",
}

# Test assert messages (user-friendly with instructions)
TEST_ASSERT_MSGS = {
    "container_not_running": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ CONTAINER CHECK FAILED: {container}
╠══════════════════════════════════════════════════════════════════════════════╣
║ Status: {status}
║
║ HOW TO FIX:
║   1. SSH to OIM server and check container: podman ps -a | grep {container}
║   2. Check container logs: podman logs {container}
║   3. Try restarting: podman restart {container}
║   4. If container doesn't exist, re-run prepare_oim.yml
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "container_unhealthy": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ CONTAINER UNHEALTHY: {container}
╠══════════════════════════════════════════════════════════════════════════════╣
║ Status: {status}
║
║ HOW TO FIX:
║   1. Check container health: podman inspect {container} --format '{{{{.State.Health}}}}'
║   2. Check container logs: podman logs {container}
║   3. Try restarting: podman restart {container}
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "service_not_active": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ SERVICE CHECK FAILED: {service}
╠══════════════════════════════════════════════════════════════════════════════╣
║ Expected: active | Got: {status}
║
║ HOW TO FIX:
║   1. Check service status: systemctl status {service}
║   2. Check service logs: journalctl -u {service} -n 50
║   3. Try restarting: systemctl restart {service}
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "target_not_active": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ SYSTEMD TARGET CHECK FAILED: {target}
╠══════════════════════════════════════════════════════════════════════════════╣
║ Expected: active | Got: {status}
║
║ HOW TO FIX:
║   1. Check target status: systemctl status {target}
║   2. List dependencies: systemctl list-dependencies {target}
║   3. Check failed units: systemctl list-units --state=failed
║   4. Re-run prepare_oim.yml if target was not created
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "ochami_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ OPENCHAMI {service} SERVICE CHECK FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Error: {error}
║
║ HOW TO FIX:
║   1. Check if ochami CLI is installed: which ochami
║   2. Check openchami.target: systemctl status openchami.target
║   3. Check OpenChami logs: ls -la /opt/omnia/log/openchami/
║   4. Verify OpenChami containers are running: podman ps | grep -E 'bss|smd'
║   5. Re-run prepare_oim.yml if OpenChami was not deployed
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "pulp_api_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ PULP API PASSWORD VALIDATION FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Status: {status}
║ Error: {error}
║
║ HOW TO FIX:
║   1. Check Pulp container: podman ps | grep pulp
║   2. Check Pulp logs: podman logs pulp
║   3. Verify pulp_password in omnia_config_credentials.yml
║   4. Test API manually: curl http://localhost:2225/pulp/api/v3/status/
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "pulp_cert_not_found": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ PULP WEBSERVER CERTIFICATE NOT FOUND
╠══════════════════════════════════════════════════════════════════════════════╣
║ Expected: /opt/omnia/pulp/settings/certs/pulp_webserver.crt inside omnia_core
║ Status: {status}
║
║ HOW TO FIX:
║   1. Check if omnia_core container is running: podman ps | grep omnia_core
║   2. Check certificate path: podman exec omnia_core ls -la /opt/omnia/pulp/settings/certs/
║   3. Check Pulp logs: podman logs pulp
║   4. Re-run prepare_oim.yml if certificate was not generated
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "bss_service_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ OCHAMI BSS SERVICE CHECK FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Expected: {{"bss-status":"running"}} | Got: {status}
║
║ HOW TO FIX:
║   1. Generate access token: export <HOSTNAME>_ACCESS_TOKEN=$(sudo bash -lc 'gen_access_token')
║   2. Check BSS status: ochami bss service status
║   3. Check OpenChami containers: podman ps | grep -E 'bss|smd'
║   4. Verify openchami.target is active: systemctl status openchami.target
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "smd_service_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ OCHAMI SMD SERVICE CHECK FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Expected: {{"code":0,"message":"HSM is healthy"}} | Got: {status}
║
║ HOW TO FIX:
║   1. Generate access token: export <HOSTNAME>_ACCESS_TOKEN=$(sudo bash -lc 'gen_access_token')
║   2. Check SMD status: ochami smd service status
║   3. Check OpenChami containers: podman ps | grep -E 'bss|smd'
║   4. Verify openchami.target is active: systemctl status openchami.target
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "ldap_cert_not_found": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ LDAP AUTH CERTIFICATE NOT FOUND
╠══════════════════════════════════════════════════════════════════════════════╣
║ Expected: /opt/omnia/auth/tls_certs/ldapserver.crt inside omnia_core container
║ Status: {status}
║
║ HOW TO FIX:
║   1. Check if omnia_core container is running: podman ps | grep omnia_core
║   2. Check certificate path: podman exec omnia_core ls -la /opt/omnia/auth/tls_certs/
║   3. Check auth logs: podman exec omnia_core cat /opt/omnia/log/auth.log
║   4. Re-run prepare_oim.yml if LDAP auth was not configured properly
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "validation_failed": "Validation failed: {error}",
}

# =============================================================================
# FUNCTION MESSAGES (for prepare_oim_func.py)
# =============================================================================

PREPARE_OIM_MSGS: Dict[str, str] = {

    # =========================================================================
    # PLAYBOOK EXECUTION
    # =========================================================================
    "playbook_start": "Starting prepare_oim.yml playbook execution...",
    "playbook_success": "prepare_oim.yml completed successfully",
    "playbook_fail": "prepare_oim.yml failed",
    "playbook_timeout": "prepare_oim.yml timed out after {timeout} seconds",

    # =========================================================================
    # CONTAINER VERIFICATION
    # =========================================================================
    "container_check_start": "Checking container status...",
    "container_running": "Container {container} is running",
    "container_not_running": "Container {container} is NOT running",
    "container_healthy": "Container {container} is healthy",
    "container_unhealthy": "Container {container} status: {status}",
    "all_containers_ok": "All required containers are running",
    "containers_failed": "{failed} of {total} containers not running",

    # =========================================================================
    # AUTH CONTAINER (LDAP)
    # =========================================================================
    "auth_check_start": "Checking auth container (LDAP)...",
    "auth_enabled": "LDAP is enabled in software_config.json",
    "auth_disabled": "LDAP is NOT enabled in software_config.json",
    "auth_skipped": "Skipping auth container check (LDAP not configured)",
    "auth_running": "Auth container (omnia_auth) is running",
    "auth_not_running": "Auth container (omnia_auth) is NOT running",

    # =========================================================================
    # SERVICE VERIFICATION
    # =========================================================================
    "service_check_start": "Checking systemd services...",
    "omnia_target_active": "omnia.target is active",
    "omnia_target_inactive": "omnia.target is {status}",
    "openchami_target_active": "openchami.target is active",
    "openchami_target_inactive": "openchami.target is {status}",
    "dependencies_check_start": "Checking service dependencies...",
    "dependencies_ok": "All service dependencies are running",
    "dependencies_failed": "Some dependencies are not running",

    # =========================================================================
    # OCHAMI VERIFICATION
    # =========================================================================
    "ochami_check_start": "Checking OpenChami services...",
    "ochami_bss_ok": "OpenChami BSS service is running",
    "ochami_bss_fail": "OpenChami BSS service check failed",
    "ochami_smd_ok": "OpenChami SMD service is running",
    "ochami_smd_fail": "OpenChami SMD service check failed",

    # =========================================================================
    # VALIDATION SUMMARY
    # =========================================================================
    "validation_start": "Starting prepare_oim validation...",
    "validation_pass": "All prepare_oim validations PASSED",
    "validation_fail": "prepare_oim validation FAILED: {failed_count} check(s) failed",
    "validation_summary": """
Validation Summary:
- Total: {total}
- Passed: {passed}
- Failed: {failed}
- Skipped: {skipped}
""",

    # =========================================================================
    # INSTRUCTIONS
    # =========================================================================
    "container_instruction": """
ACTION REQUIRED: Container is not running.
- Check container logs: podman logs {container}
- Check if container exists: podman ps -a | grep {container}
- Try restarting: podman restart {container}
""",

    "service_instruction": """
ACTION REQUIRED: Service is not active.
- Check service status: systemctl status {service}
- Check service logs: journalctl -u {service}
- Try restarting: systemctl restart {service}
""",

    "ochami_instruction": """
ACTION REQUIRED: OpenChami service check failed.
- Verify openchami.target is active: systemctl status openchami.target
- Check OpenChami logs in /opt/omnia/log/openchami/
- Re-run prepare_oim.yml if needed
""",
}
