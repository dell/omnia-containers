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
OpenLDAP Module - Functions.

Functions for deploying Bitnami OpenLDAP container, creating LDAP users,
and verifying LDAP directory entries.
"""

import os
from typing import Any, Dict, List

import yaml

from automation_library.core import (
    run_on_oim,
)
from automation_library.openldap.vars import (
    OPENLDAP_CONTAINER_NAME,
    OPENLDAP_CONTAINER_IMAGE,
    OPENLDAP_LDAP_PORT,
    OPENLDAP_LDAPS_PORT,
    OPENLDAP_DEFAULT_ADMIN_USERNAME,
    OPENLDAP_DEFAULT_DOMAIN,
    OPENLDAP_DEFAULT_LOGIN_SHELL,
    OPENLDAP_DEFAULT_UID_START,
)


def _get_project_root() -> str:
    """Get the project root directory path."""
    # This file is in automation_library/openldap/functions/
    # Project root is 3 levels up
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))


def load_openldap_config() -> Dict[str, Any]:
    """
    Load OpenLDAP configuration from utility/openldap_config.yml.

    Returns:
        Dictionary with all OpenLDAP settings, defaults applied.
    """
    # Get project root and locate utility/openldap_config.yml
    project_root = _get_project_root()
    config_path = os.path.join(project_root, "utility", "openldap_config.yml")
    
    if not os.path.exists(config_path):
        return {
            # Target server (empty = localhost)
            "server_ip": "",
            "ssh_user": "root",
            "ssh_password": "",
            "ssh_port": 22,
            # LDAP settings
            "admin_username": OPENLDAP_DEFAULT_ADMIN_USERNAME,
            "admin_password": "",
            "domain": OPENLDAP_DEFAULT_DOMAIN,
            "image": OPENLDAP_CONTAINER_IMAGE,
            "container_name": OPENLDAP_CONTAINER_NAME,
            "ldap_port": OPENLDAP_LDAP_PORT,
            "ldaps_port": OPENLDAP_LDAPS_PORT,
            "users": [],
            "default_login_shell": OPENLDAP_DEFAULT_LOGIN_SHELL,
            "default_uid_start": OPENLDAP_DEFAULT_UID_START,
        }
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    
    return {
        # Target server (empty = localhost)
        "server_ip": config.get("openldap_server_ip", ""),
        "ssh_user": config.get("openldap_server_ssh_user", "root"),
        "ssh_password": config.get("openldap_server_ssh_password", ""),
        "ssh_port": int(config.get("openldap_server_ssh_port", 22)),
        # LDAP settings
        "admin_username": config.get("openldap_admin_username", OPENLDAP_DEFAULT_ADMIN_USERNAME),
        "admin_password": config.get("openldap_admin_password", ""),
        "domain": config.get("openldap_domain", OPENLDAP_DEFAULT_DOMAIN),
        "image": config.get("openldap_image", OPENLDAP_CONTAINER_IMAGE),
        "container_name": config.get("openldap_container_name", OPENLDAP_CONTAINER_NAME),
        "ldap_port": config.get("openldap_port", OPENLDAP_LDAP_PORT),
        "ldaps_port": config.get("openldap_secure_port", OPENLDAP_LDAPS_PORT),
        "users": config.get("openldap_users", []),
        "default_login_shell": config.get("openldap_default_login_shell", OPENLDAP_DEFAULT_LOGIN_SHELL),
        "default_uid_start": config.get("openldap_default_uid_start", OPENLDAP_DEFAULT_UID_START),
    }


def domain_to_dc(domain: str) -> str:
    """
    Convert a domain name to LDAP DC components.

    Args:
        domain: Domain name (e.g., "omnia.test")

    Returns:
        DC string (e.g., "dc=omnia,dc=test")
    """
    parts = domain.strip().split(".")
    return ",".join(f"dc={p}" for p in parts)


def validate_openldap_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate OpenLDAP configuration.

    Args:
        config: Configuration dictionary from load_openldap_config()

    Returns:
        Dictionary with keys: success (bool), errors (list of str)
    """
    errors: List[str] = []

    if not config.get("admin_password"):
        errors.append("openldap_admin_password is required but empty")

    domain = config.get("domain", "")
    if not domain or "." not in domain:
        errors.append(f"openldap_domain must be a valid domain (e.g., 'omnia.test'), got: '{domain}'")

    # Remote mode requires SSH password
    server_ip = (config.get("server_ip") or "").strip()
    if server_ip and server_ip not in ("localhost", "127.0.0.1"):
        if not config.get("ssh_password"):
            errors.append("openldap_server_ssh_password is required when openldap_server_ip is set")

    users = config.get("users", [])
    if not users:
        errors.append("openldap_users list is empty — at least one user is required")
    else:
        for i, user in enumerate(users):
            if not isinstance(user, dict):
                errors.append(f"openldap_users[{i}] must be a dictionary, got: {type(user).__name__}")
                continue
            if not user.get("username"):
                errors.append(f"openldap_users[{i}].username is required but empty")
            if not user.get("password"):
                errors.append(f"openldap_users[{i}].password is required but empty")

    return {
        "success": len(errors) == 0,
        "errors": errors,
    }


