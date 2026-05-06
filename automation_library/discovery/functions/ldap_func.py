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
Discovery Module - LDAP Functions.

Functions for LDAP slapd.conf configuration and verification.
"""

import time
from typing import Dict, Any, List

import pytest

from automation_library.core import (
    run_on_oim,
    run_in_container,
    run_on_remote_node,
    is_software_enabled,
    get_multiple_credentials,
    load_omnia_test_config,
    SLAPD_CONF_PATH,
    OMNIA_CREDENTIALS_PATH,
    OMNIA_CREDENTIALS_KEY_PATH,
)
from .common_func import (
    parse_ssh_error,
    get_slurm_control_nodes,
    get_slurm_compute_nodes,
    get_login_nodes,
    get_login_compiler_nodes,
)

from ..messages import SKIP_MSGS
from ..vars import (
    LDAP_CONTAINER_NAME,
    SLAPD_CONF_TEMPLATE,
    CONTAINER_STABLE_WAIT_SECONDS,
    CONTAINER_CHECK_INTERVAL,
)


# =============================================================================
# ENABLE CHECK AND SKIP FUNCTIONS
# =============================================================================

def is_openldap_enabled(host) -> bool:
    """Check if OpenLDAP is enabled in software_config.json."""
    return is_software_enabled(host, "openldap")


def skip_if_openldap_not_enabled(host, log):
    """Skip test if OpenLDAP is not enabled in software_config.json."""
    if not is_openldap_enabled(host):
        msg = SKIP_MSGS["openldap_not_enabled"]
        log.skipped(msg, SKIP_MSGS["skip_detail_not_enabled"].format(software="OpenLDAP"))
        pytest.skip(msg)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def domain_to_dc(domain: str) -> str:
    """
    Convert domain name to LDAP DC format.

    Examples:
        omnia.test -> dc=omnia,dc=test
        omnia.test.cluster -> dc=omnia,dc=test,dc=cluster
        chola.test -> dc=chola,dc=test

    Args:
        domain: Domain name (e.g., omnia.test, chola.test)

    Returns:
        DC string (e.g., dc=omnia,dc=test)
    """
    parts = domain.split(".")
    return ",".join(f"dc={part}" for part in parts)


def get_oim_domain(host) -> str:
    """
    Get OIM domain name from the OIM server hostname.

    Example: cholacp.chola.test -> chola.test
    """
    cmd = run_on_oim(host, "hostname -f")
    if cmd.rc != 0:
        return ""

    hostname = cmd.stdout.strip()
    parts = hostname.split(".")

    # Remove machine name (first part) to get domain
    # e.g., cholacp.chola.test -> chola.test
    if len(parts) > 2:
        return ".".join(parts[1:])
    return hostname


def get_ldap_credentials(host) -> Dict[str, Any]:
    """
    Get LDAP credentials from omnia_config_credentials.yml.

    Uses core secrets module to handle encrypted/decrypted files.

    Returns:
        Dict with success, openldap_db_username, openldap_db_password, error
    """
    result = get_multiple_credentials(
        host,
        OMNIA_CREDENTIALS_PATH,
        OMNIA_CREDENTIALS_KEY_PATH,
        ["openldap_db_username", "openldap_db_password"]
    )

    if not result["success"]:
        return {
            "success": False,
            "openldap_db_username": "",
            "openldap_db_password": "",
            "error": result["error"],
        }

    return {
        "success": True,
        "openldap_db_username": result["values"]["openldap_db_username"],
        "openldap_db_password": result["values"]["openldap_db_password"],
        "error": "",
    }


def get_external_ldap_config() -> Dict[str, str]:
    """
    Get external LDAP configuration from local omnia_test_config.yml.

    Returns:
        Dict with external LDAP config values
    """
    config = load_omnia_test_config()
    return {
        "server_ip": config.get("external_ldap_server_ip", ""),
        "server_port": config.get("external_ldap_server_port", ""),
        "domain": config.get("external_ldap_domain", ""),
        "bind_username": config.get("external_ldap_bind_username", ""),
        "bind_password": config.get("external_ldap_bind_password", ""),
    }


def build_slapd_config(host) -> Dict[str, Any]:
    """
    Build complete slapd.conf configuration from OIM domain and user config.

    Returns:
        Dict with all slapd.conf values and any error
    """
    result = {
        "success": False,
        "config": {},
        "error": "",
    }

    # Get OIM domain
    oim_domain = get_oim_domain(host)
    if not oim_domain:
        result["error"] = "Failed to get OIM domain from hostname"
        return result

    # Get LDAP credentials from vault using core secrets module
    creds = get_ldap_credentials(host)
    if not creds["success"]:
        result["error"] = f"Failed to get LDAP credentials: {creds['error']}"
        return result

    # Get external LDAP config from local omnia_test_config.yml
    ext_config = get_external_ldap_config()

    # Validate required external fields
    required = ["server_ip", "server_port", "domain", "bind_username", "bind_password"]
    for field in required:
        if not ext_config.get(field):
            result["error"] = f"external_ldap_{field} not configured in omnia_test_config.yml"
            return result

    # Build DC from domain names
    local_dc = domain_to_dc(oim_domain)
    external_dc = domain_to_dc(ext_config["domain"])

    # Build complete config
    result["config"] = {
        "ldap_suffix": local_dc,
        "ldap_rootdn": f"cn={creds['openldap_db_username']},{local_dc}",
        "ldap_rootpw": creds["openldap_db_password"],
        "ldap_uri": (
            f"ldap://{ext_config['server_ip']}:{ext_config['server_port']}/{local_dc}"
        ),
        "ldap_suffixmassage_local": local_dc,
        "ldap_suffixmassage_remote": external_dc,
        "ldap_bind_dn": f"cn={ext_config['bind_username']},{external_dc}",
        "ldap_bind_credentials": ext_config["bind_password"],
        "ldap_server_ip": ext_config["server_ip"],
        "oim_domain": oim_domain,
        "external_domain": ext_config["domain"],
    }

    result["success"] = True
    return result


def generate_slapd_conf(config: Dict[str, str]) -> str:
    """
    Generate slapd.conf content from template using config values.

    Args:
        config: Dict with LDAP config values

    Returns:
        Generated slapd.conf content
    """
    return SLAPD_CONF_TEMPLATE.format(
        ldap_suffix=config["ldap_suffix"],
        ldap_rootdn=config["ldap_rootdn"],
        ldap_rootpw=config["ldap_rootpw"],
        ldap_uri=config["ldap_uri"],
        ldap_suffixmassage_local=config["ldap_suffixmassage_local"],
        ldap_suffixmassage_remote=config["ldap_suffixmassage_remote"],
        ldap_bind_dn=config["ldap_bind_dn"],
        ldap_bind_credentials=config["ldap_bind_credentials"],
    )


# =============================================================================
# LDAP SLAPD.CONF CONFIGURATION TEST
# =============================================================================

def apply_slapd_conf_and_verify(host) -> Dict[str, Any]:
    """
    Generate slapd.conf from template, apply it, and verify LDAP service.

    This test:
    1. Gets OIM hostname and builds local DC
    2. Gets LDAP password from omnia_config_credentials.yml (decrypted)
    3. Gets external LDAP config from omnia_test_config.yml
    4. Builds external DC from external hostname
    5. Generates slapd.conf from template
    6. Backs up existing slapd.conf
    7. Writes new slapd.conf to /opt/omnia/auth/slapd.conf
    8. Restarts omnia_auth container
    9. Waits for container to be stable (10 seconds)
    10. Verifies external LDAP server is accessible - FAILS if not accessible

    Returns:
        Dict with success, details, error
    """
    results = {
        "success": False,
        "details": "",
        "error": "",
    }

    details_lines = []

    # Step 1: Build complete slapd config
    config_result = build_slapd_config(host)
    if not config_result["success"]:
        results["error"] = config_result["error"]
        return results

    config = config_result["config"]

    details_lines.append(f"OIM domain: {config['oim_domain']}")
    details_lines.append(f"Local DC: {config['ldap_suffix']}")
    details_lines.append(f"External domain: {config['external_domain']}")
    details_lines.append(f"External DC: {config['ldap_suffixmassage_remote']}")
    details_lines.append(f"LDAP URI: {config['ldap_uri']}")

    # Step 2: Generate slapd.conf from template
    slapd_content = generate_slapd_conf(config)
    details_lines.append("✓ Generated slapd.conf from template")

    # Step 3: Backup existing slapd.conf inside omnia_core container
    backup_path = f"{SLAPD_CONF_PATH}.backup"
    cmd = run_in_container(host, f"cp {SLAPD_CONF_PATH} {backup_path}")
    if cmd.rc != 0:
        results["error"] = f"Failed to backup slapd.conf: {cmd.stderr}"
        results["details"] = "\n".join(details_lines)
        return results

    details_lines.append(f"✓ Backed up existing slapd.conf to {backup_path}")

    # Step 4: Write new slapd.conf inside omnia_core container (ONLY slapd.conf, no other changes)
    escaped_content = slapd_content.replace("'", "'\\''")
    cmd = run_in_container(host, f"bash -c \"echo '{escaped_content}' > {SLAPD_CONF_PATH}\"")
    if cmd.rc != 0:
        results["error"] = f"Failed to write new slapd.conf: {cmd.stderr}"
        results["details"] = "\n".join(details_lines)
        return results

    details_lines.append(f"✓ Applied new slapd.conf to {SLAPD_CONF_PATH}")

    # Step 5: Restart omnia_auth container
    cmd = run_on_oim(host, f"podman restart {LDAP_CONTAINER_NAME}")
    if cmd.rc != 0:
        results["error"] = f"Failed to restart container: {cmd.stderr}"
        results["details"] = "\n".join(details_lines)
        return results

    details_lines.append(f"✓ Restarted {LDAP_CONTAINER_NAME} container")

    # Step 6: Wait for container to be stable
    details_lines.append(f"→ Waiting {CONTAINER_STABLE_WAIT_SECONDS}s for container...")

    elapsed = 0
    container_running = False
    while elapsed < CONTAINER_STABLE_WAIT_SECONDS:
        time.sleep(CONTAINER_CHECK_INTERVAL)
        elapsed += CONTAINER_CHECK_INTERVAL

        cmd = run_on_oim(
            host,
            f"podman ps --filter name={LDAP_CONTAINER_NAME} "
            f"--filter status=running --format '{{{{.Names}}}}'"
        )

        if cmd.rc == 0 and LDAP_CONTAINER_NAME in cmd.stdout:
            container_running = True
            break

    if not container_running:
        results["error"] = (
            f"Container {LDAP_CONTAINER_NAME} not running after "
            f"{CONTAINER_STABLE_WAIT_SECONDS} seconds"
        )
        results["details"] = "\n".join(details_lines)
        return results

    details_lines.append(f"✓ Container {LDAP_CONTAINER_NAME} is running")

    # Step 7: Verify external LDAP server is accessible from omnia_auth container
    ldap_server_ip = config["ldap_server_ip"]
    ldap_port = config.get("ldap_port", "1389")
    ldapsearch_cmd = f"ldapsearch -x -H ldap://{ldap_server_ip}:{ldap_port} -b '' -s base 2>&1"
    cmd = run_on_oim(
        host,
        f"podman exec {LDAP_CONTAINER_NAME} {ldapsearch_cmd}"
    )

    if cmd.rc != 0:
        results["error"] = (
            f"LDAP server at {ldap_server_ip} is NOT accessible after restart. "
            f"Error: {cmd.stderr or cmd.stdout}"
        )
        results["details"] = "\n".join(details_lines)
        return results

    details_lines.append(f"✓ LDAP server at {ldap_server_ip} is accessible")

    results["success"] = True
    results["details"] = "\n".join(details_lines)
    return results


# =============================================================================
# LDAP USER LOGIN VERIFICATION
# =============================================================================

def parse_ldap_credentials(omnia_config: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Parse LDAP credentials from omnia_test_config.yml.

    Supports two formats:
    1. New format: ldap_credentials: "user1:pwd1,user2:pwd2"
    2. Legacy format: ldap_user: "user", ldap_password: "pwd"

    Returns:
        List of dicts with 'user' and 'password' keys
    """
    credentials = []

    # Try new format first: ldap_credentials: "user1:pwd1,user2:pwd2"
    ldap_creds_str = omnia_config.get("ldap_credentials", "")
    if ldap_creds_str:
        for cred in ldap_creds_str.split(","):
            cred = cred.strip()
            if ":" in cred:
                parts = cred.split(":", 1)
                credentials.append({
                    "user": parts[0].strip(),
                    "password": parts[1].strip(),
                })

    # Fall back to legacy format if no new format found
    if not credentials:
        ldap_user = omnia_config.get("ldap_user", "")
        ldap_password = omnia_config.get("ldap_password", "")
        if ldap_user and ldap_password:
            credentials.append({
                "user": ldap_user,
                "password": ldap_password,
            })

    return credentials


