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
Create User Registry — Automated Container Registry Setup Utility

Deploys a Docker Registry v2 container with optional HTTPS (self-signed certs)
and htpasswd authentication. Reads all inputs from utility/user_registry_config.yml.

Supports two modes:
  - LOCAL:  registry_server_ip is empty -> runs podman commands locally
  - REMOTE: registry_server_ip is set  -> runs commands on remote server via SSH

Usage:
    python utility/create_user_registry.py
    python utility/create_user_registry.py --config /path/to/user_registry_config.yml

Steps performed:
    1. Validate configuration
    2. Generate self-signed TLS certificates (if enable_https is true)
    3. Create htpasswd authentication file (if enable_auth is true)
    4. Pull and run Docker Registry v2 container (podman)
    5. Wait for registry readiness
    6. Pull, re-tag, and push sample images (if configured)
    7. Verify registry is functional
    8. Print local_repo_config.yml snippet for user_registry
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
                f"  Check registry_server_ip, registry_server_ssh_user, "
                f"registry_server_ssh_password in user_registry_config.yml"
            )
        self._client = client
        return client

    def run(self, cmd: str, check: bool = False, timeout: int = 120) -> subprocess.CompletedProcess:
        """
        Run a shell command locally or on the remote server.

        Args:
            cmd: Shell command string to execute.
            check: If True, raise on non-zero exit code.
            timeout: Command timeout in seconds.

        Returns:
            CompletedProcess-like object with stdout, stderr, returncode.
        """
        if self.is_local:
            return self._run_local(cmd, check=check, timeout=timeout)
        return self._run_remote(cmd, check=check, timeout=timeout)

    def _run_local(self, cmd: str, check: bool = False, timeout: int = 120) -> subprocess.CompletedProcess:
        """Run command locally."""
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        if check and result.returncode != 0:
            die(f"Command failed (rc={result.returncode}): {cmd}\n{result.stderr}")
        return result

    def _run_remote(self, cmd: str, check: bool = False, timeout: int = 120) -> subprocess.CompletedProcess:
        """Run command on remote server via SSH."""
        client = self._get_ssh_client()
        try:
            _, stdout_ch, stderr_ch = client.exec_command(cmd, timeout=timeout)
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
    """Locate user_registry_config.yml."""
    if config_path and os.path.isfile(config_path):
        return config_path

    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "user_registry_config.yml"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    die(
        "user_registry_config.yml not found in utility directory.\n"
        "  Looked in: " + ", ".join(candidates) + "\n"
        "  Use --config to specify the path."
    )
    return ""  # unreachable


def load_config(config_path: str = "") -> dict:
    """Load and return the user registry configuration."""
    path = _find_config_file(config_path)
    info(f"Loading config from: {path}")

    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    return {
        # Target server
        "server_ip": raw.get("registry_server_ip", ""),
        "ssh_user": raw.get("registry_server_ssh_user", "root"),
        "ssh_password": raw.get("registry_server_ssh_password", ""),
        "ssh_port": int(raw.get("registry_server_ssh_port", 22)),
        # Registry settings
        "image": raw.get("registry_image", "docker.io/library/registry:2"),
        "container_name": raw.get("registry_container_name", "user_registry"),
        "port": int(raw.get("registry_port", 5000)),
        # HTTPS
        "enable_https": bool(raw.get("enable_https", True)),
        "cert_directory": raw.get("cert_directory", "/opt/omnia/user_registry/certs"),
        "cert_common_name": raw.get("cert_common_name", ""),
        "cert_validity_days": int(raw.get("cert_validity_days", 365)),
        # Auth
        "enable_auth": bool(raw.get("enable_auth", True)),
        "users": raw.get("registry_users", []),
        # Sample images
        "sample_images": raw.get("sample_images", []),
    }


