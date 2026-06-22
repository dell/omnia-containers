#!/usr/bin/env python3
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
Create LDAP Users — Automated OpenLDAP Setup Utility

Deploys a Bitnami OpenLDAP container and creates LDAP users with POSIX
attributes automatically. Reads all inputs from utility/openldap_config.yml.

Supports two modes:
  - LOCAL:  openldap_server_ip is empty → runs podman/ldap commands locally
  - REMOTE: openldap_server_ip is set  → runs commands on remote server via SSH

Usage:
    python utility/create_ldap_user.py
    python utility/create_ldap_user.py --config /path/to/openldap_config.yml

Steps performed:
    1. Validate configuration
    2. Pull and run Bitnami OpenLDAP container (podman)
    3. Wait for LDAP service readiness
    4. Create organizational units (ou=People, ou=groups)
    5. Create each user with POSIX attributes (LDIF)
    6. Create each user's group (LDIF)
    7. Set user passwords
    8. Verify all users via ldapsearch
"""

import argparse
import os
import subprocess
import sys
import time

import paramiko
import yaml


# =============================================================================
# COLOURS AND FORMATTING
# =============================================================================

class _C:
    """Terminal colour codes."""
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    CYAN = "\033[0;36m"
    BOLD = "\033[1m"
    NC = "\033[0m"


def info(msg: str) -> None:
    """Print an info message."""
    print(f"{_C.CYAN}[INFO]{_C.NC}  {msg}")


def success(msg: str) -> None:
    """Print a success message."""
    print(f"{_C.GREEN}[OK]{_C.NC}    {msg}")


def warn(msg: str) -> None:
    """Print a warning message."""
    print(f"{_C.YELLOW}[WARN]{_C.NC}  {msg}")


def error(msg: str) -> None:
    """Print an error message to stderr."""
    print(f"{_C.RED}[ERROR]{_C.NC} {msg}", file=sys.stderr)


def die(msg: str) -> None:
    """Print an error and exit."""
    error(msg)
    sys.exit(1)


# =============================================================================
# COMMAND RUNNER (local / remote)
# =============================================================================

class CommandRunner:
    """
    Executes shell commands either locally or on a remote server via SSH.

    Args:
        server_ip: Remote server IP. Empty or None for local execution.
        ssh_user: SSH username for remote server.
        ssh_password: SSH password for remote server.
        ssh_port: SSH port (default 22).
    """

    def __init__(
        self,
        server_ip: str = "",
        ssh_user: str = "root",
        ssh_password: str = "",
        ssh_port: int = 22,
    ):
        self.server_ip = (server_ip or "").strip()
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.ssh_port = ssh_port
        self.is_local = not self.server_ip or self.server_ip in ("localhost", "127.0.0.1")
        self._client = None

    @property
    def target_label(self) -> str:
        """Human-readable target label."""
        return "localhost" if self.is_local else self.server_ip

    def _get_ssh_client(self) -> paramiko.SSHClient:
        """Get or create SSH client connection."""
        if self._client is not None:
            # Check if transport is still active
            transport = self._client.get_transport()
            if transport and transport.is_active():
                return self._client
            self._client = None

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=self.server_ip,
                port=self.ssh_port,
                username=self.ssh_user,
                password=self.ssh_password,
                timeout=30,
                allow_agent=False,
                look_for_keys=False,
            )
        except Exception as exc:
            die(
                f"SSH connection to {self.server_ip}:{self.ssh_port} failed: {exc}\n"
                f"  Check openldap_server_ip, openldap_server_ssh_user, "
                f"openldap_server_ssh_password in omnia_test_config.yml"
            )
        self._client = client
        return client

    def run(self, cmd: str, check: bool = False, no_log: bool = False) -> subprocess.CompletedProcess:
        """
        Run a shell command locally or on the remote server.

        Args:
            cmd: Shell command string to execute.
            check: If True, raise on non-zero exit code.
            no_log: If True, suppress the command from log output.

        Returns:
            CompletedProcess-like object with stdout, stderr, returncode.
        """
        if self.is_local:
            return self._run_local(cmd, check=check)
        return self._run_remote(cmd, check=check)

    def _run_local(self, cmd: str, check: bool = False) -> subprocess.CompletedProcess:
        """Run command locally."""
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=120
        )
        if check and result.returncode != 0:
            die(f"Command failed (rc={result.returncode}): {cmd}\n{result.stderr}")
        return result

    def _run_remote(self, cmd: str, check: bool = False) -> subprocess.CompletedProcess:
        """Run command on remote server via SSH."""
        client = self._get_ssh_client()
        try:
            _, stdout_ch, stderr_ch = client.exec_command(cmd, timeout=120)
            stdout = stdout_ch.read().decode("utf-8", errors="replace")
            stderr = stderr_ch.read().decode("utf-8", errors="replace")
            rc = stdout_ch.channel.recv_exit_status()
        except Exception as exc:
            die(f"SSH command execution failed: {exc}\nCommand: {cmd}")
            return subprocess.CompletedProcess(cmd, 1, "", str(exc))  # unreachable

        result = subprocess.CompletedProcess(cmd, rc, stdout, stderr)
        if check and rc != 0:
            die(f"Remote command failed (rc={rc}): {cmd}\n{stderr}")
        return result

    def close(self) -> None:
        """Close SSH connection if open."""
        if self._client:
            self._client.close()
            self._client = None


# =============================================================================
# CONFIGURATION
# =============================================================================

def _find_config_file(config_path: str = "") -> str:
    """Locate openldap_config.yml."""
    if config_path and os.path.isfile(config_path):
        return config_path

    # Try relative to this script (utility directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "openldap_config.yml"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    die(
        "openldap_config.yml not found in utility directory.\n"
        "  Looked in: " + ", ".join(candidates) + "\n"
        "  Use --config to specify the path."
    )
    return ""  # unreachable


def load_config(config_path: str = "") -> dict:
    """Load and return the OpenLDAP configuration from openldap_config.yml."""
    path = _find_config_file(config_path)
    info(f"Loading config from: {path}")

    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    return {
        # Target server
        "server_ip": raw.get("openldap_server_ip", ""),
        "ssh_user": raw.get("openldap_server_ssh_user", "root"),
        "ssh_password": raw.get("openldap_server_ssh_password", ""),
        "ssh_port": int(raw.get("openldap_server_ssh_port", 22)),
        # LDAP settings
        "admin_username": raw.get("openldap_admin_username", "admin"),
        "admin_password": raw.get("openldap_admin_password", ""),
        "domain": raw.get("openldap_domain", "omnia.test"),
        "image": raw.get("openldap_image", "docker.io/bitnamilegacy/openldap:latest"),
        "container_name": raw.get("openldap_container_name", "openldap"),
        "ldap_port": int(raw.get("openldap_port", 1389)),
        "ldaps_port": int(raw.get("openldap_secure_port", 1636)),
        "users": raw.get("openldap_users", []),
        "default_login_shell": raw.get("openldap_default_login_shell", "/bin/bash"),
        "default_uid_start": int(raw.get("openldap_default_uid_start", 2000)),
    }


def domain_to_dc(domain: str) -> str:
    """Convert 'omnia.test' -> 'dc=omnia,dc=test'."""
    return ",".join(f"dc={p}" for p in domain.strip().split("."))


def validate_config(cfg: dict) -> None:
    """Validate required fields and exit on error."""
    errors = []

    if not cfg.get("admin_password"):
        errors.append("openldap_admin_password is required but empty")

    # Remote mode requires SSH password
    server_ip = (cfg.get("server_ip") or "").strip()
    if server_ip and server_ip not in ("localhost", "127.0.0.1"):
        if not cfg.get("ssh_password"):
            errors.append(
                "openldap_server_ssh_password is required when openldap_server_ip is set"
            )

    users = cfg.get("users") or []
    if not users:
        errors.append("openldap_users list is empty — at least one user is required")
    else:
        for i, user in enumerate(users):
            if not isinstance(user, dict):
                errors.append(f"openldap_users[{i}] must be a mapping, got {type(user).__name__}")
                continue
            if not user.get("username"):
                errors.append(f"openldap_users[{i}].username is required")
            if not user.get("password"):
                errors.append(f"openldap_users[{i}].password is required")

    if errors:
        die(
            "Configuration errors in openldap_config.yml:\n  - "
            + "\n  - ".join(errors)
        )


# =============================================================================
# LDAP OPERATIONS
# =============================================================================

def fetch_domain_from_server(runner: CommandRunner) -> str:
    """
    Fetch the FQDN (domain name) from the server.

    Returns:
        Domain name (e.g., "omnia.test")
    """
    info("Fetching domain name from server ...")
    result = runner.run("hostname -f")
    if result.returncode != 0 or not result.stdout.strip():
        warn("Could not fetch FQDN from server, trying hostname ...")
        result = runner.run("hostname")
    
    hostname = result.stdout.strip()
    if not hostname:
        warn("Could not determine domain name from server, using default 'omnia.test'")
        return "omnia.test"
    
    # If hostname is just a short name without dots, return default
    if "." not in hostname:
        warn(f"Server hostname '{hostname}' has no domain, using default 'omnia.test'")
        return "omnia.test"
    
    # Extract domain part from FQDN (e.g., "pmo.omnia.test" -> "omnia.test")
    # Take the last two parts for the domain
    parts = hostname.split(".")
    if len(parts) >= 2:
        domain = ".".join(parts[-2:])
        info(f"Detected domain: {domain}")
        return domain
    
    return "omnia.test"

def deploy_openldap_container(runner: CommandRunner, cfg: dict, base_dn: str) -> None:
    """Pull and start the Bitnami OpenLDAP container, removing any existing deployment."""
    cname = cfg["container_name"]
    vname = "openldap_data"

    info(f"Checking for existing container '{cname}' ...")
    result = runner.run(f"podman ps -a --filter name=^{cname}$ --format '{{{{.Status}}}}'")
    status = result.stdout.strip()

    # Remove existing container if it exists
    if status:
        info(f"Removing existing container '{cname}' ({status}) ...")
        runner.run(f"podman rm -f {cname}")

    # Remove existing volume to ensure fresh data with correct credentials
    info(f"Checking for existing volume '{vname}' ...")
    result = runner.run(f"podman volume ls -q --filter name=^{vname}$")
    if result.stdout.strip():
        info(f"Removing existing volume '{vname}' to ensure fresh credentials ...")
        runner.run(f"podman volume rm {vname}")

    info(f"Pulling and starting OpenLDAP container '{cname}' ...")
    run_cmd = (
        f"podman run -d --name {cname} "
        f"-p 0.0.0.0:{cfg['ldap_port']}:1389 "
        f"-p 0.0.0.0:{cfg['ldaps_port']}:1636 "
        f"-e LDAP_ADMIN_USERNAME={cfg['admin_username']} "
        f"-e LDAP_ADMIN_PASSWORD={cfg['admin_password']} "
        f"-e LDAP_ROOT={base_dn} "
        f"-v {vname}:/bitnami/openldap "
        f"{cfg['image']}"
    )
    result = runner.run(run_cmd)
    if result.returncode != 0:
        die(f"Failed to start container: {result.stderr}")
    success(f"Container '{cname}' started.")


def wait_for_ldap_ready(runner: CommandRunner, cfg: dict, base_dn: str, timeout: int = 60) -> None:
    """Wait until the LDAP service inside the container is accepting queries."""
    cname = cfg["container_name"]
    admin_dn = f"cn={cfg['admin_username']},{base_dn}"
    info(f"Waiting for LDAP service to be ready (timeout {timeout}s) ...")

    for attempt in range(1, timeout // 2 + 1):
        check_cmd = (
            f"podman exec {cname} ldapsearch -x -H ldap://localhost:1389 "
            f"-D \"{admin_dn}\" -w {cfg['admin_password']} "
            f"-b \"{base_dn}\" -s base \"(objectClass=*)\" dn"
        )
        result = runner.run(check_cmd)
        if result.returncode == 0 and "dn:" in result.stdout:
            success(f"LDAP service is ready (attempt {attempt}).")
            return
        time.sleep(2)

    die(f"LDAP service not ready after {timeout}s. Check: podman logs {cname}")


def ensure_ou(runner: CommandRunner, cfg: dict, base_dn: str, ou_name: str) -> None:
    """Create an organizational unit if it does not exist."""
    cname = cfg["container_name"]
    admin_dn = f"cn={cfg['admin_username']},{base_dn}"

    check_cmd = (
        f"podman exec {cname} ldapsearch -x -H ldap://localhost:1389 "
        f"-D \"{admin_dn}\" -w {cfg['admin_password']} "
        f"-b \"ou={ou_name},{base_dn}\" -s base \"(objectClass=organizationalUnit)\" dn"
    )
    result = runner.run(check_cmd)
    if result.returncode == 0 and f"ou={ou_name}" in result.stdout:
        info(f"OU '{ou_name}' already exists.")
        return

    info(f"Creating OU: ou={ou_name},{base_dn} ...")
    ldif = (
        f"dn: ou={ou_name},{base_dn}\n"
        f"objectClass: top\n"
        f"objectClass: organizationalUnit\n"
        f"ou: {ou_name}\n"
    )
    add_cmd = (
        f"podman exec {cname} bash -c '"
        f"echo \"{ldif}\" > /tmp/ou_{ou_name}.ldif && "
        f"ldapadd -x -H ldap://localhost:1389 "
        f"-D \"{admin_dn}\" -w {cfg['admin_password']} "
        f"-f /tmp/ou_{ou_name}.ldif"
        f"'"
    )
    result = runner.run(add_cmd)
    if result.returncode != 0 and "Already exists" not in result.stderr:
        die(f"Failed to create OU '{ou_name}': {result.stderr}")
    success(f"OU '{ou_name}' is ready.")


def create_ldap_user(
    runner: CommandRunner,
    cfg: dict,
    base_dn: str,
    username: str,
    password: str,
    uid_number: int,
    gid_number: int,
    login_shell: str,
    home_directory: str,
) -> bool:
    """
    Create a single LDAP user entry, group entry, and set password.

    Returns True on success, False if user already exists.
    """
    cname = cfg["container_name"]
    admin_dn = f"cn={cfg['admin_username']},{base_dn}"

    # --- Check if user already exists ---
    check_cmd = (
        f"podman exec {cname} ldapsearch -x -H ldap://localhost:1389 "
        f"-D \"{admin_dn}\" -w {cfg['admin_password']} "
        f"-b \"uid={username},ou=People,{base_dn}\" -s base "
        f"\"(objectClass=posixAccount)\" dn"
    )
    result = runner.run(check_cmd)
    if result.returncode == 0 and f"uid={username}" in result.stdout:
        warn(f"User '{username}' already exists — skipping creation.")
        # Still set password in case it needs updating
        _set_password(runner, cfg, base_dn, username, password)
        return False

    # --- Create user LDIF ---
    info(f"Creating user '{username}' (uid={uid_number}, gid={gid_number}) ...")
    user_ldif = (
        f"dn: uid={username},ou=People,{base_dn}\\n"
        f"objectClass: inetOrgPerson\\n"
        f"objectClass: posixAccount\\n"
        f"objectClass: shadowAccount\\n"
        f"cn: {username}\\n"
        f"sn: {username}\\n"
        f"loginShell: {login_shell}\\n"
        f"uidNumber: {uid_number}\\n"
        f"gidNumber: {gid_number}\\n"
        f"homeDirectory: {home_directory}\\n"
        f"shadowLastChange: 0\\n"
        f"shadowMax: 0\\n"
        f"shadowWarning: 0"
    )
    add_user_cmd = (
        f"podman exec {cname} bash -c '"
        f"echo -e \"{user_ldif}\" > /tmp/user_{username}.ldif && "
        f"ldapadd -x -H ldap://localhost:1389 "
        f"-D \"{admin_dn}\" -w {cfg['admin_password']} "
        f"-f /tmp/user_{username}.ldif"
        f"'"
    )
    result = runner.run(add_user_cmd)
    if result.returncode != 0 and "Already exists" not in result.stderr:
        error(f"Failed to create user '{username}': {result.stderr}")
        return False

    # --- Create group LDIF ---
    info(f"Creating group '{username}' (gid={gid_number}) ...")
    group_ldif = (
        f"dn: cn={username},ou=groups,{base_dn}\\n"
        f"objectClass: posixGroup\\n"
        f"cn: {username}\\n"
        f"gidNumber: {gid_number}\\n"
        f"memberUid: {username}"
    )
    add_group_cmd = (
        f"podman exec {cname} bash -c '"
        f"echo -e \"{group_ldif}\" > /tmp/group_{username}.ldif && "
        f"ldapadd -x -H ldap://localhost:1389 "
        f"-D \"{admin_dn}\" -w {cfg['admin_password']} "
        f"-f /tmp/group_{username}.ldif"
        f"'"
    )
    result = runner.run(add_group_cmd)
    if result.returncode != 0 and "Already exists" not in result.stderr:
        warn(f"Group creation for '{username}' failed (user was still created): {result.stderr}")

    # --- Set password ---
    _set_password(runner, cfg, base_dn, username, password)

    success(f"User '{username}' created (uid={uid_number}, gid={gid_number}, home={home_directory})")
    return True


def _set_password(
    runner: CommandRunner, cfg: dict, base_dn: str, username: str, password: str
) -> None:
    """Set LDAP user password."""
    cname = cfg["container_name"]
    admin_dn = f"cn={cfg['admin_username']},{base_dn}"

    passwd_cmd = (
        f"podman exec {cname} ldappasswd -x "
        f"-D \"{admin_dn}\" -w {cfg['admin_password']} "
        f"-s {password} -H ldap://localhost:1389 "
        f"\"uid={username},ou=People,{base_dn}\""
    )
    result = runner.run(passwd_cmd)
    if result.returncode != 0:
        error(f"Failed to set password for '{username}': {result.stderr}")
    else:
        info(f"Password set for '{username}'.")


def verify_users(runner: CommandRunner, cfg: dict, base_dn: str) -> bool:
    """Run ldapsearch to verify all created users. Returns True if all found."""
    cname = cfg["container_name"]
    admin_dn = f"cn={cfg['admin_username']},{base_dn}"

    search_cmd = (
        f"podman exec {cname} ldapsearch -x -H ldap://localhost:1389 "
        f"-D \"{admin_dn}\" -w {cfg['admin_password']} "
        f"-b \"{base_dn}\" \"(objectClass=posixAccount)\" uid uidNumber gidNumber"
    )
    result = runner.run(search_cmd)
    stdout = result.stdout.strip()

    all_found = True
    for user in cfg["users"]:
        uname = user["username"]
        if f"uid: {uname}" in stdout or f"uid={uname}" in stdout:
            success(f"Verified: '{uname}' exists in LDAP directory")
        else:
            error(f"NOT FOUND: '{uname}' missing from LDAP directory")
            all_found = False

    return all_found


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Deploy Bitnami OpenLDAP and create LDAP users from utility/openldap_config.yml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python utility/create_ldap_user.py\n"
            "  python utility/create_ldap_user.py --config /path/to/openldap_config.yml\n"
        ),
    )
    parser.add_argument(
        "--config", default="", help="Path to openldap_config.yml (auto-detected if omitted)"
    )
    args = parser.parse_args()

    # --- Load and validate config ---
    cfg = load_config(args.config)
    validate_config(cfg)

    ldap_host = cfg["server_ip"].strip() if cfg["server_ip"] else "localhost"

    # --- Create runner (local or remote) ---
    runner = CommandRunner(
        server_ip=cfg["server_ip"],
        ssh_user=cfg["ssh_user"],
        ssh_password=cfg["ssh_password"],
        ssh_port=cfg["ssh_port"],
    )

    try:
        if not runner.is_local:
            info(f"Connecting to remote server {cfg['server_ip']}:{cfg['ssh_port']} via SSH ...")
            # Test connection
            result = runner.run("hostname")
            success(f"Connected to: {result.stdout.strip()}")

        # --- Fetch domain from server ---
        domain = fetch_domain_from_server(runner)
        # Override config domain with fetched domain
        cfg["domain"] = domain
        base_dn = domain_to_dc(domain)

        # --- Display plan ---
        print()
        print(f"{_C.BOLD}{'=' * 56}{_C.NC}")
        print(f"{_C.BOLD}  OPENLDAP AUTOMATED SETUP{_C.NC}")
        print(f"{_C.BOLD}{'=' * 56}{_C.NC}")
        print(f"  Target server : {ldap_host}")
        print(f"  Image         : {cfg['image']}")
        print(f"  Container     : {cfg['container_name']}")
        print(f"  LDAP port     : {cfg['ldap_port']}")
        print(f"  LDAPS port    : {cfg['ldaps_port']}")
        print(f"  Domain        : {domain}")
        print(f"  Base DN       : {base_dn}")
        print(f"  Admin user    : {cfg['admin_username']}")
        print(f"  Users to create: {len(cfg['users'])}")
        for i, u in enumerate(cfg["users"]):
            uid = u.get("uid_number", cfg["default_uid_start"] + i)
            print(f"    - {u['username']} (uid={uid})")
        print(f"{_C.BOLD}{'=' * 56}{_C.NC}")
        print()

        # Step 1: Deploy container
        deploy_openldap_container(runner, cfg, base_dn)

        # Step 2: Wait for readiness
        wait_for_ldap_ready(runner, cfg, base_dn)

        # Step 3: Create OUs
        ensure_ou(runner, cfg, base_dn, "People")
        ensure_ou(runner, cfg, base_dn, "groups")

        # Step 4: Create users and groups
        created = 0
        skipped = 0
        for i, user in enumerate(cfg["users"]):
            username = user["username"]
            password = user["password"]
            uid_number = int(user.get("uid_number", cfg["default_uid_start"] + i))
            gid_number = int(user.get("gid_number", cfg["default_uid_start"] + i))
            login_shell = user.get("login_shell", cfg["default_login_shell"])
            home_directory = user.get("home_directory", f"/home/{username}")

            was_created = create_ldap_user(
                runner, cfg, base_dn,
                username, password,
                uid_number, gid_number,
                login_shell, home_directory,
            )
            if was_created:
                created += 1
            else:
                skipped += 1

        # Step 5: Verify
        print()
        info("Verifying all users ...")
        all_ok = verify_users(runner, cfg, base_dn)

        # --- Summary ---
        ldap_url = f"ldap://{ldap_host}:{cfg['ldap_port']}"
        print()
        print(f"{_C.GREEN}{_C.BOLD}{'=' * 56}{_C.NC}")
        print(f"{_C.GREEN}{_C.BOLD}  OPENLDAP SETUP COMPLETE{_C.NC}")
        print(f"{_C.GREEN}{_C.BOLD}{'=' * 56}{_C.NC}")
        print(f"  LDAP URL      : {ldap_url}")
        print(f"  Base DN       : {base_dn}")
        print(f"  Admin DN      : cn={cfg['admin_username']},{base_dn}")
        print(f"  Created       : {created}")
        print(f"  Skipped       : {skipped} (already existed)")
        print()
        print(f"  {_C.BOLD}To verify manually:{_C.NC}")
        print(f"    ldapsearch -x -H {ldap_url} \\")
        print(f"      -D \"cn={cfg['admin_username']},{base_dn}\" -W \\")
        print(f"      -b \"{base_dn}\"")
        print(f"{_C.GREEN}{_C.BOLD}{'=' * 56}{_C.NC}")
        print()

        if not all_ok:
            die("Some users could not be verified. Check output above.")

    finally:
        runner.close()


if __name__ == "__main__":
    main()