def _verify_ldap_user_login(host, run_func) -> Dict[str, Any]:
    """
    Verify LDAP users can SSH login to Slurm nodes.

    Generic function — run_func determines where SSH originates:
      - run_on_oim: SSH from OIM host
      - run_in_container: SSH from omnia_core container

    Tests slurm_control_node, login_node, login_compiler_node.
    Note: slurm_node blocked by PAM (tested separately).

    Args:
        host: Testinfra host object
        run_func: Function to execute commands (run_on_oim or run_in_container)

    Returns:
        Dict with success, results_by_group, ldap_users, error
    """
    from .common_func import (
        get_slurm_control_nodes,
        get_login_nodes,
        get_login_compiler_nodes,
    )

    results = {
        "success": False,
        "results_by_group": {},
        "ldap_users": [],
        "error": "",
    }

    omnia_test_config = load_omnia_test_config()
    if not omnia_test_config:
        results["error"] = "Failed to load omnia_test_config.yml"
        return results

    credentials = parse_ldap_credentials(omnia_test_config)
    if not credentials:
        results["error"] = "ldap_credentials not set in omnia_test_config.yml"
        return results

    results["ldap_users"] = [c["user"] for c in credentials]

    all_nodes = (
        get_slurm_control_nodes(host)
        + get_login_nodes(host)
        + get_login_compiler_nodes(host)
    )
    if not all_nodes:
        results["error"] = "No slurm_control_node, login_node or login_compiler_node in PXE mapping"
        return results

    all_success = True
    for node in all_nodes:
        hostname = node.get("hostname", "")
        admin_ip = node.get("admin_ip", "")
        func_group = node.get("functional_group", "unknown")

        if func_group not in results["results_by_group"]:
            results["results_by_group"][func_group] = []

        node_result = {
            "hostname": hostname,
            "admin_ip": admin_ip,
            "success": True,
            "user_results": [],
        }

        for cred in credentials:
            ldap_user = cred["user"]
            ldap_password = cred["password"]

            user_result = {"user": ldap_user, "success": False, "message": ""}

            ssh_cmd = (
                f"sshpass -p '{ldap_password}' ssh -o StrictHostKeyChecking=no "
                f"-o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 "
                f"{ldap_user}@{admin_ip} 'echo LOGIN_SUCCESS' 2>&1"
            )
            cmd = run_func(host, ssh_cmd)

            if cmd.rc == 0 and "LOGIN_SUCCESS" in cmd.stdout:
                user_result["success"] = True
                user_result["message"] = "Login successful"
            else:
                node_result["success"] = False
                all_success = False
                output = (cmd.stdout or "") + (cmd.stderr or "")
                user_result["message"] = parse_ssh_error(output)

            node_result["user_results"].append(user_result)

        results["results_by_group"][func_group].append(node_result)

    results["success"] = all_success
    if not all_success:
        failed = [
            f"{ur['user']}@{n['hostname']}"
            for nodes_list in results["results_by_group"].values()
            for n in nodes_list if not n["success"]
            for ur in n["user_results"] if not ur["success"]
        ]
        results["error"] = f"LDAP login failed: {', '.join(failed)}"

    return results