def validate_config(cfg: dict) -> None:
    """Validate required fields and exit on error."""
    errors = []

    # Remote mode requires SSH password
    server_ip = (cfg.get("server_ip") or "").strip()
    if server_ip and server_ip not in ("localhost", "127.0.0.1"):
        if not cfg.get("ssh_password"):
            errors.append(
                "registry_server_ssh_password is required when registry_server_ip is set"
            )

    # Auth requires at least one user with username and password
    if cfg.get("enable_auth"):
        users = cfg.get("users") or []
        if not users:
            errors.append(
                "registry_users list is empty — at least one user is required "
                "when enable_auth is true"
            )
        else:
            for i, user in enumerate(users):
                if not isinstance(user, dict):
                    errors.append(
                        f"registry_users[{i}] must be a mapping, got {type(user).__name__}"
                    )
                    continue
                if not user.get("username"):
                    errors.append(f"registry_users[{i}].username is required")
                if not user.get("password"):
                    errors.append(f"registry_users[{i}].password is required")

    # Sample images validation
    for i, img in enumerate(cfg.get("sample_images") or []):
        if not isinstance(img, dict):
            errors.append(f"sample_images[{i}] must be a mapping")
            continue
        if not img.get("source"):
            errors.append(f"sample_images[{i}].source is required")
        if not img.get("name"):
            errors.append(f"sample_images[{i}].name is required")
        if not img.get("tag"):
            errors.append(f"sample_images[{i}].tag is required")

    if errors:
        die(
            "Configuration errors in user_registry_config.yml:\n  - "
            + "\n  - ".join(errors)
        )


# =============================================================================
# TLS CERTIFICATE GENERATION
# =============================================================================

def generate_tls_certs(runner: CommandRunner, cfg: dict) -> dict:
    """Generate self-signed TLS certificates for the registry.

    Returns:
        dict with cert_path and key_path on the target server.
    """
    cert_dir = cfg["cert_directory"]
    server_ip = cfg["server_ip"].strip() if cfg["server_ip"] else "127.0.0.1"
    cn = cfg["cert_common_name"].strip() if cfg["cert_common_name"] else server_ip
    days = cfg["cert_validity_days"]

    cert_path = f"{cert_dir}/domain.crt"
    key_path = f"{cert_dir}/domain.key"

    info(f"Creating certificate directory: {cert_dir}")
    runner.run(f"mkdir -p {cert_dir}", check=True)

    # Check if certs already exist
    result = runner.run(f"test -f {cert_path} && test -f {key_path} && echo EXISTS")
    if "EXISTS" in (result.stdout or ""):
        warn(f"TLS certificates already exist at {cert_dir} — regenerating ...")

    info(f"Generating self-signed TLS certificate (CN={cn}, validity={days} days) ...")

    # Generate self-signed cert with SAN for IP and CN
    openssl_cmd = (
        f"openssl req -newkey rsa:4096 -nodes -sha256 "
        f"-keyout {key_path} "
        f"-x509 -days {days} "
        f"-out {cert_path} "
        f"-subj '/CN={cn}' "
        f"-addext 'subjectAltName=IP:{server_ip}'"
    )
    result = runner.run(openssl_cmd)
    if result.returncode != 0:
        die(f"Failed to generate TLS certificates: {result.stderr}")

    # Set permissions
    runner.run(f"chmod 644 {cert_path}")
    runner.run(f"chmod 600 {key_path}")

    success(f"TLS certificates generated:")
    info(f"  cert_path: {cert_path}")
    info(f"  key_path : {key_path}")

    return {"cert_path": cert_path, "key_path": key_path}


# =============================================================================
# HTPASSWD AUTHENTICATION
# =============================================================================

def create_htpasswd(runner: CommandRunner, cfg: dict) -> str:
    """Create htpasswd file for registry authentication.

    Returns:
        Path to the htpasswd file on the target server.
    """
    auth_dir = f"{cfg['cert_directory']}/../auth"
    htpasswd_path = f"{auth_dir}/htpasswd"

    info(f"Creating auth directory: {auth_dir}")
    runner.run(f"mkdir -p {auth_dir}", check=True)

    # Remove existing htpasswd file to start fresh
    runner.run(f"rm -f {htpasswd_path}")

    for i, user in enumerate(cfg["users"]):
        username = user["username"]
        password = user["password"]

        info(f"Adding registry user: {username}")

        # Use htpasswd via the registry container or generate with openssl
        # Method: use podman run with httpd-tools to generate htpasswd
        if i == 0:
            # Create new file with first user
            htpasswd_cmd = (
                f"podman run --rm --entrypoint htpasswd "
                f"docker.io/library/httpd:2-alpine "
                f"-Bbn '{username}' '{password}' > {htpasswd_path}"
            )
        else:
            # Append additional users
            htpasswd_cmd = (
                f"podman run --rm --entrypoint htpasswd "
                f"docker.io/library/httpd:2-alpine "
                f"-Bbn '{username}' '{password}' >> {htpasswd_path}"
            )

        result = runner.run(htpasswd_cmd)
        if result.returncode != 0:
            # Fallback: generate bcrypt hash with openssl
            warn(f"htpasswd via httpd container failed, using openssl fallback ...")
            fallback_cmd = (
                f"echo -n '{password}' | openssl passwd -apr1 -stdin "
                f"| xargs -I {{}} echo '{username}:{{}}' >> {htpasswd_path}"
            )
            result = runner.run(fallback_cmd)
            if result.returncode != 0:
                die(f"Failed to create htpasswd entry for '{username}': {result.stderr}")

    runner.run(f"chmod 644 {htpasswd_path}")
    success(f"htpasswd file created at {htpasswd_path}")

    return htpasswd_path


