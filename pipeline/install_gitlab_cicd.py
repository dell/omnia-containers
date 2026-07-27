#!/usr/bin/env python3
"""
GitLab CI/CD Installation and Configuration Script
Installs GitLab on a server and configures it with multi-cluster pipeline settings.
"""

import os
import sys
import subprocess
import re
import base64
import yaml
import json
import time
import getpass
import requests
import argparse
import socket
import glob
from pathlib import Path
from urllib.parse import urljoin, urlparse

# Suppress SSL warnings for self-signed certificates
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _ensure_hostname_resolvable(gitlab_url):
    """Ensure the GitLab hostname is resolvable by adding to /etc/hosts if needed.
    
    Args:
        gitlab_url: The GitLab URL (e.g., https://gitlab.example.com)
    
    Returns:
        True if hostname is resolvable (either by DNS or after /etc/hosts update),
        False if unable to make it resolvable.
    """
    parsed = urlparse(gitlab_url)
    hostname = parsed.hostname
    
    try:
        # Check if hostname already resolves
        socket.gethostbyname(hostname)
        print(f"✓ Hostname {hostname} is already resolvable")
        return True
    except socket.gaierror:
        # Hostname doesn't resolve, try to add to /etc/hosts
        print(f"⚠ Hostname {hostname} does not resolve in DNS")
        print(f"  Attempting to add to /etc/hosts...")
        
        # Get the server's primary IP address
        try:
            # Create a socket to get the local IP used for outgoing connections
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Google DNS - just to get the route
            local_ip = s.getsockname()[0]
            s.close()
            
            # Add to /etc/hosts
            hosts_path = "/etc/hosts"
            with open(hosts_path, "a") as f:
                f.write(f"{local_ip} {hostname}\n")
            
            print(f"✓ Added {local_ip} {hostname} to /etc/hosts")
            
            # Verify it now resolves
            socket.gethostbyname(hostname)
            print(f"✓ Hostname {hostname} is now resolvable")
            return True
            
        except Exception as e:
            print(f"✗ Failed to add hostname to /etc/hosts: {e}")
            print(f"  Please manually add your server's IP and {hostname} to /etc/hosts")
            return False


def _repo_root():
    return Path(__file__).resolve().parent.parent


def _gitlab_cred_paths():
    """Return (vault_file, key_file) paths for the GitLab admin credentials."""
    pipeline_dir = Path(__file__).resolve().parent
    return (
        pipeline_dir / "gitlab_admin_credentials.yml",
        pipeline_dir / ".omnia_test_credentials.key",
    )


def _ansible_vault_bin():
    """Locate the ansible-vault executable (prefer the project's venv)."""
    venv_bin = _repo_root() / ".venv" / "bin" / "ansible-vault"
    if venv_bin.exists():
        return str(venv_bin)
    return "ansible-vault"  # fall back to PATH