def verify_ldap_user_login_from_oim(host) -> Dict[str, Any]:
    """Verify LDAP users can SSH login to Slurm nodes from OIM."""
    return _verify_ldap_user_login(host, run_on_oim)


def verify_ldap_user_login_from_core(host) -> Dict[str, Any]:
    """Verify LDAP users can SSH login to Slurm nodes from omnia_core container."""
    return _verify_ldap_user_login(host, run_in_container)


def verify_pam_slurm_adopt(host) -> Dict[str, Any]:
    """
    Verify PAM slurm_adopt behavior on slurm_node.

    PAM slurm_adopt is default behavior on slurm_node - LDAP users cannot login
    unless they have an active job running.

    Expected behavior: SSH login should fail with "Access denied by pam_slurm_adopt"

    Returns:
        Dict with success, results_by_group, ldap_users, error
    """
    from .common_func import get_slurm_compute_nodes

    results = {
        "success": False,
        "results_by_group": {},
        "ldap_users": [],
        "error": "",
    }

    # Get LDAP credentials from omnia_test_config.yml
    omnia_test_config = load_omnia_test_config()
    if not omnia_test_config:
        results["error"] = "Failed to load omnia_test_config.yml"
        return results

    credentials = parse_ldap_credentials(omnia_test_config)
    if not credentials:
        results["error"] = "ldap_credentials not set in omnia_test_config.yml"
        return results

    # For PAM test, use only the first user (PAM behavior is the same for all users)
    ldap_user = credentials[0]["user"]
    ldap_password = credentials[0]["password"]
    results["ldap_users"] = [ldap_user]

    # Get slurm compute nodes
    slurm_nodes = get_slurm_compute_nodes(host)
    if not slurm_nodes:
        results["error"] = "No slurm_node in PXE mapping"
        return results

    # Test SSH login - should FAIL with PAM message
    all_correct = True
    for node in slurm_nodes:
        hostname = node.get("hostname", "")
        admin_ip = node.get("admin_ip", "")
        func_group = node.get("functional_group", "unknown")

        if func_group not in results["results_by_group"]:
            results["results_by_group"][func_group] = []

        node_result = {
            "hostname": hostname,
            "admin_ip": admin_ip,
            "success": False,
            "login_blocked": False,
            "message": "",
        }

        # SSH login using sshpass - should be blocked by PAM
        ssh_cmd = (
            f"sshpass -p '{ldap_password}' ssh -o StrictHostKeyChecking=no "
            f"-o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 "
            f"{ldap_user}@{admin_ip} 'echo LOGIN_SUCCESS' 2>&1"
        )
        cmd = run_on_oim(host, ssh_cmd)

        output = (cmd.stdout or "") + (cmd.stderr or "")

        # PAM blocks login - check for "Access denied by pam_slurm_adopt" or "no active jobs"
        if "pam_slurm_adopt" in output or "no active jobs" in output.lower():
            node_result["success"] = True
            node_result["login_blocked"] = True
            node_result["message"] = "Access denied by pam_slurm_adopt: you have no active jobs on this node"
        elif "Connection closed" in output and cmd.rc != 0:
            # Connection closed after PAM denial
            node_result["success"] = True
            node_result["login_blocked"] = True
            node_result["message"] = "Login blocked by PAM (connection closed)"
        elif cmd.rc == 0 and "LOGIN_SUCCESS" in output:
            # Login succeeded - PAM not working
            node_result["message"] = "Login succeeded but should have been blocked by PAM"
            all_correct = False
        else:
            # Some other error
            node_result["message"] = f"Unexpected response: {output.strip()[:100]}"
            all_correct = False

        results["results_by_group"][func_group].append(node_result)

    results["success"] = all_correct
    if not all_correct:
        results["error"] = "PAM slurm_adopt not working correctly on some nodes"

    return results