# =============================================================================
# REGISTRY CONTAINER DEPLOYMENT
# =============================================================================

def deploy_registry_container(
    runner: CommandRunner,
    cfg: dict,
    tls_paths: dict,
    htpasswd_path: str,
) -> None:
    """Pull and start the Docker Registry v2 container."""
    cname = cfg["container_name"]
    port = cfg["port"]

    info(f"Checking for existing container '{cname}' ...")
    result = runner.run(f"podman ps -a --filter name=^{cname}$ --format '{{{{.Status}}}}'")
    status = result.stdout.strip()

    if status:
        info(f"Removing existing container '{cname}' ({status}) ...")
        runner.run(f"podman rm -f {cname}")

    info(f"Pulling registry image: {cfg['image']} ...")
    result = runner.run(f"podman pull {cfg['image']}", timeout=300)
    if result.returncode != 0:
        die(f"Failed to pull registry image: {result.stderr}")

    # Build podman run command with appropriate flags
    run_parts = [
        f"podman run -d --name {cname}",
        f"-p 0.0.0.0:{port}:5000",
        "--restart=always",
    ]

    # HTTPS configuration
    if cfg["enable_https"] and tls_paths:
        cert_dir = cfg["cert_directory"]
        run_parts.extend([
            f"-v {cert_dir}:/certs:ro",
            "-e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/domain.crt",
            "-e REGISTRY_HTTP_TLS_KEY=/certs/domain.key",
        ])

    # Auth configuration
    if cfg["enable_auth"] and htpasswd_path:
        auth_dir = os.path.dirname(htpasswd_path) if "/" in htpasswd_path else "/opt/omnia/user_registry/auth"
        run_parts.extend([
            f"-v {auth_dir}:/auth:ro",
            "-e REGISTRY_AUTH=htpasswd",
            '-e REGISTRY_AUTH_HTPASSWD_REALM="User Registry"',
            "-e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd",
        ])

    # Storage volume
    run_parts.extend([
        "-v user_registry_data:/var/lib/registry",
        cfg["image"],
    ])

    run_cmd = " \\\n    ".join(run_parts)
    info(f"Starting registry container '{cname}' on port {port} ...")
    result = runner.run(" ".join(run_parts))
    if result.returncode != 0:
        die(f"Failed to start registry container: {result.stderr}")

    success(f"Registry container '{cname}' started on port {port}.")