def _detect_primary_ip():
    """Best-effort detection of the server's primary non-loopback IP."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("1.1.1.1", 80))
            ip_addr = s.getsockname()[0]
            if ip_addr and not ip_addr.startswith("127."):
                return ip_addr
    except Exception:
        pass
    return None


def save_gitlab_credentials(config):
    """Create gitlab_admin_credentials.yml in pipeline/ and encrypt with ansible-vault.

    Reuses the existing .omnia_test_credentials.key (creating it if missing,
    same convention the automation uses). The user can later inspect the file
    manually with:

        ansible-vault view pipeline/gitlab_admin_credentials.yml \\
            --vault-password-file pipeline/.omnia_test_credentials.key
    """
    vault_file, key_file = _gitlab_cred_paths()

    # Create the vault key if it does not exist yet
    if not key_file.exists():
        import secrets
        key_file.write_text(secrets.token_urlsafe(32)[:32], encoding="utf-8")
        os.chmod(key_file, 0o600)

    # Write the plain-text credentials file
    data = {
        "gitlab": {
            "url": config["gitlab_url"],
            "admin": {
                "username": config["admin_username"],
                "password": config["admin_password"],
            },
        }
    }
    vault_file.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
    os.chmod(vault_file, 0o600)

    # Encrypt it in place
    try:
        subprocess.run(
            [_ansible_vault_bin(), "encrypt", str(vault_file),
             "--vault-password-file", str(key_file)],
            capture_output=True, text=True, check=True,
        )
        print(f"✓ Saved and encrypted admin credentials: {vault_file}")
        print(f"  Decrypt with: ansible-vault view {vault_file.name} "
              f"--vault-password-file {key_file.name}")
        return True
    except Exception as e:
        print(f"Warning: Could not encrypt credentials file: {e}")
        return False


def load_gitlab_credentials():
    """Load GitLab admin credentials from the encrypted vault file.

    Returns a dict with gitlab_url/admin_username/admin_password, or None
    if the file or key is missing / cannot be decrypted.
    """
    vault_file, key_file = _gitlab_cred_paths()
    if not vault_file.exists() or not key_file.exists():
        return None

    try:
        result = subprocess.run(
            [_ansible_vault_bin(), "view", str(vault_file),
             "--vault-password-file", str(key_file)],
            capture_output=True, text=True, check=True,
        )
        creds = yaml.safe_load(result.stdout)
        return {
            "gitlab_url": creds["gitlab"]["url"],
            "admin_username": creds["gitlab"]["admin"]["username"],
            "admin_password": creds["gitlab"]["admin"]["password"],
        }
    except Exception as e:
        print(f"Warning: Could not load encrypted credentials: {e}")
        return None


class GitLabInstaller:
    def __init__(self):
        script_dir = Path(__file__).resolve().parent
        self.config_file = script_dir / ".gitlab-ci.yml"
        # clusters/ lives under pipeline/
        self.clusters_dir = script_dir / "clusters"
        self.datasets_dir = script_dir.parent / "datasets"
        self.gitlab_url = None
        self.admin_token = None
        self.project_id = None
        self.config = {}
        
    def load_default_config(self):
        """Load default configuration from the multi-cluster YAML file"""
        try:
            with open(self.config_file, 'r') as f:
                content = f.read()
                # Extract variables section
                if 'variables:' in content:
                    variables_start = content.index('variables:')
                    variables_section = content[variables_start:]
                    
                    # Parse variables manually since we only need the variables section
                    self.config = self._parse_yaml_variables(variables_section)
                    print("✓ Loaded default configuration from multi-cluster YAML file")
                    return True
        except Exception as e:
            print(f"✗ Error loading default config: {e}")
            return False
    
    def _parse_yaml_variables(self, yaml_content):
        """Parse variables from YAML content"""
        variables = {}
        lines = yaml_content.split('\n')
        in_variables = False
        
        for line in lines:
            if line.strip().startswith('variables:'):
                in_variables = True
                continue
            if in_variables and line.strip() and not line.startswith(' '):
                break
            if in_variables and ':' in line and not line.strip().startswith('#'):
                key_value = line.split(':', 1)
                if len(key_value) == 2:
                    key = key_value[0].strip()
                    value = key_value[1].strip().strip('"\'')
                    if value:  # Only add non-empty values
                        variables[key] = value
        
        return variables
    
    def get_user_input(self, args):
        """Get user input for GitLab configuration.

        Always prompts for Admin Username, Admin Password, Project Name,
        and Project Path so the user can confirm or override the defaults.
        CLI arguments (--gitlab-url, --admin-token) pre-fill values but
        other fields are always asked interactively.

        If gitlab_admin_credentials.yml (encrypted) exists, credentials
        are auto-loaded from there and shown as defaults.
        """
        print("\n" + "=" * 60)
        print("GitLab CI/CD Configuration")
        print("=" * 60)

        # Try to load credentials from encrypted vault file
        vault_creds = load_gitlab_credentials()
        if vault_creds:
            print("✓ Loaded credentials from encrypted gitlab_admin_credentials.yml")

        # --- GitLab URL ---
        if args.gitlab_url:
            self.gitlab_url = args.gitlab_url
            print(f"GitLab URL: {self.gitlab_url}")
        elif vault_creds:
            default_url = vault_creds["gitlab_url"]
            self.gitlab_url = (
                input(f"GitLab Server URL [default: {default_url}]: ").strip()
                or default_url
            )
        else:
            default_url = "https://omnia.gitlab.com"
            self.gitlab_url = (
                input(f"GitLab Server URL [default: {default_url}]: ").strip()
                or default_url
            )
        if not self.gitlab_url.startswith(("http://", "https://")):
            self.gitlab_url = "https://" + self.gitlab_url

        # --- Always prompt for admin credentials ---
        default_username = vault_creds["admin_username"] if vault_creds else args.admin_username
        default_password = vault_creds["admin_password"] if vault_creds else args.admin_password

        print("\nGitLab Admin Credentials:")
        admin_username = input(f"Admin Username [default: {default_username}]: ").strip() or default_username
        if admin_username.lower() != "root":
            print("⚠ GitLab's built-in admin account is 'root'. Forcing username to 'root'.")
            admin_username = "root"

        if default_password:
            admin_password = getpass.getpass(
                "Admin Password [Enter=keep saved, or type new]: "
            ) or default_password
        else:
            admin_password = getpass.getpass("Admin Password: ")
            if not admin_password:
                print("Error: Admin password is required.")
                return None

        # --- Always prompt for project configuration ---
        default_project_name = args.project_name   # argparse default 'omnia-automation'
        default_project_path = args.project_path   # argparse default 'root/omnia-automation'

        print("\nProject Configuration:")
        print(f"Project Name: {default_project_name} (using default)")
        print(f"Project Path: {default_project_path} (using default)")
        project_name = default_project_name
        project_path = default_project_path

        # --- Personal access token ---
        if args.admin_token:
            self.admin_token = args.admin_token
            print("\nPersonal Access Token: [provided via CLI]")
        else:
            print("\nNote: Leave empty to auto-generate after installation")
            self.admin_token = input("Personal Access Token [leave empty to auto-generate]: ").strip() or ""

        return {
            "gitlab_url": self.gitlab_url,
            "admin_username": admin_username,
            "admin_password": admin_password,
            "project_name": project_name,
            "project_path": project_path,
            "admin_token": self.admin_token,
        }
    
    def install_gitlab(self, config, non_interactive=False):
        """Install GitLab on the server
        
        Args:
            config: Configuration dictionary
            non_interactive: If True, skip prompts and auto-cleanup URL changes
        """
        print("\n" + "="*60)
        print("Installing GitLab...")
        print("="*60)
        
        # Detect OS and install GitLab
        try:
            # Check if running on Ubuntu/Debian
            if os.path.exists('/etc/debian_version'):
                self._install_gitlab_debian(config, non_interactive=non_interactive)
            # Check if running on RHEL/CentOS
            elif os.path.exists('/etc/redhat-release'):
                self._install_gitlab_rhel(config, non_interactive=non_interactive)
            else:
                print("✗ Unsupported OS. Please install GitLab manually.")
                return False
            
            print("✓ GitLab installation completed")
            print(f"✓ GitLab URL: {self.gitlab_url}")
            print("✓ Please wait for GitLab to fully start (may take 5-10 minutes)")
            return True
        except Exception as e:
            print(f"✗ Error installing GitLab: {e}")
            return False
    
    def _install_gitlab_debian(self, config, non_interactive=False):
        """Install GitLab on Debian/Ubuntu
        
        Args:
            config: Configuration dictionary
            non_interactive: If True, skip prompts and auto-cleanup URL changes
        """
        print("Installing GitLab on Debian/Ubuntu...")
        
        # Check if GitLab is already installed
        gitlab_installed = os.path.exists('/etc/gitlab/gitlab.rb')
        
        # Load existing password if GitLab is already installed
        old_password = None
        if gitlab_installed:
            vault_creds = load_gitlab_credentials()
            if vault_creds:
                old_password = vault_creds.get("admin_password")
        
        if not gitlab_installed:
            # Fresh installation
            commands = [
                "curl -sS https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.deb.sh | sudo bash",
                "apt-get install -y gitlab-ce"
            ]
            
            for cmd in commands:
                print(f"Executing: {cmd}")
                subprocess.run(cmd, shell=True, check=True)
        else:
            print("GitLab is already installed, skipping package installation")
        
        # Check for URL change and cleanup if needed
        url_changed = self._check_and_handle_url_change(non_interactive=non_interactive)
        
        # Ensure runsvdir is active and disable Let’s Encrypt before reconfigure
        self._ensure_runsvdir_running()
        self._disable_letsencrypt()
        self._ensure_self_signed_ssl()
        self._patch_logrotate_recipe()

        # Kill any stale Cinc/Chef client processes that could block reconfigure
        subprocess.run("pkill -9 -f 'cinc-client|chef-client' 2>/dev/null",
                       shell=True, capture_output=True)

        # Configure GitLab URL
        disable_le_config = "letsencrypt['enable']=false;nginx['redirect_http_to_https']=false"
        configure_cmd = (
            f"EXTERNAL_URL='{self.gitlab_url}' "
            f"GITLAB_OMNIBUS_CONFIG=\"{disable_le_config}\" gitlab-ctl reconfigure"
        )
        print(f"Executing: {configure_cmd}")
        subprocess.run(configure_cmd, shell=True, check=True)
        
        # Reset admin password if provided (wait for services first)
        if config.get("admin_password"):
            print("\nEnsuring admin password matches provided credentials...")
            self._wait_for_gitlab_services()
            self._reset_admin_password(config.get("admin_username"), config.get("admin_password"))
    
    def _install_gitlab_rhel(self, config, non_interactive=False):
        """Install GitLab on RHEL/CentOS
        
        Args:
            config: Configuration dictionary
            non_interactive: If True, skip prompts and auto-cleanup URL changes
        """
        print("Installing GitLab on RHEL/CentOS...")
        
        # Check if GitLab is already installed
        gitlab_installed = os.path.exists('/etc/gitlab/gitlab.rb')
        
        # Load existing password if GitLab is already installed
        old_password = None
        if gitlab_installed:
            vault_creds = load_gitlab_credentials()
            if vault_creds:
                old_password = vault_creds.get("admin_password")
        
        if not gitlab_installed:
            # Fresh installation
            commands = [
                "curl -sS https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.rpm.sh | sudo bash",
                "yum install -y gitlab-ce"
            ]
            
            for cmd in commands:
                print(f"Executing: {cmd}")
                subprocess.run(cmd, shell=True, check=True)
        else:
            print("GitLab is already installed, skipping package installation")
        
        # Handle SELinux before reconfigure
        self._handle_selinux()
        
        # Check for URL change and cleanup if needed
        url_changed = self._check_and_handle_url_change(non_interactive=non_interactive)
        
        # Ensure runsvdir is active and disable Let’s Encrypt before reconfigure
        self._ensure_runsvdir_running()
        self._disable_letsencrypt()
        self._ensure_self_signed_ssl()
        self._patch_logrotate_recipe()

        # Kill any stale Cinc/Chef client processes that could block reconfigure
        subprocess.run("pkill -9 -f 'cinc-client|chef-client' 2>/dev/null",
                       shell=True, capture_output=True)

        # Configure GitLab URL
        disable_le_config = "letsencrypt['enable']=false;nginx['redirect_http_to_https']=false"
        configure_cmd = (
            f"EXTERNAL_URL='{self.gitlab_url}' "
            f"GITLAB_OMNIBUS_CONFIG=\"{disable_le_config}\" gitlab-ctl reconfigure"
        )
        print(f"Executing: {configure_cmd}")
        subprocess.run(configure_cmd, shell=True, check=True)
        
        # Reset admin password if provided (wait for services first)
        if config.get("admin_password"):
            print("\nEnsuring admin password matches provided credentials...")
            self._wait_for_gitlab_services()
            self._reset_admin_password(config.get("admin_username"), config.get("admin_password"))
    
    def _handle_selinux(self):
        """Handle SELinux compatibility issues before gitlab-ctl reconfigure"""
        try:
            result = subprocess.run("getenforce", shell=True, capture_output=True, text=True)
            selinux_status = result.stdout.strip()
            print(f"SELinux status: {selinux_status}")
            
            if selinux_status in ["Enforcing", "Permissive"]:
                print("SELinux is active. Patching GitLab SELinux recipe to skip module loading...")
                selinux_recipe = "/opt/gitlab/embedded/cookbooks/gitlab/recipes/selinux.rb"
                if os.path.exists(selinux_recipe):
                    with open(selinux_recipe, 'r') as f:
                        content = f.read()
                    original = content
                    # 1. Add action :nothing to all semodule -i (install) execute blocks
                    content = re.sub(
                        r'(execute "semodule -i [^"]+" do\s*\n'
                        r'\s*not_if "getenforce \| grep Disabled"\s*\n'
                        r'\s*not_if "semodule -l [^"]+"\s*\n'
                        r'\s*retries SELINUX_OPERATION_RETRIES\s*\n'
                        r'\s*retry_delay SELINUX_OPERATION_RETRY_DELAY)\s*\n(\s*end)',
                        r'\1\n      action :nothing\n\2',
                        content
                    )
                    # 2. Disable the bash block for setting security context
                    content = re.sub(
                        r'(only_if \{ SELinuxHelper\.enabled\? && !SELinuxHelper\.context_set\?\(node\) \})',
                        r'only_if { false }',
                        content
                    )
                    if content != original:
                        with open(selinux_recipe, 'w') as f:
                            f.write(content)
                        print("✓ Patched SELinux recipe to skip module loading and context checks")
                    else:
                        print("SELinux recipe already patched or pattern not found")
                        subprocess.run("setenforce 0", shell=True)
                        print("Set SELinux to permissive mode as fallback")
                else:
                    print("SELinux recipe not found, setting permissive mode")
                    subprocess.run("setenforce 0", shell=True)
        except FileNotFoundError:
            print("getenforce not found, SELinux likely not installed")
        except Exception as e:
            print(f"SELinux handling warning: {e}")

    def _ensure_runsvdir_running(self):
        """Ensure gitlab-runsvdir service is active and supervise pipes exist.

        After cleanup or a fresh install the supervise/ok pipes may be missing
        even when the service shows as 'active'.  A restart recreates them and
        prevents the 'wait for <service> service socket' hang during reconfigure.
        """
        try:
            subprocess.run("systemctl enable gitlab-runsvdir",
                           shell=True, capture_output=True)

            # Always restart to ensure supervise pipes are recreated
            print("Restarting gitlab-runsvdir to ensure supervise pipes exist...")
            restart_result = subprocess.run(
                "systemctl restart gitlab-runsvdir",
                shell=True, capture_output=True, text=True
            )
            if restart_result.returncode != 0:
                print(f"✗ Failed to restart gitlab-runsvdir: {restart_result.stderr.strip()}")
                # Fallback: try start if restart failed
                subprocess.run("systemctl start gitlab-runsvdir",
                               shell=True, capture_output=True)
            else:
                print("✓ gitlab-runsvdir restarted successfully")

            # Wait for the supervise pipes to appear (up to 15 seconds)
            for _ in range(15):
                pipes = glob.glob("/opt/gitlab/service/*/supervise/ok")
                if pipes:
                    print(f"✓ Supervise pipes ready ({len(pipes)} services)")
                    return
                time.sleep(1)
            print("⚠ Supervise pipes not yet ready — reconfigure may wait briefly")
        except Exception as e:
            print(f"⚠ Unable to verify gitlab-runsvdir status: {e}")

    def _patch_logrotate_recipe(self):
        """Patch the logrotate Chef recipe to skip socket wait checks that can hang reconfigure."""
        logrotate_recipe = "/opt/gitlab/embedded/cookbooks/gitlab/recipes/logrotate.rb"
        if not os.path.exists(logrotate_recipe):
            # Recipe may not exist in all GitLab versions
            return

        try:
            with open(logrotate_recipe, 'r') as f:
                content = f.read()

            original = content

            # Find and disable the ruby_block that waits for logrotate service socket
            # Pattern: ruby_block "wait for logrotate service socket" do ... end
            content = re.sub(
                r'ruby_block "wait for logrotate service socket" do\b',
                'ruby_block "wait for logrotate service socket" do\n      action :nothing',
                content
            )

            # Also disable the ruby_block for logrotate service check if present
            content = re.sub(
                r'ruby_block "wait for logrotate service to be ready" do\b',
                'ruby_block "wait for logrotate service to be ready" do\n      action :nothing',
                content
            )

            if content != original:
                with open(logrotate_recipe, 'w') as f:
                    f.write(content)
                print("✓ Patched logrotate recipe to skip socket wait checks")
            else:
                print("Logrotate recipe already patched or pattern not found")
        except Exception as e:
            print(f"⚠ Could not patch logrotate recipe: {e}")

    def _disable_letsencrypt(self):
        """Explicitly disable Let's Encrypt to avoid ACME failures on private domains."""
        gitlab_rb = "/etc/gitlab/gitlab.rb"
        if not os.path.exists(gitlab_rb):
            return

        try:
            with open(gitlab_rb, 'r') as f:
                content = f.read()

            updated = content
            # Force disable letsencrypt
            if "letsencrypt['enable']" in content:
                updated = re.sub(r"letsencrypt\['enable'\]\s*=.*", "letsencrypt['enable'] = false", updated)
            else:
                updated += "\nletsencrypt['enable'] = false\n"

            # Ensure HTTP->HTTPS redirect is disabled when not using certs
            if "nginx['redirect_http_to_https']" in updated:
                updated = re.sub(r"nginx\['redirect_http_to_https'\]\s*=.*", "nginx['redirect_http_to_https'] = false", updated)
            else:
                updated += "nginx['redirect_http_to_https'] = false\n"

            if updated != content:
                with open(gitlab_rb, 'w') as f:
                    f.write(updated)
                print("✓ Disabled Let's Encrypt auto-provisioning in gitlab.rb")
        except Exception as e:
            print(f"⚠ Could not update gitlab.rb to disable Let's Encrypt: {e}")

    def _ensure_self_signed_ssl(self):
        """Generate self-signed SSL certificates when using https:// without Let's Encrypt.

        GitLab Nginx expects cert files at /etc/gitlab/ssl/<hostname>.crt and .key
        when EXTERNAL_URL starts with https://. Without them Nginx refuses to start,
        causing 'Connection refused' on port 443.
        """
        if not self.gitlab_url or not self.gitlab_url.startswith("https://"):
            return

        hostname = urlparse(self.gitlab_url).hostname
        if not hostname:
            return

        ssl_dir = "/etc/gitlab/ssl"
        cert_path = os.path.join(ssl_dir, f"{hostname}.crt")
        key_path = os.path.join(ssl_dir, f"{hostname}.key")

        # Skip if valid certs already exist
        if os.path.exists(cert_path) and os.path.exists(key_path):
            print(f"✓ SSL certificates already exist for {hostname}")
            return

        print(f"Generating self-signed SSL certificate for {hostname}...")
        os.makedirs(ssl_dir, exist_ok=True)

        openssl_cmd = (
            f'openssl req -x509 -nodes -days 3650 -newkey rsa:2048 '
            f'-keyout "{key_path}" -out "{cert_path}" '
            f'-subj "/C=US/ST=State/L=City/O=GitLab/CN={hostname}" '
            f'-addext "subjectAltName=DNS:{hostname}"'
        )
        result = subprocess.run(
            openssl_cmd, shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            os.chmod(key_path, 0o600)
            print(f"✓ Self-signed SSL certificate generated for {hostname}")
        else:
            print(f"⚠ Failed to generate SSL certificate: {result.stderr.strip()}")
            print("  GitLab may not start on HTTPS. Consider using http:// URL instead.")
    
    def _get_current_gitlab_url(self):
        """Get the current EXTERNAL_URL from GitLab configuration if GitLab is installed"""
        gitlab_rb = "/etc/gitlab/gitlab.rb"
        if not os.path.exists(gitlab_rb):
            return None
        
        try:
            with open(gitlab_rb, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("external_url"):
                        # Extract the URL from: external_url 'https://gitlab.example.com'
                        match = re.search(r"external_url\s+[\"']([^\"']+)[\"']", line)
                        if match:
                            return match.group(1)
        except Exception as e:
            print(f"Warning: Could not read gitlab.rb: {e}")
        
        return None
    
    def _wait_for_gitlab_services(self, timeout=120):
        """Wait for critical GitLab services (PostgreSQL, Rails) to be ready.

        Password reset and API calls fail if executed before services finish
        starting after gitlab-ctl reconfigure.
        """
        print("Waiting for GitLab services to be ready...")
        deadline = time.time() + timeout
        while time.time() < deadline:
            result = subprocess.run(
                "gitlab-ctl status",
                shell=True, capture_output=True, text=True
            )
            output = result.stdout
            # Check that postgresql and rails (puma/unicorn) are running
            pg_ok = "run: postgresql" in output or "run: patroni" in output
            web_ok = "run: puma" in output or "run: unicorn" in output
            if pg_ok and web_ok:
                print("✓ GitLab services (PostgreSQL + Web) are running")
                return True
            time.sleep(5)
        print("⚠ Timed out waiting for GitLab services — continuing anyway")
        return False

    def _reset_admin_password(self, username, new_password):
        """Reset the admin password in GitLab database using gitlab-rails.

        Uses stdin to pass the Ruby script to avoid shell-quoting issues
        with special characters in passwords.
        """
        print(f"\nResetting admin password for user '{username}'...")
        
        try:
            # Build Ruby script — password is passed via env var to avoid quoting issues
            ruby_script = (
                "pw = ENV['GITLAB_ADMIN_PW']\n"
                f"user = User.find_by_username('{username}')\n"
                "if user\n"
                "  user.password = pw\n"
                "  user.password_confirmation = pw\n"
                "  user.save!\n"
                "  puts 'Password reset successfully'\n"
                "else\n"
                "  puts 'User not found'\n"
                "end"
            )

            env = os.environ.copy()
            env['GITLAB_ADMIN_PW'] = new_password

            result = subprocess.run(
                ["gitlab-rails", "runner", "-"],
                input=ruby_script,
                capture_output=True,
                text=True,
                timeout=120,
                env=env,
            )
            
            if result.returncode == 0 and "successfully" in result.stdout:
                print("✓ Admin password reset successfully")
                return True
            else:
                print(f"✗ Failed to reset password: {result.stderr or result.stdout}")
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ Password reset command timed out")
            return False
        except Exception as e:
            print(f"✗ Error resetting password: {e}")
            return False
    
    def _cleanup_old_gitlab_config(self, old_url):
        """Clean up old GitLab configuration before reconfiguring with new URL"""
        print(f"\nCleaning up old GitLab configuration for: {old_url}")
        
        # 1. Update /etc/gitlab/gitlab.rb with new EXTERNAL_URL
        gitlab_rb = "/etc/gitlab/gitlab.rb"
        if os.path.exists(gitlab_rb):
            try:
                with open(gitlab_rb, 'r') as f:
                    content = f.read()
                
                # Replace old external_url with new one
                new_content = re.sub(
                    r"external_url\s+[\"'][^\"']+[\"']",
                    f"external_url '{self.gitlab_url}'",
                    content
                )
                
                if new_content != content:
                    with open(gitlab_rb, 'w') as f:
                        f.write(new_content)
                    print(f"✓ Updated EXTERNAL_URL in {gitlab_rb}")
                else:
                    # If no external_url line found, add it
                    if "external_url" not in content:
                        with open(gitlab_rb, 'a') as f:
                            f.write(f"\nexternal_url '{self.gitlab_url}'\n")
                        print(f"✓ Added EXTERNAL_URL to {gitlab_rb}")
            except Exception as e:
                print(f"✗ Error updating gitlab.rb: {e}")
        
        # 2. Remove old hostname from /etc/hosts
        old_hostname = urlparse(old_url).hostname
        if old_hostname:
            try:
                with open("/etc/hosts", 'r') as f:
                    lines = f.readlines()
                
                new_lines = []
                removed = False
                for line in lines:
                    if old_hostname in line and not line.strip().startswith('#'):
                        # Remove only the entry with this hostname
                        parts = line.split()
                        new_parts = [p for p in parts if old_hostname not in p]
                        if new_parts:
                            new_lines.append(' '.join(new_parts) + '\n')
                        removed = True
                    else:
                        new_lines.append(line)
                
                if removed:
                    with open("/etc/hosts", 'w') as f:
                        f.writelines(new_lines)
                    print(f"✓ Removed old hostname '{old_hostname}' from /etc/hosts")
            except Exception as e:
                print(f"✗ Error updating /etc/hosts: {e}")
        
        # 3. Stop GitLab services before reconfigure
        print("Stopping GitLab services...")
        subprocess.run("gitlab-ctl stop", shell=True, capture_output=True)
        print("✓ GitLab services stopped")
        
        # 4. Clear all cached configurations
        print("Clearing cached configurations...")
        
        # Clear Chef cache
        subprocess.run("rm -rf /opt/gitlab/embedded/cookbooks/cache", shell=True, capture_output=True)
        print("✓ Chef cache cleared")
        
        # Clear Nginx configuration cache
        subprocess.run("rm -rf /var/opt/gitlab/nginx/conf/nginx.conf*", shell=True, capture_output=True)
        subprocess.run("rm -rf /var/log/gitlab/nginx/*", shell=True, capture_output=True)
        print("✓ Nginx config cache cleared")
        
        # Clear SSL certificates for old domain
        old_hostname = urlparse(old_url).hostname
        if old_hostname:
            subprocess.run(f"rm -rf /etc/gitlab/ssl/{old_hostname}* 2>/dev/null", shell=True, capture_output=True)
            subprocess.run(f"rm -rf /var/opt/gitlab/nginx/conf/ssl/{old_hostname}* 2>/dev/null", shell=True, capture_output=True)
            print(f"✓ SSL certificates for '{old_hostname}' cleared")
        
        # Note: Do NOT clear /opt/gitlab/sv/*/supervise/* — those are runit
        # supervision pipes created by runsvdir. Deleting them causes the
        # "wait for <service> service socket" hang during reconfigure.
        
        # Clear tmp files
        subprocess.run("rm -rf /var/opt/gitlab/tmp/* 2>/dev/null", shell=True, capture_output=True)
        print("✓ Temporary files cleared")
    
    def _check_and_handle_url_change(self, non_interactive=False):
        """Check if GitLab URL has changed and handle cleanup if needed
        
        Args:
            non_interactive: If True, automatically cleanup without prompting
        """
        current_url = self._get_current_gitlab_url()
        
        if current_url:
            print(f"GitLab is already configured with URL: {current_url}")
            print(f"New URL to configure: {self.gitlab_url}")
            
            # Normalize URLs for comparison (remove trailing slashes, ensure same scheme)
            current_normalized = current_url.rstrip('/')
            new_normalized = self.gitlab_url.rstrip('/')
            
            if current_normalized != new_normalized:
                print("⚠ URL change detected!")
                if non_interactive:
                    print("Non-interactive mode: Automatically cleaning up old configuration")
                    self._cleanup_old_gitlab_config(current_url)
                    return True
                else:
                    response = input("Do you want to clean up the old configuration and reconfigure with the new URL? (yes/no): ").strip().lower()
                    if response == 'yes':
                        self._cleanup_old_gitlab_config(current_url)
                        return True
                    else:
                        print("Keeping existing configuration. Note: GitLab may continue to use the old URL.")
                        return False
            else:
                print("✓ URL matches, no change needed")
                return False
        
        return False

    def _remove_all_rich_rules(self):
        """Remove all existing rich rules from the default firewall zone."""
        try:
            result = subprocess.run(
                "firewall-cmd --list-rich-rules",
                shell=True, capture_output=True, text=True
            )
            for rule in result.stdout.strip().splitlines():
                rule = rule.strip()
                if rule:
                    subprocess.run(
                        f"firewall-cmd --permanent --remove-rich-rule='{rule}'",
                        shell=True, capture_output=True
                    )
            print("✓ Cleared existing rich rules")
        except Exception as e:
            print(f"⚠ Could not clear rich rules: {e}")

    def configure_firewall(self, allowed_endpoints=None):
        """Configure firewall rules for GitLab access.
        
        Args:
            allowed_endpoints: List of IP addresses or CIDR ranges to allow access from.
                             If None, allows access from anywhere (0.0.0.0/0).
                             Examples: ['192.168.1.0/24', '10.0.0.100', '172.16.0.0/16']
        """
        print("\n" + "=" * 60)
        print("Configuring Firewall for GitLab Access")
        print("=" * 60)
        
        try:
            # Check if firewalld is running
            result = subprocess.run(
                "systemctl is-active firewalld",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print("⚠ firewalld is not running. Attempting to start it...")
                subprocess.run("systemctl start firewalld", shell=True, check=True)
                subprocess.run("systemctl enable firewalld", shell=True, check=True)
                print("✓ firewalld started and enabled")
            
            # Get current firewall zone
            zone_result = subprocess.run(
                "firewall-cmd --get-default-zone",
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            default_zone = zone_result.stdout.strip()
            print(f"Firewall default zone: {default_zone}")
            
            if allowed_endpoints:
                print(f"Configuring restrictive access for endpoints: {', '.join(allowed_endpoints)}")
                
                # Remove any existing rich rules (cleanup from previous runs)
                self._remove_all_rich_rules()
                
                # First remove general http/https services
                subprocess.run(
                    f"firewall-cmd --permanent --remove-service=http",
                    shell=True,
                    capture_output=True
                )
                subprocess.run(
                    f"firewall-cmd --permanent --remove-service=https",
                    shell=True,
                    capture_output=True
                )
                
                # Add rich rules for each endpoint
                for endpoint in allowed_endpoints:
                    # Add HTTP rule for this endpoint
                    http_rule = (
                        f'rule family="ipv4" source address="{endpoint}" '
                        f'service name="http" accept'
                    )
                    subprocess.run(
                        f'firewall-cmd --permanent --add-rich-rule=\'{http_rule}\'',
                        shell=True,
                        check=True
                    )
                    print(f"✓ Added HTTP access for {endpoint}")
                    
                    # Add HTTPS rule for this endpoint
                    https_rule = (
                        f'rule family="ipv4" source address="{endpoint}" '
                        f'service name="https" accept'
                    )
                    subprocess.run(
                        f'firewall-cmd --permanent --add-rich-rule=\'{https_rule}\'',
                        shell=True,
                        check=True
                    )
                    print(f"✓ Added HTTPS access for {endpoint}")
            else:
                print("Configuring public access (allows HTTP/HTTPS from anywhere)")
                # Remove any existing rich rules (cleanup from previous restrictive runs)
                self._remove_all_rich_rules()
                print("✓ Removed restrictive rules")
                
                # Allow HTTP and HTTPS from anywhere
                subprocess.run(
                    "firewall-cmd --permanent --add-service=http",
                    shell=True,
                    check=True
                )
                print("✓ Added HTTP service (public access)")
                
                subprocess.run(
                    "firewall-cmd --permanent --add-service=https",
                    shell=True,
                    check=True
                )
                print("✓ Added HTTPS service (public access)")
            
            # Reload firewall to apply changes
            subprocess.run("firewall-cmd --reload", shell=True, check=True)
            print("✓ Firewall reloaded successfully")
            
            # Show current rules
            print("\nCurrent firewall rules:")
            subprocess.run("firewall-cmd --list-all", shell=True)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"✗ Error configuring firewall: {e}")
            print("⚠ Please configure firewall manually:")
            if allowed_endpoints:
                for endpoint in allowed_endpoints:
                    print(f"  firewall-cmd --permanent --add-rich-rule='rule family=\"ipv4\" source address=\"{endpoint}\" service name=\"http\" accept'")
                    print(f"  firewall-cmd --permanent --add-rich-rule='rule family=\"ipv4\" source address=\"{endpoint}\" service name=\"https\" accept'")
            else:
                print("  firewall-cmd --permanent --add-service=http")
                print("  firewall-cmd --permanent --add-service=https")
            print("  firewall-cmd --reload")
            return False
        except Exception as e:
            print(f"✗ Unexpected error configuring firewall: {e}")
            return False
    
    def wait_for_gitlab(self, max_retries=60, retry_interval=10):
        """Wait for GitLab to be ready.

        Tries the configured URL first, then falls back to localhost to handle
        cases where the hostname is not yet resolvable but GitLab is running.
        """
        print("\nWaiting for GitLab to be ready...")
        print("This may take 5-10 minutes for first startup...")

        # Build list of URLs to probe (configured URL + localhost fallback)
        probe_urls = [f"{self.gitlab_url}/api/v4/version"]
        parsed = urlparse(self.gitlab_url)
        scheme = parsed.scheme or "http"
        port = parsed.port
        if not port:
            port = 443 if scheme == "https" else 80
        localhost_url = f"{scheme}://127.0.0.1:{port}/api/v4/version"
        if localhost_url not in probe_urls:
            probe_urls.append(localhost_url)

        for i in range(max_retries):
            for url in probe_urls:
                try:
                    response = requests.get(url, timeout=10, verify=False)
                    if response.status_code in [200, 401]:
                        print(f"✓ GitLab is ready (responded on {url})")
                        return True
                except requests.exceptions.ConnectionError:
                    pass
                except Exception:
                    pass

            if (i + 1) % 6 == 0:
                print(f"Still waiting... ({i+1}/{max_retries}) - {(i+1)*retry_interval}s elapsed")
            time.sleep(retry_interval)
        
        print("✗ GitLab did not become ready in time")
        return False
    
    def generate_admin_token(self, config):
        """Generate admin personal access token using gitlab-rails console or API"""
        print("Attempting to generate Personal Access Token...")
        
        # Try with the provided username first, then fallback to 'root' (GitLab default)
        usernames_to_try = [config['admin_username']]
        if config['admin_username'] != 'root':
            usernames_to_try.append('root')
        
        for username in usernames_to_try:
            # Method 1: Use gitlab-rails console (most reliable for fresh installs)
            try:
                rails_cmd = (
                    "gitlab-rails runner \""
                    "token = User.find_by_username('" + username + "')"
                    ".personal_access_tokens.create("
                    "scopes: ['api'], "
                    "name: 'cicd-automation', "
                    "expires_at: 365.days.from_now"
                    "); puts token.token\""
                )
                result = subprocess.run(
                    rails_cmd, shell=True, capture_output=True, text=True, timeout=120
                )
                if result.returncode == 0 and result.stdout.strip():
                    token = result.stdout.strip().split('\n')[-1]
                    if len(token) >= 20:
                        print(f"✓ Token generated via gitlab-rails (user: {username})")
                        return token
            except Exception as e:
                print(f"gitlab-rails method failed for user '{username}': {e}")
        
        # Method 2: Use OAuth password grant (try with both usernames)
        for username in usernames_to_try:
            try:
                response = requests.post(
                    f"{self.gitlab_url}/oauth/token",
                    data={
                        'grant_type': 'password',
                        'username': username,
                        'password': config['admin_password']
                    },
                    verify=False,
                    timeout=30
                )
                if response.status_code == 200:
                    oauth_token = response.json().get('access_token')
                    if oauth_token:
                        # Use OAuth token to create a PAT
                        pat_response = requests.post(
                            f"{self.gitlab_url}/api/v4/users/1/personal_access_tokens",
                            headers={'Authorization': f'Bearer {oauth_token}'},
                            json={'name': 'cicd-automation', 'scopes': ['api']},
                            verify=False,
                            timeout=30
                        )
                        if pat_response.status_code in [200, 201]:
                            token = pat_response.json().get('token')
                            if token:
                                print("✓ Token generated via OAuth")
                                return token
            except Exception as e:
                print(f"OAuth method failed for user '{username}': {e}")
        
        print("✗ Could not generate token automatically")
        print("Please create a token manually:")
        print(f"  1. Go to {self.gitlab_url}/-/user_settings/personal_access_tokens")
        print("  2. Create a token with 'api' scope")
        
        # Prompt for manual token input
        manual_token = input("Paste your token here (or press Enter to abort): ").strip()
        return manual_token or None
    
    def _find_existing_project(self, config):
        """Look up an existing project by path or name and set self.project_id."""
        headers = {"PRIVATE-TOKEN": self.admin_token}

        # Try exact path lookup first (most reliable)
        encoded_path = config["project_path"].replace("/", "%2F")
        try:
            resp = requests.get(
                f"{self.gitlab_url}/api/v4/projects/{encoded_path}",
                headers=headers,
                verify=False,
            )
            if resp.status_code == 200:
                project = resp.json()
                self.project_id = project["id"]
                print(f"✓ Found existing project: {project.get('web_url', config['project_path'])}")
                return True
        except Exception:
            pass

        # Fallback: search by name
        try:
            resp = requests.get(
                f"{self.gitlab_url}/api/v4/projects",
                headers=headers,
                params={"search": config["project_name"]},
                verify=False,
            )
            if resp.status_code == 200:
                for project in resp.json():
                    if project.get("path_with_namespace") == config["project_path"]:
                        self.project_id = project["id"]
                        print(f"✓ Found existing project: {project.get('web_url', config['project_path'])}")
                        return True
        except Exception:
            pass

        return False

    def create_project(self, config):
        """Create GitLab project, or reuse it if it already exists."""
        print("\n" + "=" * 60)
        print("Creating GitLab Project...")
        print("=" * 60)

        headers = {"PRIVATE-TOKEN": self.admin_token}

        project_data = {
            "name": config["project_name"],
            "path": config["project_name"],
            "namespace_id": self._get_namespace_id(
                config["project_path"].split("/")[0], headers
            ),
        }

        try:
            response = requests.post(
                f"{self.gitlab_url}/api/v4/projects",
                headers=headers,
                json=project_data,
                verify=False,
            )

            if response.status_code in [200, 201]:
                project = response.json()
                self.project_id = project["id"]
                print(f"✓ Project created: {project['web_url']}")
                return True

            # GitLab returns 400 "has already been taken" or 409 Conflict
            # when the project already exists — handle both.
            already_exists = False
            if response.status_code == 409:
                already_exists = True
            elif response.status_code == 400:
                try:
                    body = response.json()
                    msgs = json.dumps(body)
                    if "already been taken" in msgs:
                        already_exists = True
                except Exception:
                    pass

            if already_exists:
                print("Project already exists, looking it up...")
                if self._find_existing_project(config):
                    return True
                print("✗ Project exists but could not retrieve its ID")
                return False

            print(f"✗ Error creating project: {response.status_code} {response.text}")
            return False
        except Exception as e:
            print(f"✗ Error creating project: {e}")
            return False
    
    def _get_namespace_id(self, namespace, headers):
        """Get namespace ID from namespace name"""
        try:
            response = requests.get(
                f"{self.gitlab_url}/api/v4/namespaces?search={namespace}",
                headers=headers,
                verify=False
            )
            namespaces = response.json()
            if namespaces:
                return namespaces[0]['id']
        except:
            pass
        return None
    
    def configure_ci_cd_variables(self):
        """Configure CI/CD variables from the loaded configuration"""
        print("\n" + "="*60)
        print("Configuring CI/CD Variables...")
        print("="*60)
        
        if not self.project_id:
            print("✗ Project ID not set")
            return False
        
        headers = {'PRIVATE-TOKEN': self.admin_token}
        
        # Auto-detect clusters from clusters directory
        clusters_list = []
        if self.clusters_dir.exists():
            for cluster_dir in sorted(self.clusters_dir.iterdir()):
                if cluster_dir.is_dir() and (cluster_dir / "cluster.env").exists():
                    clusters_list.append(cluster_dir.name)
        
        # Add CLUSTERS variable to config
        if clusters_list:
            clusters_value = ",".join(clusters_list)
            self.config["CLUSTERS"] = clusters_value
            print(f"Auto-detected clusters: {clusters_value}")
        
        # Configure each variable
        for key, value in self.config.items():
            if value:  # Only configure non-empty values
                try:
                    # Check if variable already exists
                    response = requests.get(
                        f"{self.gitlab_url}/api/v4/projects/{self.project_id}/variables/{key}",
                        headers=headers,
                        verify=False
                    )
                    
                    if response.status_code == 200:
                        # Update existing variable
                        response = requests.put(
                            f"{self.gitlab_url}/api/v4/projects/{self.project_id}/variables/{key}",
                            headers=headers,
                            json={'value': str(value)},
                            verify=False
                        )
                        print(f"✓ Updated variable: {key}")
                    else:
                        # Create new variable
                        response = requests.post(
                            f"{self.gitlab_url}/api/v4/projects/{self.project_id}/variables",
                            headers=headers,
                            json={
                                'key': key,
                                'value': str(value),
                                'variable_type': 'env_var',
                                'protected': False,
                                'masked': False
                            },
                            verify=False
                        )
                        print(f"✓ Created variable: {key}")
                except Exception as e:
                    print(f"✗ Error configuring variable {key}: {e}")
        
        print(f"✓ Configured {len(self.config)} CI/CD variables")
        return True
    
    def configure_cluster_variables(self):
        """Configure cluster-specific variables"""
        print("\n" + "="*60)
        print("Configuring Cluster Variables...")
        print("="*60)
        
        if not os.path.exists(self.clusters_dir):
            print("✗ Clusters directory not found")
            return False
        
        headers = {'PRIVATE-TOKEN': self.admin_token}
        cluster_configs = {}
        
        # Load cluster configurations
        for cluster_dir in os.listdir(self.clusters_dir):
            cluster_env = os.path.join(self.clusters_dir, cluster_dir, 'cluster.env')
            if os.path.exists(cluster_env):
                try:
                    with open(cluster_env, 'r') as f:
                        cluster_config = {}
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                cluster_config[key.strip()] = value.strip().strip('"\'')
                        cluster_configs[cluster_dir] = cluster_config
                        print(f"✓ Loaded configuration for cluster: {cluster_dir}")
                except Exception as e:
                    print(f"✗ Error loading cluster {cluster_dir}: {e}")
        
        # Configure cluster variables
        for cluster_name, cluster_config in cluster_configs.items():
            for key, value in cluster_config.items():
                variable_name = f"{cluster_name.upper()}_{key}"

                # Skip values that reference GitLab CI/CD variables (${VAR} syntax)
                # These are meant to be resolved at pipeline runtime, not set here
                if '${' in value and '}' in value:
                    print(f"  Skipping {variable_name} (contains variable reference: {value})")
                    continue

                try:
                    response = requests.post(
                        f"{self.gitlab_url}/api/v4/projects/{self.project_id}/variables",
                        headers=headers,
                        json={
                            'key': variable_name,
                            'value': str(value),
                            'variable_type': 'env_var',
                            'protected': False,
                            'masked': True if 'PASS' in key else False
                        },
                        verify=False
                    )
                    if response.status_code in [200, 201]:
                        print(f"✓ Created cluster variable: {variable_name}")
                except Exception as e:
                    print(f"✗ Error configuring cluster variable {variable_name}: {e}")
        
        return True

    def configure_cluster_passwords(self):
        """Auto-create cluster password CI/CD variables as masked placeholders.

        For each cluster that references a variable like ${CLUSTER1_TARGET_PASS}
        in its cluster.env, this creates (or updates) the corresponding GitLab
        CI/CD variable with a placeholder value. The user can then set the real
        password in the GitLab UI under Settings > CI/CD > Variables.
        No interactive prompt is used.
        """
        print("\n" + "=" * 60)
        print("Configuring Cluster Password Variables")
        print("=" * 60)

        if not self.project_id or not self.admin_token:
            print("✗ Project ID or admin token not set")
            return False

        if not os.path.exists(self.clusters_dir):
            print("✗ Clusters directory not found")
            return False

        headers = {"PRIVATE-TOKEN": self.admin_token}

        # Discover clusters and auto-create password variables
        for cluster_dir in sorted(os.listdir(self.clusters_dir)):
            cluster_env = os.path.join(self.clusters_dir, cluster_dir, "cluster.env")
            if not os.path.exists(cluster_env):
                continue

            # Read cluster.env to find variable references for TARGET_PASS
            with open(cluster_env, "r") as f:
                for line in f:
                    if "TARGET_PASS" in line and "${CLUSTER" in line:
                        match = re.search(r'\$\{([A-Z0-9_]+)\}', line)
                        if match:
                            var_name = match.group(1)
                            # Create as a masked CI/CD variable with placeholder
                            self._set_gitlab_variable(
                                headers, var_name, "CHANGE_ME_IN_GITLAB_UI"
                            )
                            print(
                                f"  Set {var_name} as CI/CD variable "
                                f"(update in GitLab UI: Settings > CI/CD > Variables)"
                            )
                        break

        print("\n✓ Cluster password variables configured as CI/CD variables")
        print("  Update the actual passwords in GitLab UI: Settings > CI/CD > Variables")
        return True

    def _set_gitlab_variable(self, headers, key, value):
        """Set a GitLab CI/CD variable."""
        try:
            # Check if variable exists
            response = requests.get(
                f"{self.gitlab_url}/api/v4/projects/{self.project_id}/variables/{key}",
                headers=headers,
                verify=False,
            )
            if response.status_code == 200:
                # Update existing variable
                response = requests.put(
                    f"{self.gitlab_url}/api/v4/projects/{self.project_id}/variables/{key}",
                    headers=headers,
                    json={"value": str(value)},
                    verify=False,
                )
                print(f"✓ Updated variable: {key}")
            else:
                # Create new variable
                response = requests.post(
                    f"{self.gitlab_url}/api/v4/projects/{self.project_id}/variables",
                    headers=headers,
                    json={
                        "key": key,
                        "value": str(value),
                        "variable_type": "env_var",
                        "protected": False,
                        "masked": True,
                    },
                    verify=False,
                )
                print(f"✓ Created variable: {key}")
        except Exception as e:
            print(f"✗ Error setting variable {key}: {e}")

    def generate_and_upload_datasets(self, args):
        """Generate per-cluster datasets and upload them to the GitLab repo.

        Uses generate_multi_cluster_datasets.py to create datasets from
        omnia-artifactory templates, then commits them to the GitLab repo
        via the API so they are visible and editable in the GitLab UI.
        """
        print("\n" + "=" * 60)
        print("Generating Multi-Cluster Datasets...")
        print("=" * 60)

        artifactory_path = Path(args.artifactory_path)
        gen_script = artifactory_path / "utility" / "generate_datasets.py"
        if not gen_script.exists():
            print(f"ERROR: generate_datasets.py not found at {gen_script}")
            print("Use --artifactory-path to specify the omnia-artifactory location.")
            return False

        # Build the command to invoke the multi-cluster generator
        script_dir = Path(__file__).resolve().parent
        mc_gen_script = script_dir / "generate_multi_cluster_datasets.py"
        if not mc_gen_script.exists():
            print(f"ERROR: generate_multi_cluster_datasets.py not found at {mc_gen_script}")
            return False

        cmd = [
            sys.executable, str(mc_gen_script),
            "--artifactory-path", str(artifactory_path),
            "--base-tc", args.base_tc,
            "--clean",
        ]
        if args.clusters:
            cmd.extend(["--clusters", args.clusters])

        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False)
        if result.returncode != 0:
            print("ERROR: Dataset generation failed")
            return False

        print("\nDatasets generated successfully.")

        # Upload to GitLab if we have a project ID and token
        if self.project_id and self.admin_token:
            self._upload_datasets_to_gitlab()

        return True

    def _commit_to_gitlab(self, actions, commit_message, max_retries=3, retry_delay=10):
        """Commit a list of file actions to GitLab with retry logic.

        Returns True on success, False on failure.
        """
        headers = {"PRIVATE-TOKEN": self.admin_token}
        commit_data = {
            "branch": "main",
            "commit_message": commit_message,
            "actions": actions,
        }

        last_error = None
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    f"{self.gitlab_url}/api/v4/projects/{self.project_id}"
                    "/repository/commits",
                    headers=headers,
                    json=commit_data,
                    verify=False,
                    timeout=120,
                )
                if resp.status_code in [200, 201]:
                    return True
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                if resp.status_code in [500, 502, 503, 504] and attempt < max_retries - 1:
                    print(f"    GitLab returned {resp.status_code}, retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)
                    continue
                break
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    print(f"    Connection error, retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)
                    continue
                break

        print(f"    ✗ Failed: {last_error}")
        return False

    def _build_file_action(self, file_path, repo_path):
        """Build a commit action dict for a file (create or update)."""
        headers = {"PRIVATE-TOKEN": self.admin_token}

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = base64.b64encode(file_path.read_bytes()).decode("ascii")

        import urllib.parse
        encoded_path = urllib.parse.quote(repo_path, safe="")
        check_resp = requests.get(
            f"{self.gitlab_url}/api/v4/projects/{self.project_id}"
            f"/repository/files/{encoded_path}?ref=main",
            headers=headers,
            verify=False,
            timeout=30,
        )
        action_type = "update" if check_resp.status_code == 200 else "create"

        return {
            "action": action_type,
            "file_path": repo_path,
            "content": content,
        }

    def _upload_datasets_to_gitlab(self):
        """Upload generated datasets to GitLab, one commit per cluster."""
        print("\nUploading datasets to GitLab repository...")

        datasets_dir = self.datasets_dir

        # Only upload cluster dataset directories (e.g. cluster1_config/)
        skip_dirs = {"project_default", "project_new_cluster", "templates",
                     "user_registry_example"}
        dataset_dirs = [
            d for d in sorted(datasets_dir.iterdir())
            if d.is_dir() and d.name not in skip_dirs
                            and d.name.endswith("_config")
        ]

        if not dataset_dirs:
            print("No generated datasets found to upload.")
            return

        total_files = 0
        failed_dirs = []

        # Commit one cluster at a time to avoid overloading GitLab
        for dataset_dir in dataset_dirs:
            actions = []
            for file_path in sorted(dataset_dir.iterdir()):
                if file_path.is_file():
                    repo_path = f"datasets/{dataset_dir.name}/{file_path.name}"
                    actions.append(self._build_file_action(file_path, repo_path))

            if not actions:
                continue

            print(f"  Uploading {dataset_dir.name}/ ({len(actions)} files)...")
            ok = self._commit_to_gitlab(
                actions,
                f"Add/update dataset: {dataset_dir.name}\n\n"
                "Auto-generated by install_gitlab_cicd.py --generate-datasets",
            )
            if ok:
                total_files += len(actions)
                print(f"    ✓ {dataset_dir.name}: {len(actions)} files committed")
            else:
                failed_dirs.append(dataset_dir.name)

            # Small pause between commits to let GitLab recover
            if dataset_dir != dataset_dirs[-1]:
                time.sleep(3)

        print(f"\n✓ Committed {total_files} dataset files to GitLab")
        if failed_dirs:
            print(f"✗ Failed clusters: {', '.join(failed_dirs)}")
            print("  You can manually commit these from datasets/ directory.")

    def upload_config_files(self):
        """Upload the global omnia_test_config.yml to the GitLab repo root.

        Per-cluster credentials are NOT uploaded here - they are uploaded as
        pipeline/clusters/<name>/credentials.yml by upload_pipeline_files().
        """
        print("\n" + "=" * 60)
        print("Uploading Global Config File to GitLab Repo...")
        print("=" * 60)

        if not self.project_id or not self.admin_token:
            print("✗ Project ID or admin token not set")
            return False

        config_path = _repo_root() / "omnia_test_config.yml"
        if not config_path.exists():
            print(f"  ✗ {config_path} not found, skipping")
            return True

        action = self._build_file_action(config_path, "omnia_test_config.yml")
        ok = self._commit_to_gitlab([action], "Update omnia_test_config.yml")
        if ok:
            print("✓ Committed omnia_test_config.yml to GitLab")
        else:
            print("WARNING: Failed to commit omnia_test_config.yml")

        return True

    def _get_dataset_from_env(self, env_path):
        """Read the DATASET value from a cluster.env file."""
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DATASET="):
                        return line.split("=", 1)[1].strip().strip("\"'")
        except Exception:
            pass
        return env_path.parent.name + "_config"  # fallback

    def configure_https(self):
        """Configure GitLab for HTTPS with self-signed certificate."""
        print("\n" + "=" * 60)
        print("Configuring HTTPS for GitLab")
        print("=" * 60)

        gitlab_rb = "/etc/gitlab/gitlab.rb"
        ssl_dir = "/etc/gitlab/ssl"

        # Get the hostname/IP from gitlab_url
        from urllib.parse import urlparse
        parsed = urlparse(self.gitlab_url)
        hostname = parsed.hostname or parsed.netloc

        print(f"  Hostname: {hostname}")

        # Create SSL directory
        if not os.path.exists(ssl_dir):
            os.makedirs(ssl_dir, mode=0o700)
            print(f"  ✓ Created {ssl_dir}")

        # Generate self-signed certificate
        cert_path = f"{ssl_dir}/{hostname}.crt"
        key_path = f"{ssl_dir}/{hostname}.key"

        if os.path.exists(cert_path) and os.path.exists(key_path):
            print(f"  ✓ Certificate already exists: {cert_path}")
        else:
            print(f"  Generating self-signed certificate for {hostname}...")
            try:
                subprocess.run(
                    [
                        "openssl", "req", "-new", "-x509", "-days", "365", "-nodes",
                        "-out", cert_path,
                        "-keyout", key_path,
                        "-subj", f"/CN={hostname}"
                    ],
                    check=True,
                    capture_output=True
                )
                os.chmod(cert_path, 0o644)
                os.chmod(key_path, 0o600)
                print(f"  ✓ Certificate generated: {cert_path}")
            except subprocess.CalledProcessError as e:
                print(f"  ✗ Failed to generate certificate: {e.stderr.decode()}")
                return False

        # Update external_url in gitlab.rb to use HTTPS
        https_url = f"https://{hostname}"
        print(f"  Setting external_url to: {https_url}")

        try:
            with open(gitlab_rb, 'r') as f:
                content = f.read()

            # Replace or add external_url
            import re
            if re.search(r'^external_url\s+', content, re.MULTILINE):
                content = re.sub(
                    r'^external_url\s+.*$',
                    f"external_url '{https_url}'",
                    content,
                    flags=re.MULTILINE
                )
            else:
                content += f"\nexternal_url '{https_url}'\n"

            with open(gitlab_rb, 'w') as f:
                f.write(content)

            print(f"  ✓ Updated {gitlab_rb}")

            # Reconfigure GitLab
            print("  Running gitlab-ctl reconfigure...")
            result = subprocess.run(
                ["gitlab-ctl", "reconfigure"],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                print("  ✓ GitLab reconfigured successfully")
                self.gitlab_url = https_url  # Update internal URL reference
                return True
            else:
                print(f"  ✗ Reconfigure failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"  ✗ Error configuring HTTPS: {e}")
            return False

    def register_gitlab_runner(self):
        """Register a GitLab runner for the project."""
        print("\n" + "=" * 60)
        print("Registering GitLab Runner")
        print("=" * 60)

        if not self.project_id or not self.admin_token:
            print("✗ Project ID or admin token not set, skipping runner registration")
            return False

        try:
            # Get project registration token
            headers = {'PRIVATE-TOKEN': self.admin_token}
            response = requests.get(
                f"{self.gitlab_url}/api/v4/projects/{self.project_id}",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            project_data = response.json()

            # Get runners registration token
            response = requests.get(
                f"{self.gitlab_url}/api/v4/projects/{self.project_id}/runners",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            # For project runners, we need to get the registration token from project settings
            # Using a different endpoint for registration token
            response = requests.post(
                f"{self.gitlab_url}/api/v4/user/runners",
                headers=headers,
                json={
                    'runner_type': 'project_type',
                    'project_id': self.project_id,
                    'group_id': None,
                    'description': 'omnia-automation-runner',
                    'paused': False,
                    'locked': False,
                    'run_untagged': True,
                    'tag_list': ['docker', 'shell'],
                    'access_level': 'not_protected',
                    'maximum_timeout': 3600
                },
                timeout=30
            )

            if response.status_code == 201:
                runner_data = response.json()
                token = runner_data.get('token')
                print(f"✓ Runner created with token: {token[:8]}...")

                # Register the runner locally
                runner_name = "omnia-automation-runner"
                runner_url = self.gitlab_url

                # Register using gitlab-runner register command
                cmd = [
                    'gitlab-runner', 'register',
                    '--non-interactive',
                    '--url', runner_url,
                    '--token', token,
                    '--executor', 'shell',
                    '--description', runner_name,
                ]

                # Add TLS CA file for self-signed certs
                parsed = urllib.parse.urlparse(runner_url)
                cert_path = f"/etc/gitlab/ssl/{parsed.hostname}.crt"
                if os.path.exists(cert_path):
                    cmd.extend(['--tls-ca-file', cert_path])

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                if result.returncode == 0:
                    print("✓ GitLab runner registered successfully")
                    # Set concurrent to 10 for parallel child pipelines
                    config_path = '/etc/gitlab-runner/config.toml'
                    if os.path.exists(config_path):
                        with open(config_path, 'r') as f:
                            config = f.read()
                        config = config.replace('concurrent = 1', 'concurrent = 10', 1)
                        with open(config_path, 'w') as f:
                            f.write(config)
                        print("✓ Runner concurrency set to 10")
                    # Start/restart the runner service
                    subprocess.run(['gitlab-runner', 'restart'], capture_output=True, timeout=10)
                    print("✓ GitLab runner service started")
                    return True
                else:
                    print(f"✗ Failed to register runner: {result.stderr}")
                    return False
            else:
                print(f"✗ Failed to create runner token: {response.text}")
                return False

        except Exception as e:
            print(f"✗ Error registering GitLab runner: {e}")
            return False

    def upload_pipeline_files(self):
        """Upload all pipeline + cluster files to GitLab in a single commit.

        GitLab repo structure:
        - .gitlab-ci.yml                              (parent pipeline)
        - .gitlab-ci-cluster.yml                      (child pipeline template)
        - send_email.py                               (email helper)
        - clusters/<name>/cluster.env                 (per-cluster connection details)
        - clusters/<name>/credentials.yml             (per-cluster credentials)
        - clusters/<name>/omnia_test_config.yml       (per-cluster test config)
        - datasets/<dataset>/*                        (dataset-specific config files)
        """
        print("\n" + "=" * 60)
        print("Uploading Pipeline & Cluster Files to GitLab...")
        print("=" * 60)

        if not self.project_id or not self.admin_token:
            print("✗ Project ID or admin token not set, skipping upload")
            return False

        script_dir = Path(__file__).resolve().parent
        repo_root = script_dir.parent
        actions = []
        file_list = []

        # Pipeline files at root level in GitLab
        files_to_upload = [
            (script_dir / ".gitlab-ci.yml", ".gitlab-ci.yml"),
            (script_dir / ".gitlab-ci-cluster.yml", ".gitlab-ci-cluster.yml"),
            (script_dir / "send_email.py", "send_email.py"),
        ]

        # Per-cluster files from pipeline/clusters/<name>/ → clusters/<name>/
        if self.clusters_dir.exists():
            for cluster_dir in sorted(self.clusters_dir.iterdir()):
                if cluster_dir.is_dir():
                    for fname in ("cluster.env", "credentials.yml", "omnia_test_config.yml"):
                        fpath = cluster_dir / fname
                        if fpath.exists():
                            files_to_upload.append(
                                (fpath, f"clusters/{cluster_dir.name}/{fname}")
                            )

        # Dataset files from datasets/<dataset>/ → datasets/<dataset>/
        datasets_dir = repo_root / "datasets"
        if datasets_dir.exists():
            for dataset_dir in sorted(datasets_dir.iterdir()):
                if dataset_dir.is_dir():
                    for fpath in sorted(dataset_dir.iterdir()):
                        if fpath.is_file():
                            files_to_upload.append(
                                (fpath, f"datasets/{dataset_dir.name}/{fpath.name}")
                            )

        # Build actions
        for local_path, repo_path in files_to_upload:
            if local_path.exists():
                actions.append(self._build_file_action(local_path, repo_path))
                file_list.append(repo_path)
            else:
                print(f"  ✗ Not found: {local_path}")

        if not actions:
            print("No pipeline files found to upload.")
            return False

        print(f"  Committing {len(actions)} pipeline files...")
        ok = self._commit_to_gitlab(
            actions,
            "Add/update pipeline configuration files\n\n"
            "Includes .gitlab-ci.yml, .gitlab-ci-cluster.yml, send_email.py,\n"
            "cluster configs, and dataset files.\n"
            "Auto-committed by install_gitlab_cicd.py",
        )

        if ok:
            print(f"\n✓ Uploaded {len(file_list)} pipeline files:")
            for f in file_list:
                print(f"    - {f}")
            return True
        else:
            print(f"\n✗ Failed to upload pipeline files.")
            print("  You can manually commit from pipeline/ directory:")
            print("    cd /root/rohith/omnia-artifactory")
            print("    git add pipeline/ && git commit -m 'Add pipeline' && git push")
            return False
    
    def generate_setup_instructions(self, config):
        """Generate setup instructions for the user"""
        print("\n" + "="*60)
        print("Setup Instructions")
        print("="*60)
        
        instructions = f"""
GitLab CI/CD Configuration Complete!

GitLab Details:
- URL: {self.gitlab_url}
- Project: {config['project_name']}
- Project Path: {config['project_path']}

Repository Layout in GitLab (uploaded automatically):
- .gitlab-ci.yml                              - Parent pipeline (triggers child pipelines)
- .gitlab-ci-cluster.yml                      - Child pipeline (per-cluster stages)
- send_email.py                               - Email notification helper
- clusters/<name>/cluster.env                 - Per-cluster connection details
- clusters/<name>/credentials.yml             - Per-cluster credentials
- clusters/<name>/omnia_test_config.yml       - Per-cluster test config
- datasets/<dataset>/*                        - Dataset-specific config files
                                             (omnia_config.yml, storage_config.yml, etc.)

Pipeline Architecture:
- Parent pipeline triggers an independent child pipeline per cluster
- Each cluster runs all stages independently
- If one cluster fails, it does not affect the others

Admin Credentials (saved locally in pipeline/, encrypted):
- pipeline/gitlab_admin_credentials.yml (ansible-vault encrypted)
- Decrypt manually with:
  ansible-vault view pipeline/gitlab_admin_credentials.yml \\
    --vault-password-file pipeline/.omnia_test_credentials.key

Next Steps:
1. Access GitLab at {self.gitlab_url}
2. Login with admin credentials
3. Navigate to your project: {config['project_path']}
4. Trigger the pipeline from CI/CD > Pipelines > Run pipeline

CI/CD Variables:
- {len(self.config)} pipeline variables configured
- Cluster password variables (CLUSTER1_TARGET_PASS, etc.) created
  as CI/CD variables with placeholder values
- Update passwords in: Project > Settings > CI/CD > Variables

For multi-cluster execution:
1. Update cluster passwords in GitLab CI/CD Variables
2. Edit pipeline/clusters/<name>/cluster.env  (target IP, DATASET, BASE_TC)
3. Edit pipeline/clusters/<name>/omnia_test_config.yml (cluster-specific config)
4. Edit pipeline/clusters/<name>/credentials.yml (SSH/LDAP credentials)
5. Edit datasets/<dataset>/ files (omnia_config.yml, storage_config.yml, etc.)
6. Update the CLUSTER matrix in .gitlab-ci.yml when adding/removing clusters
7. Re-run install_gitlab_cicd.py to upload changes to GitLab

HTTPS Configuration:
- To enable HTTPS, run with --enable-https flag
- This generates a self-signed certificate and configures GitLab for HTTPS
- Example: python3 install_gitlab_cicd.py --enable-https
"""
        print(instructions)

        # Save instructions to file
        script_dir = Path(__file__).resolve().parent
        instructions_file = script_dir / "gitlab_setup_instructions.txt"
        with open(instructions_file, 'w') as f:
            f.write(instructions)
        print(f"✓ Setup instructions saved to: {instructions_file}")

def main():
    script_dir = Path(__file__).resolve().parent
    default_artifactory_path = script_dir.parent

    parser = argparse.ArgumentParser(description='Install and configure GitLab CI/CD for multi-cluster pipeline')
    parser.add_argument('--gitlab-url', help='GitLab server URL')
    parser.add_argument('--admin-username', default='root', help='GitLab admin username (default shown in prompt)')
    parser.add_argument('--admin-password', help='GitLab admin password (pre-fills the prompt)')
    parser.add_argument('--admin-token', help='GitLab personal access token')
    parser.add_argument('--project-name', default='omnia-automation', help='GitLab project name (default shown in prompt)')
    parser.add_argument('--project-path', default='root/omnia-automation', help='GitLab project path (default shown in prompt)')
    parser.add_argument('--skip-install', action='store_true', help='Skip GitLab installation (assume already installed)')
    parser.add_argument('--generate-datasets', action='store_true', help='Generate per-cluster datasets using generate_datasets.py from omnia-artifactory')
    parser.add_argument('--artifactory-path', default=str(default_artifactory_path), help='Path to omnia-artifactory repo (for dataset generation)')
    parser.add_argument('--base-tc', default='tc01_production_standard', help='Base test case for dataset generation (default: tc01_production_standard)')
    parser.add_argument('--clusters', help='Comma-separated cluster names for dataset generation (default: all)')
    parser.add_argument('--configure-firewall', action='store_true', help='Configure firewall for GitLab HTTP/HTTPS access')
    parser.add_argument('--allowed-ips', help='Comma-separated list of IPs/CIDRs to allow GitLab access (default: allow all). Example: 192.168.1.0/24,10.0.0.100,172.16.0.0/16')
    parser.add_argument('--skip-firewall', action='store_true', help='Skip firewall configuration entirely')
    parser.add_argument('--firewall-only', action='store_true', help='Only configure firewall, skip all GitLab operations')
    parser.add_argument('--enable-https', action='store_true', help='Configure GitLab with HTTPS using self-signed certificate')
    parser.add_argument('--non-interactive', action='store_true', help='Run in non-interactive mode (auto-cleanup URL changes without prompting)')
    
    args = parser.parse_args()
    
    # Handle standalone firewall configuration
    if args.firewall_only:
        print("=" * 60)
        print("Standalone Firewall Configuration")
        print("=" * 60)
        installer = GitLabInstaller()
        allowed_endpoints = None
        if args.allowed_ips:
            allowed_endpoints = [ip.strip() for ip in args.allowed_ips.split(',') if ip.strip()]
        
        success = installer.configure_firewall(allowed_endpoints)
        if success:
            print("\n✓ Firewall configuration completed successfully")
        else:
            print("\n✗ Firewall configuration failed")
            sys.exit(1)
        return
    
    installer = GitLabInstaller()

    # Load default configuration from .gitlab-ci.yml variables section
    if not installer.load_default_config():
        print("Warning: Could not load default configuration")
        print("Continuing with manual configuration...")

    # Always prompt for user input (args provide defaults shown in prompts)
    config = installer.get_user_input(args)
    if config is None:
        print("Configuration incomplete. Exiting.")
        return

    # Confirmation prompt
    print("\n" + "=" * 60)
    print("Configuration Summary")
    print("=" * 60)
    print(f"GitLab URL:   {config['gitlab_url']}")
    print(f"Admin Username: {config['admin_username']}")
    print(f"Project Name: {config['project_name']}")
    print(f"Project Path: {config['project_path']}")
    print(f"Skip Install: {args.skip_install}")
    
    # Firewall configuration summary
    if args.skip_firewall:
        print("Firewall: Skipped (--skip-firewall)")
    elif args.configure_firewall or args.allowed_ips:
        if args.allowed_ips:
            print(f"Firewall: Restrictive access for IPs: {args.allowed_ips}")
        else:
            print("Firewall: Public access (--configure-firewall)")
    else:
        print("Firewall: Not configured (use --configure-firewall to enable)")
    
    action = "configure" if args.skip_install else "install and configure"
    confirm = input(f"\nProceed to {action} GitLab CI/CD? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Cancelled")
        return

    # ---- Ensure GitLab hostname is resolvable ----
    print("\n" + "=" * 60)
    print("Ensuring GitLab Hostname is Resolvable")
    print("=" * 60)
    if not _ensure_hostname_resolvable(config['gitlab_url']):
        print("✗ Cannot proceed - hostname is not resolvable")
        print("  Please ensure the GitLab URL is correct and either:")
        print("  1. Configure DNS to point to this server, or")
        print("  2. Add the hostname to /etc/hosts manually")
        return

    # ---- Save + encrypt the GitLab admin credentials in pipeline/ ----
    # Save immediately after user input so credentials are persisted even if
    # later steps (token generation, project creation, etc.) fail.
    save_gitlab_credentials(config)

    # ---- Install GitLab (unless --skip-install) ----
    if not args.skip_install:
        if not installer.install_gitlab(config, non_interactive=args.non_interactive):
            print("GitLab installation failed")
            return
        if not installer.wait_for_gitlab():
            print("GitLab did not become ready")
            return
        # Generate token if not provided
        if not config["admin_token"]:
            print("\nGenerating Personal Access Token...")
            token = installer.generate_admin_token(config)
            if not token:
                print("Failed to generate token")
                return
            config["admin_token"] = token
            installer.admin_token = token
            print(f"✓ Generated token: {token[:8]}...")
    else:
        # --skip-install: still verify GitLab is running and reset password
        print("\nSkipping installation (--skip-install). Verifying GitLab is running...")
        if not installer.wait_for_gitlab(max_retries=6, retry_interval=5):
            print("⚠ GitLab does not appear to be running.")
            print("  Run without --skip-install to install, or start GitLab manually.")
            return
        # Reset admin password even when skipping install
        if config.get("admin_password"):
            print("\nEnsuring admin password matches provided credentials...")
            installer._wait_for_gitlab_services()
            installer._reset_admin_password(config.get("admin_username"), config.get("admin_password"))

    # ---- Configure Firewall (if requested) ----
    if not args.skip_firewall:
        if args.configure_firewall or args.allowed_ips:
            allowed_endpoints = None
            if args.allowed_ips:
                # Parse comma-separated IPs/CIDRs
                allowed_endpoints = [ip.strip() for ip in args.allowed_ips.split(',') if ip.strip()]
            
            if not installer.configure_firewall(allowed_endpoints):
                print("⚠ Firewall configuration failed, but continuing...")
                print("  You can configure firewall manually later")
        else:
            print("\n⚠ Firewall not configured. GitLab may not be accessible externally.")
            print("  Use --configure-firewall to enable HTTP/HTTPS access")
            print("  Use --allowed-ips to restrict access to specific IPs/CIDRs")

    # ---- Configure HTTPS (if requested) ----
    if args.enable_https:
        if not installer.configure_https():
            print("⚠ HTTPS configuration failed, but continuing with HTTP...")
            print("  You can configure HTTPS manually later")
    else:
        print("\n⚠ HTTPS not configured. GitLab will use HTTP only.")
        print("  Use --enable-https to configure GitLab with self-signed certificate")

    # ---- Ensure we have a valid token ----
    if config.get("admin_token"):
        installer.admin_token = config["admin_token"]

    if not installer.admin_token:
        print("\nNo token available. Attempting to auto-generate...")
        token = installer.generate_admin_token(config)
        if token:
            config["admin_token"] = token
            installer.admin_token = token
            print(f"✓ Generated token: {token[:8]}...")
        else:
            print("✗ No admin token available. Cannot proceed with API calls.")
            print(f"Please create a token at: {installer.gitlab_url}/-/user_settings/personal_access_tokens")
            return

    # ---- Create / find project ----
    if not installer.create_project(config):
        print("Project creation failed")
        return

    # ---- Configure CI/CD variables ----
    installer.configure_ci_cd_variables()
    installer.configure_cluster_variables()

    # ---- Auto-create cluster password CI/CD variables (no user prompt) ----
    installer.configure_cluster_passwords()

    # ---- Optional: generate and upload datasets ----
    if args.generate_datasets:
        installer.generate_and_upload_datasets(args)

    # ---- Finish ----
    installer.upload_pipeline_files()

    # ---- Register GitLab Runner ----
    if not args.skip_install:
        print("\nRegistering GitLab Runner...")
        if not installer.register_gitlab_runner():
            print("⚠ GitLab runner registration failed.")
            print("  You can register manually using:")
            print("  1. Get registration token from: Settings > CI/CD > Runners")
            print("  2. Run: gitlab-runner register --url <gitlab-url> --registration-token <token>")

    installer.generate_setup_instructions(config)

    print("\n✓ GitLab CI/CD configuration completed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