def verify_pam_slurm_adopt_session_termination(host) -> Dict[str, Any]:
    """
    Verify PAM slurm_adopt session termination behavior.

    Submits jobs from ALL submit nodes (slurm_control_node, login_node, login_compiler_node)
    and verifies for each:
    1. LDAP user can login during active job (session adopted)
    2. LDAP user login is blocked after job ends (auto-logout)

    Returns:
        Dict with success, details, error, results_by_submit_node
    """
    import os
    import base64

    results = {
        "success": False,
        "details": "",
        "error": "",
        "results_by_submit_node": {},
        "ldap_users": [],
    }

    # Get LDAP credentials from omnia_test_config.yml
    omnia_test_config = load_omnia_test_config()
    if not omnia_test_config:
        results["error"] = "Failed to load omnia_test_config.yml"
        return results

    credentials = parse_ldap_credentials(omnia_test_config)
    if not credentials:
        results["error"] = "ldap_credentials not set in omnia_test_config.yml"
        return results

    ldap_user = credentials[0]["user"]
    ldap_password = credentials[0]["password"]
    results["ldap_users"] = [ldap_user]

    # Collect all nodes per type (all slurm_control_node, login_node, login_compiler_node)
    submit_nodes_by_type = {}
    control_nodes = get_slurm_control_nodes(host)
    if control_nodes:
        submit_nodes_by_type["slurm_control_node"] = control_nodes
    login_nodes = get_login_nodes(host)
    if login_nodes:
        submit_nodes_by_type["login_node"] = login_nodes
    lc_nodes = get_login_compiler_nodes(host)
    if lc_nodes:
        submit_nodes_by_type["login_compiler_node"] = lc_nodes

    if not submit_nodes_by_type:
        results["error"] = (
            "No slurm_control_node, login_node, or "
            "login_compiler_node in PXE mapping"
        )
        return results

    compute_nodes = get_slurm_compute_nodes(host)
    if not compute_nodes:
        results["error"] = "No slurm_node in PXE mapping"
        return results

    # Build hostname -> admin_ip lookup for compute nodes
    compute_node_map = {
        n.get("hostname", ""): n.get("admin_ip", "")
        for n in compute_nodes
    }

    details_lines = [
        f"LDAP user: {ldap_user}",
        f"Available compute nodes: {', '.join(compute_node_map.keys())}",
    ]

    # ── Read job.sh from vars/ ──
    job_sh_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "vars", "job.sh",
    )
    try:
        with open(job_sh_path, "r", encoding="utf-8") as f:
            job_sh_content = f.read()
    except FileNotFoundError:
        results["error"] = f"job.sh not found at {job_sh_path}"
        results["details"] = "\n".join(details_lines)
        return results

    encoded = base64.b64encode(job_sh_content.encode()).decode()
    _ssh = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    SSH_OPTS = (
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/dev/null "
        "-o ConnectTimeout=10"
    )

    # ── Loop through all submit nodes ──
    all_success = True
    for node_type, nodes in submit_nodes_by_type.items():
        for submit_node in nodes:
            submit_ip = submit_node.get("admin_ip", "")
            submit_hostname = submit_node.get("hostname", "")

            details_lines.append("")
            details_lines.append(f"=== Testing from {node_type}: {submit_hostname} (IP: {submit_ip}) ===")

            node_result = {
                "node_type": node_type,
                "hostname": submit_hostname,
                "admin_ip": submit_ip,
                "success": False,
                "job_id": "",
                "login_during_job": False,
                "login_during_job_message": "",
                "session_terminated_after_job": False,
                "post_job_block_message": "",
                "error": "",
            }

            # Copy job.sh to ldapuser's home directory on the submit node
            copy_cmd = (
                f"echo '{encoded}' | base64 -d > /home/{ldap_user}/job.sh && "
                f"chmod 755 /home/{ldap_user}/job.sh && "
                f"echo COPY_OK"
            )
            cmd = run_on_remote_node(host, copy_cmd, submit_ip)
            if "COPY_OK" not in (cmd.stdout or ""):
                node_result["error"] = f"Failed to copy job.sh: {(cmd.stdout or '').strip()}"
                results["results_by_submit_node"][submit_hostname] = node_result
                all_success = False
                details_lines.append(f"  ✗ Copy job.sh failed: {node_result['error']}")
                continue

            details_lines.append(f"  ✓ Copied job.sh to {submit_hostname}:/home/{ldap_user}/job.sh")

            # Submit job as ldapuser using sbatch --uid (no -w: let Slurm assign any compute node)
            submit_ssh = (
                f'ssh {_ssh} root@{submit_ip} '
                f'"sbatch --uid={ldap_user} '
                f'-D /home/{ldap_user} --output=/home/{ldap_user}/slurm_%j.out --error=/home/{ldap_user}/slurm_%j.err '
                f'/home/{ldap_user}/job.sh" 2>&1'
            )
            cmd = run_in_container(host, submit_ssh)
            output = ((cmd.stdout or "") + (cmd.stderr or "")).strip()

            job_id = ""
            if "Submitted batch job" in output:
                for part in output.split("\n"):
                    if "Submitted batch job" in part:
                        job_id = part.strip().split()[-1]
                        break
            else:
                node_result["error"] = f"Job submission failed: {output}"
                results["results_by_submit_node"][submit_hostname] = node_result
                all_success = False
                details_lines.append(f"  ✗ Job submission failed: {node_result['error']}")
                continue

            node_result["job_id"] = job_id
            details_lines.append(f"  ✓ Submitted job ID: {job_id} (as {ldap_user})")

            # Wait for job to start RUNNING and detect which compute node it's on (max 30s)
            job_running = False
            job_state = ""
            actual_compute_hostname = ""
            actual_compute_ip = ""
            for _ in range(15):
                time.sleep(2)
                sq_ssh = (
                    f'ssh {_ssh} root@{submit_ip} '
                    f'"squeue -j {job_id} -h -o \"%T %N\"" 2>&1'
                )
                cmd = run_in_container(host, sq_ssh)
                raw = (cmd.stdout or "").strip()
                lines = [
                    l.strip() for l in raw.splitlines()
                    if l.strip() and not l.startswith("Warning:") and "known hosts" not in l
                ]
                last_line = lines[-1] if lines else ""
                parts = last_line.split()
                job_state = parts[0] if parts else ""
                if job_state == "RUNNING" and len(parts) >= 2:
                    actual_compute_hostname = parts[1]
                    actual_compute_ip = compute_node_map.get(actual_compute_hostname, "")
                    job_running = True
                    break

            if not job_running:
                node_result["error"] = f"Job did not reach RUNNING: '{job_state}'"
                results["results_by_submit_node"][submit_hostname] = node_result
                all_success = False
                details_lines.append(f"  ✗ Job state: {node_result['error']}")
                continue

            if not actual_compute_ip:
                # hostname from squeue may be short; try partial match
                for chost, cip in compute_node_map.items():
                    if actual_compute_hostname in chost or chost in actual_compute_hostname:
                        actual_compute_ip = cip
                        actual_compute_hostname = chost
                        break

            if not actual_compute_ip:
                node_result["error"] = (
                    f"Cannot find IP for compute node '{actual_compute_hostname}' in PXE mapping"
                )
                results["results_by_submit_node"][submit_hostname] = node_result
                all_success = False
                details_lines.append(f"  ✗ {node_result['error']}")
                continue

            node_result["compute_hostname"] = actual_compute_hostname
            node_result["compute_ip"] = actual_compute_ip
            details_lines.append(f"  ✓ Job {job_id}: RUNNING on {actual_compute_hostname} (IP: {actual_compute_ip})")

            # Login to the actual compute node as ldapuser during active job
            login_cmd = (
                f"sshpass -p '{ldap_password}' ssh {SSH_OPTS} "
                f"{ldap_user}@{actual_compute_ip} 'echo LOGIN_SUCCESS' 2>&1"
            )
            cmd = run_on_oim(host, login_cmd)
            login_output = ((cmd.stdout or "") + (cmd.stderr or "")).strip()

            login_msg_lines = [
                line for line in login_output.splitlines()
                if not line.startswith("Warning:") and "known hosts" not in line
            ]
            clean_login_msg = "\n".join(login_msg_lines).strip()

            if "LOGIN_SUCCESS" in login_output:
                node_result["login_during_job"] = True
                node_result["login_during_job_message"] = "Login allowed (session adopted)"
                details_lines.append("  ✓ Login during job: ALLOWED (session adopted)")
            else:
                node_result["login_during_job"] = False
                node_result["login_during_job_message"] = clean_login_msg
                details_lines.append("  ✗ Login during job: BLOCKED - " + clean_login_msg[:100])

            # Wait for job to complete (job.sh sleeps 40s, max wait 90s)
            job_finished = False
            final_state = ""
            for _ in range(45):
                time.sleep(2)
                sq_ssh = (
                    f'ssh {_ssh} root@{submit_ip} '
                    f'"squeue -j {job_id} -h -o %T" 2>&1'
                )
                cmd = run_in_container(host, sq_ssh)
                raw = (cmd.stdout or "").strip()
                lines = [
                    l.strip() for l in raw.splitlines()
                    if l.strip() and not l.startswith("Warning:") and "known hosts" not in l
                ]
                state = lines[-1] if lines else ""
                if not state or state in ("COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"):
                    job_finished = True
                    final_state = state or "COMPLETED"
                    break
                final_state = state

            if not job_finished:
                run_in_container(host, f'ssh {_ssh} root@{submit_ip} "scancel {job_id}" 2>&1')
                node_result["error"] = f"Job timeout (last state: {final_state})"
                results["results_by_submit_node"][submit_hostname] = node_result
                all_success = False
                details_lines.append(f"  ✗ Job timeout: {node_result['error']}")
                continue

            details_lines.append(f"  ✓ Job completed with state: {final_state}")

            # Small delay for PAM to terminate adopted sessions
            time.sleep(5)

            # Try login as ldapuser after job ends → should be blocked
            cmd = run_on_oim(host, login_cmd)
            post_output = ((cmd.stdout or "") + (cmd.stderr or "")).strip()

            post_msg_lines = [
                line for line in post_output.splitlines()
                if not line.startswith("Warning:") and "known hosts" not in line
            ]
            clean_post_msg = "\n".join(post_msg_lines).strip()
            node_result["post_job_block_message"] = clean_post_msg

            if cmd.rc == 0 and "LOGIN_SUCCESS" in post_output:
                node_result["session_terminated_after_job"] = False
                details_lines.append(f"  ✗ Login after job: ALLOWED (should be blocked) - {clean_post_msg[:100]}")
            else:
                node_result["session_terminated_after_job"] = True
                details_lines.append(f"  ✓ Login after job: BLOCKED - {clean_post_msg[:100]}")

            node_result["success"] = node_result["session_terminated_after_job"]
            results["results_by_submit_node"][submit_hostname] = node_result

            if not node_result["success"]:
                all_success = False

    results["success"] = all_success
    results["details"] = "\n".join(details_lines)
    return results
