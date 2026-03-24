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

"""

# Test names (displayed in test output header)
TEST_NAMES = {
    # Consolidated status
    "service_status": "Verify all service/target status",
    "container_status": "Verify all container status",
    "openchami_target": "Verify openchami.target dependencies",
    "omnia_target": "Verify omnia.target dependencies",
    # Service verification
    "bss_service_active": "Verify ochami BSS service is running",
    "smd_service_active": "Verify ochami SMD service is healthy",
    # Pulp verification
    "pulp_api_status": "Verify Pulp API password is correctly configured",
    "pulp_certificate": "Verify Pulp webserver certificate exists",
    # LDAP certificate verification
    "ldap_auth_certificate": "Verify LDAP auth certificate exists",
    "ldap_auth_certificate_skipped": "LDAP auth certificate check (LDAP not configured - SKIPPED)",
}

# Test log messages
TEST_LOG_MSGS = {
    # Consolidated status
    "services_ok": "All services/targets in expected state",
    "services_failed": "Service/target status check failed",
    "containers_ok": "All containers in expected state",
    "containers_failed": "Container status check failed",
    "openchami_target_ok": "All openchami.target dependencies matched",
    "openchami_target_failed": "openchami.target dependency mismatch detected",
    "omnia_target_ok": "All omnia.target dependencies matched",
    "omnia_target_failed": "omnia.target dependency mismatch detected",
    # Service messages
    "bss_service_active": "ochami BSS service is running",
    "bss_service_inactive": "ochami BSS service is {status}",
    "smd_service_active": "ochami SMD service is healthy",
    "smd_service_inactive": "ochami SMD service is {status}",
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
}