def wait_for_registry_ready(runner: CommandRunner, cfg: dict, timeout: int = 60) -> None:
    """Wait until the registry API is responding."""
    port = cfg["port"]
    scheme = "https" if cfg["enable_https"] else "http"
    tls_flag = "-k" if cfg["enable_https"] else ""

    info(f"Waiting for registry to be ready ({scheme}://localhost:{port}) ...")

    for attempt in range(1, timeout // 2 + 1):
        check_cmd = (
            f"curl {tls_flag} -sSf --max-time 5 "
            f"{scheme}://localhost:{port}/v2/ 2>/dev/null"
        )

        # If auth is enabled, use first user's credentials
        if cfg["enable_auth"] and cfg["users"]:
            user = cfg["users"][0]
            check_cmd = (
                f"curl {tls_flag} -sSf --max-time 5 "
                f"-u '{user['username']}:{user['password']}' "
                f"{scheme}://localhost:{port}/v2/ 2>/dev/null"
            )

        result = runner.run(check_cmd)
        if result.returncode == 0:
            success(f"Registry is ready (attempt {attempt}).")
            return
        time.sleep(2)

    die(
        f"Registry not ready after {timeout}s.\n"
        f"  Check: podman logs {cfg['container_name']}"
    )


# =============================================================================
# SAMPLE IMAGE OPERATIONS
# =============================================================================

def push_sample_images(runner: CommandRunner, cfg: dict) -> list:
    """Pull, re-tag, and push sample images to the registry.

    Returns:
        List of dicts with image details that were successfully pushed.
    """
    images = cfg.get("sample_images") or []
    if not images:
        info("No sample images configured — skipping image push.")
        return []

    port = cfg["port"]
    server_ip = cfg["server_ip"].strip() if cfg["server_ip"] else "localhost"
    registry_url = f"{server_ip}:{port}"
    scheme = "https" if cfg["enable_https"] else "http"
    tls_flag = "--tls-verify=false" if cfg["enable_https"] else "--tls-verify=false"

    pushed = []

    # Login if auth is enabled
    if cfg["enable_auth"] and cfg["users"]:
        user = cfg["users"][0]
        info(f"Logging in to registry as '{user['username']}' ...")
        login_cmd = (
            f"podman login {registry_url} "
            f"--username '{user['username']}' "
            f"--password '{user['password']}' "
            f"{tls_flag}"
        )
        result = runner.run(login_cmd)
        if result.returncode != 0:
            warn(f"Registry login failed: {result.stderr}")
            warn("Attempting to push images without login ...")

    for img in images:
        source = img["source"]
        name = img["name"]
        tag = img["tag"]
        target = f"{registry_url}/{name}:{tag}"

        info(f"Pulling source image: {source} ...")
        result = runner.run(f"podman pull {source}", timeout=300)
        if result.returncode != 0:
            warn(f"Failed to pull {source}: {result.stderr}")
            continue

        info(f"Tagging as: {target} ...")
        result = runner.run(f"podman tag {source} {target}")
        if result.returncode != 0:
            warn(f"Failed to tag {source} -> {target}: {result.stderr}")
            continue

        info(f"Pushing to registry: {target} ...")
        result = runner.run(f"podman push {target} {tls_flag}", timeout=300)
        if result.returncode != 0:
            warn(f"Failed to push {target}: {result.stderr}")
            continue

        success(f"Pushed: {target}")
        pushed.append({"name": name, "tag": tag, "full": target})

    return pushed


# =============================================================================
# VERIFICATION
# =============================================================================

def verify_registry(runner: CommandRunner, cfg: dict) -> bool:
    """Verify registry is functional by listing the catalog."""
    port = cfg["port"]
    scheme = "https" if cfg["enable_https"] else "http"
    tls_flag = "-k" if cfg["enable_https"] else ""

    info("Verifying registry catalog ...")

    catalog_cmd = f"curl {tls_flag} -sSf --max-time 10 {scheme}://localhost:{port}/v2/_catalog"

    if cfg["enable_auth"] and cfg["users"]:
        user = cfg["users"][0]
        catalog_cmd = (
            f"curl {tls_flag} -sSf --max-time 10 "
            f"-u '{user['username']}:{user['password']}' "
            f"{scheme}://localhost:{port}/v2/_catalog"
        )

    result = runner.run(catalog_cmd)
    if result.returncode != 0:
        error(f"Registry catalog check failed: {result.stderr}")
        return False

    info(f"Registry catalog: {result.stdout.strip()}")

    # Verify auth works (if enabled) by trying without credentials
    if cfg["enable_auth"]:
        noauth_cmd = (
            f"curl {tls_flag} -sSf --max-time 5 "
            f"{scheme}://localhost:{port}/v2/_catalog 2>&1 || true"
        )
        result = runner.run(noauth_cmd)
        if result.returncode == 0 and "repositories" in (result.stdout or ""):
            warn("Registry returned catalog WITHOUT authentication — auth may not be working")
        else:
            success("Registry correctly requires authentication.")

    success("Registry is functional.")
    return True


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description=(
            "Deploy a Docker Registry v2 container with optional HTTPS and "
            "htpasswd authentication. Reads inputs from utility/user_registry_config.yml."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python utility/create_user_registry.py\n"
            "  python utility/create_user_registry.py --config /path/to/user_registry_config.yml\n"
        ),
    )
    parser.add_argument(
        "--config", default="", help="Path to user_registry_config.yml (auto-detected if omitted)"
    )
    args = parser.parse_args()

    # --- Load and validate config ---
    cfg = load_config(args.config)
    validate_config(cfg)

    server_ip = cfg["server_ip"].strip() if cfg["server_ip"] else "localhost"
    scheme = "https" if cfg["enable_https"] else "http"

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
            result = runner.run("hostname")
            success(f"Connected to: {result.stdout.strip()}")

        # --- Display plan ---
        print()
        print(f"{_C.BOLD}{'=' * 60}{_C.NC}")
        print(f"{_C.BOLD}  USER REGISTRY AUTOMATED SETUP{_C.NC}")
        print(f"{_C.BOLD}{'=' * 60}{_C.NC}")
        print(f"  Target server : {server_ip}")
        print(f"  Image         : {cfg['image']}")
        print(f"  Container     : {cfg['container_name']}")
        print(f"  Port          : {cfg['port']}")
        print(f"  Protocol      : {scheme.upper()}")
        print(f"  Authentication: {'ENABLED' if cfg['enable_auth'] else 'DISABLED'}")
        if cfg["enable_auth"]:
            for u in cfg["users"]:
                print(f"    - {u['username']}")
        if cfg["enable_https"]:
            print(f"  Cert directory: {cfg['cert_directory']}")
        if cfg.get("sample_images"):
            print(f"  Sample images : {len(cfg['sample_images'])}")
            for img in cfg["sample_images"]:
                print(f"    - {img['source']} -> {img['name']}:{img['tag']}")
        print(f"{_C.BOLD}{'=' * 60}{_C.NC}")
        print()

        # Step 1: Generate TLS certificates (if HTTPS)
        tls_paths = {}
        if cfg["enable_https"]:
            tls_paths = generate_tls_certs(runner, cfg)
        else:
            info("HTTPS disabled — skipping TLS certificate generation.")

        # Step 2: Create htpasswd (if auth enabled)
        htpasswd_path = ""
        if cfg["enable_auth"]:
            htpasswd_path = create_htpasswd(runner, cfg)
        else:
            info("Authentication disabled — skipping htpasswd creation.")

        # Step 3: Deploy registry container
        deploy_registry_container(runner, cfg, tls_paths, htpasswd_path)

        # Step 4: Wait for readiness
        wait_for_registry_ready(runner, cfg)

        # Step 5: Push sample images
        pushed = push_sample_images(runner, cfg)

        # Step 6: Verify
        print()
        verify_ok = verify_registry(runner, cfg)

        # --- Build local_repo_config.yml snippet ---
        registry_host = f"{server_ip}:{cfg['port']}"
        cert_path = tls_paths.get("cert_path", "") if cfg["enable_https"] else ""
        key_path = tls_paths.get("key_path", "") if cfg["enable_https"] else ""

        # --- Summary ---
        print()
        print(f"{_C.GREEN}{_C.BOLD}{'=' * 60}{_C.NC}")
        print(f"{_C.GREEN}{_C.BOLD}  USER REGISTRY SETUP COMPLETE{_C.NC}")
        print(f"{_C.GREEN}{_C.BOLD}{'=' * 60}{_C.NC}")
        print(f"  Registry URL  : {scheme}://{registry_host}")
        print(f"  Container     : {cfg['container_name']}")
        print(f"  Protocol      : {scheme.upper()}")
        print(f"  Authentication: {'ENABLED' if cfg['enable_auth'] else 'DISABLED'}")
        if pushed:
            print(f"  Images pushed : {len(pushed)}")
            for img in pushed:
                print(f"    - {img['full']}")
        print()

        # Print local_repo_config.yml snippet
        print(f"  {_C.BOLD}Add to local_repo_config.yml:{_C.NC}")
        print()
        if cfg["enable_https"]:
            print(f"  user_registry:")
            print(f'    - {{ host: "{registry_host}", '
                  f'cert_path: "{cert_path}", '
                  f'key_path: "{key_path}" }}')
        else:
            print(f"  user_registry:")
            print(f'    - {{ host: "{registry_host}", '
                  f'cert_path: "", key_path: "" }}')

        # Print credential file snippet if auth is enabled
        if cfg["enable_auth"]:
            print()
            print(f"  {_C.BOLD}Create user_registry_credential.yml:{_C.NC}")
            print()
            print(f"  user_registry_credential:")
            for u in cfg["users"]:
                print(f'    - {{ name: "{u["username"]}", '
                      f'username: "{u["username"]}", '
                      f'password: "********" }}')

        print()
        print(f"  {_C.BOLD}To verify manually:{_C.NC}")
        tls_curl = "-k " if cfg["enable_https"] else ""
        auth_curl = ""
        if cfg["enable_auth"] and cfg["users"]:
            u = cfg["users"][0]
            auth_curl = f"-u '{u['username']}:<password>' "
        print(f"    curl {tls_curl}{auth_curl}{scheme}://{registry_host}/v2/_catalog")
        print(f"{_C.GREEN}{_C.BOLD}{'=' * 60}{_C.NC}")
        print()

        if not verify_ok:
            die("Registry verification failed. Check output above.")

    finally:
        runner.close()


if __name__ == "__main__":
    main()