def check_openldap_container(host, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if the OpenLDAP container is running.

    Args:
        host: Testinfra host connected to OIM server
        config: OpenLDAP configuration dictionary

    Returns:
        Dictionary with keys: success, error, details
    """
    container_name = config.get("container_name", OPENLDAP_CONTAINER_NAME)
    result = run_on_oim(
        host,
        f"podman ps --filter name=^{container_name}$ --format '{{{{.Status}}}}'"
    )
    stdout = result.stdout.strip() if result.stdout else ""

    if result.rc != 0 or not stdout:
        return {
            "success": False,
            "error": f"Container '{container_name}' is not running",
            "details": result.stderr.strip() if result.stderr else "No output",
        }

    return {
        "success": "Up" in stdout,
        "error": "" if "Up" in stdout else f"Container status: {stdout}",
        "details": f"Container '{container_name}' status: {stdout}",
    }


def check_ldap_ou_exists(
    host,
    config: Dict[str, Any],
    ou_name: str,
) -> Dict[str, Any]:
    """
    Check if an organizational unit exists in LDAP.

    Args:
        host: Testinfra host connected to OIM server
        config: OpenLDAP configuration dictionary
        ou_name: Name of the organizational unit (e.g., "People")

    Returns:
        Dictionary with keys: success, error, details
    """
    container_name = config.get("container_name", OPENLDAP_CONTAINER_NAME)
    base_dn = domain_to_dc(config["domain"])
    admin_password = config["admin_password"]
    ldap_port = config.get("ldap_port", OPENLDAP_LDAP_PORT)

    cmd = (
        f"podman exec {container_name} ldapsearch -x "
        f"-H ldap://localhost:1389 "
        f"-D \"cn=admin,{base_dn}\" -w {admin_password} "
        f"-b \"ou={ou_name},{base_dn}\" -s base \"(objectClass=organizationalUnit)\" dn"
    )
    result = run_on_oim(host, cmd)
    stdout = result.stdout.strip() if result.stdout else ""

    found = f"ou={ou_name},{base_dn}" in stdout

    return {
        "success": found,
        "error": "" if found else f"OU '{ou_name}' not found under {base_dn}",
        "details": f"ou={ou_name},{base_dn}" if found else stdout,
    }


def check_ldap_user_exists(
    host,
    config: Dict[str, Any],
    username: str,
) -> Dict[str, Any]:
    """
    Check if an LDAP user exists in the directory.

    Args:
        host: Testinfra host connected to OIM server
        config: OpenLDAP configuration dictionary
        username: LDAP username to check

    Returns:
        Dictionary with keys: success, error, details, attributes (dict of found attrs)
    """
    container_name = config.get("container_name", OPENLDAP_CONTAINER_NAME)
    base_dn = domain_to_dc(config["domain"])
    admin_password = config["admin_password"]

    cmd = (
        f"podman exec {container_name} ldapsearch -x "
        f"-H ldap://localhost:1389 "
        f"-D \"cn=admin,{base_dn}\" -w {admin_password} "
        f"-b \"ou=People,{base_dn}\" \"(uid={username})\" "
        f"uid uidNumber gidNumber loginShell homeDirectory cn sn"
    )
    result = run_on_oim(host, cmd)
    stdout = result.stdout.strip() if result.stdout else ""

    found = f"uid={username}" in stdout

    # Parse attributes from ldapsearch output
    attributes: Dict[str, str] = {}
    if found:
        for line in stdout.splitlines():
            line = line.strip()
            if ": " in line and not line.startswith("#"):
                key, _, val = line.partition(": ")
                attributes[key.strip()] = val.strip()

    return {
        "success": found,
        "error": "" if found else f"User '{username}' not found under ou=People,{base_dn}",
        "details": f"uid={username},ou=People,{base_dn}" if found else stdout,
        "attributes": attributes,
    }


def check_ldap_group_exists(
    host,
    config: Dict[str, Any],
    group_name: str,
) -> Dict[str, Any]:
    """
    Check if an LDAP group exists in the directory.

    Args:
        host: Testinfra host connected to OIM server
        config: OpenLDAP configuration dictionary
        group_name: LDAP group name to check

    Returns:
        Dictionary with keys: success, error, details
    """
    container_name = config.get("container_name", OPENLDAP_CONTAINER_NAME)
    base_dn = domain_to_dc(config["domain"])
    admin_password = config["admin_password"]

    cmd = (
        f"podman exec {container_name} ldapsearch -x "
        f"-H ldap://localhost:1389 "
        f"-D \"cn=admin,{base_dn}\" -w {admin_password} "
        f"-b \"ou=groups,{base_dn}\" \"(cn={group_name})\" cn gidNumber memberUid"
    )
    result = run_on_oim(host, cmd)
    stdout = result.stdout.strip() if result.stdout else ""

    found = f"cn={group_name}" in stdout

    return {
        "success": found,
        "error": "" if found else f"Group '{group_name}' not found under ou=groups,{base_dn}",
        "details": f"cn={group_name},ou=groups,{base_dn}" if found else stdout,
    }
