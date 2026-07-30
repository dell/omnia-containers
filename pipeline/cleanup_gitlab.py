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
GitLab Cleanup Script
Completely removes GitLab installation and all configurations for a clean reinstall.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


_VALID_HOSTNAME_RE = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9._-]{0,253}[a-zA-Z0-9])?$')

def run_command(cmd, description, critical=False):
    """Run a command and handle errors. Accepts a list of arguments."""
    print(f"\n{description}...")
    try:
        if isinstance(cmd, str):
            cmd = cmd.split()
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {description} completed")
            return True
        else:
            if critical:
                print(f"✗ {description} failed: {result.stderr}")
                return False
            else:
                print(f"⚠ {description} had issues (continuing): {result.stderr}")
                return True
    except Exception as e:
        if critical:
            print(f"✗ {description} error: {e}")
            return False
        else:
            print(f"⚠ {description} error (continuing): {e}")
            return True

def stop_gitlab_services():
    """Stop all GitLab services"""
    print("\n" + "="*60)
    print("Stopping GitLab Services")
    print("="*60)
    
    run_command(["gitlab-ctl", "stop"], "Stopping GitLab services")
    run_command(["systemctl", "stop", "gitlab-runsvdir"], "Stopping gitlab-runsvdir service")
    run_command(["systemctl", "disable", "gitlab-runsvdir"], "Disabling gitlab-runsvdir service")


def gitlab_ctl_cleanup():
    """Run gitlab-ctl commands to purge data/services when available"""
    print("\n" + "=" * 60)
    print("Running gitlab-ctl Cleanup")
    print("=" * 60)

    run_command(["gitlab-ctl", "cleanse"], "gitlab-ctl cleanse", critical=False)
    run_command(["gitlab-ctl", "uninstall"], "gitlab-ctl uninstall", critical=False)

def remove_gitlab_packages():
    """Remove GitLab packages"""
    print("\n" + "="*60)
    print("Removing GitLab Packages")
    print("="*60)
    
    # Check OS type
    if os.path.exists('/etc/redhat-release'):
        # RHEL/CentOS
        run_command(["yum", "remove", "-y", "gitlab-ce"], "Removing gitlab-ce package", critical=False)
        run_command(["rpm", "-e", "gitlab-ce"], "Force removing gitlab-ce package", critical=False)
    elif os.path.exists('/etc/debian_version'):
        # Debian/Ubuntu
        run_command(["apt-get", "remove", "-y", "gitlab-ce"], "Removing gitlab-ce package", critical=False)
        run_command(["dpkg", "-r", "gitlab-ce"], "Force removing gitlab-ce package", critical=False)

def remove_gitlab_directories():
    """Remove GitLab directories and data"""
    print("\n" + "="*60)
    print("Removing GitLab Directories")
    print("="*60)
    
    directories = [
        "/etc/gitlab",
        "/var/opt/gitlab",
        "/opt/gitlab",
        "/var/log/gitlab",
        "/run/gitlab",
        "/home/git",
        "/var/lib/gitlab-runner",
        "/etc/gitlab-runner",
    ]
    
    for directory in directories:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                print(f"✓ Removing {directory} completed")
            except Exception as e:
                print(f"⚠ Removing {directory} had issues (continuing): {e}")
        else:
            print(f"⚠ {directory} does not exist (skipping)")

def remove_ssl_certificates():
    """Remove GitLab SSL certificates"""
    print("\n" + "="*60)
    print("Removing SSL Certificates")
    print("="*60)
    
    ssl_dirs = ["/etc/gitlab/ssl", "/var/opt/gitlab/nginx/conf/ssl"]
    for ssl_dir in ssl_dirs:
        if os.path.isdir(ssl_dir):
            for item in os.listdir(ssl_dir):
                item_path = os.path.join(ssl_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    print(f"⚠ Could not remove {item_path}: {e}")
            print(f"✓ Removed SSL certificates from {ssl_dir}")
        else:
            print(f"⚠ {ssl_dir} does not exist (skipping)")

def remove_firewall_rules():
    """Remove GitLab firewall rules"""
    print("\n" + "="*60)
    print("Removing Firewall Rules")
    print("="*60)
    
    # Check if firewalld is running
    result = subprocess.run(["systemctl", "is-active", "firewalld"], capture_output=True, text=True)
    if result.returncode == 0:
        print("Firewalld is running, removing GitLab rules...")

        rules_result = subprocess.run(
            ["firewall-cmd", "--permanent", "--list-rich-rules"],
            capture_output=True,
            text=True
        )
        rules = [r.strip() for r in rules_result.stdout.splitlines() if r.strip()]
        for rule in rules:
            if any(token in rule for token in ["http", "https", 'port="80"', 'port="443"', 'port="2222"', "gitlab"]):
                run_command(
                    ["firewall-cmd", "--permanent", f"--remove-rich-rule={rule}"],
                    f"Removing rich rule: {rule}",
                    critical=False
                )

        for service in ("http", "https"):
            run_command(
                ["firewall-cmd", "--permanent", f"--remove-service={service}"],
                f"Removing service {service}",
                critical=False
            )

        for port in ("80/tcp", "443/tcp", "2222/tcp"):
            run_command(
                ["firewall-cmd", "--permanent", f"--remove-port={port}"],
                f"Removing port {port}",
                critical=False
            )

        # Reload firewall
        run_command(["firewall-cmd", "--reload"], "Reloading firewall")
        
        print("✓ Firewall rules removed")
    else:
        print("⚠ Firewalld is not running (skipping firewall cleanup)")

def discover_gitlab_hostnames():
    """Discover GitLab hostnames from gitlab.rb and /etc/hosts"""
    hostnames = set()

    gitlab_rb = Path("/etc/gitlab/gitlab.rb")
    if gitlab_rb.exists():
        try:
            content = gitlab_rb.read_text()
            for match in re.findall(r"external_url\s+[\"']([^\"']+)[\"']", content):
                parsed = urlparse(match)
                if parsed.hostname:
                    hostnames.add(parsed.hostname)

            host_match = re.search(r"gitlab_rails\['gitlab_host'\]\s*=\s*[\"']([^\"']+)[\"']", content)
            if host_match:
                hostnames.add(host_match.group(1))
        except Exception as exc:
            print(f"⚠ Could not parse /etc/gitlab/gitlab.rb: {exc}")

    hosts_file = Path("/etc/hosts")
    if hosts_file.exists():
        try:
            for line in hosts_file.read_text().splitlines():
                if line.strip().startswith('#'):
                    continue
                if "gitlab" in line.lower():
                    parts = line.split()
                    for part in parts[1:]:
                        if part and part != "localhost":
                            hostnames.add(part)
        except Exception as exc:
            print(f"⚠ Could not scan /etc/hosts: {exc}")

    return sorted(hostnames)


def remove_hosts_entries(hostnames=None):
    """Remove GitLab hostnames from /etc/hosts"""
    print("\n" + "="*60)
    print("Removing /etc/hosts Entries")
    print("="*60)

    detected = hostnames or discover_gitlab_hostnames()

    if not detected:
        hostname = input("Enter GitLab hostname to remove from /etc/hosts (e.g., gitlab.demo.com): ").strip()
        if hostname and _VALID_HOSTNAME_RE.match(hostname):
            detected = [hostname]
        elif hostname:
            print(f"\u26a0 Invalid hostname format: {hostname}")
            return

    if not detected:
        print("⚠ No hostnames provided or detected (skipping)")
        return

    try:
        with open("/etc/hosts", 'r') as f:
            lines = f.readlines()

        new_lines = []
        removed_hosts = set()
        for line in lines:
            if line.strip().startswith('#'):
                new_lines.append(line)
                continue

            should_remove = False
            for hostname in detected:
                if hostname and hostname in line:
                    should_remove = True
                    removed_hosts.add(hostname)
            if not should_remove:
                new_lines.append(line)

        with open("/etc/hosts", 'w') as f:
            f.writelines(new_lines)

        if removed_hosts:
            print(f"✓ Removed host entries: {', '.join(sorted(removed_hosts))}")
        else:
            print("⚠ No matching hostnames found in /etc/hosts")
    except Exception as e:
        print(f"✗ Error updating /etc/hosts: {e}")

def remove_vault_credentials():
    """Remove encrypted GitLab credentials"""
    print("\n" + "="*60)
    print("Removing Encrypted Credentials")
    print("="*60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    vault_file = os.path.join(script_dir, "gitlab_admin_credentials.yml")
    key_file = os.path.join(script_dir, ".omnia_test_credentials.key")
    
    if os.path.exists(vault_file):
        os.remove(vault_file)
        print(f"✓ Removed {vault_file}")
    
    if os.path.exists(key_file):
        os.remove(key_file)
        print(f"✓ Removed {key_file}")

def remove_gitlab_repositories():
    """Remove GitLab package repositories"""
    print("\n" + "="*60)
    print("Removing GitLab Package Repositories")
    print("="*60)
    
    if os.path.exists('/etc/redhat-release'):
        # RHEL/CentOS
        run_command(["rm", "-f", "/etc/yum.repos.d/gitlab_gitlab-ce.repo"], "Removing yum repository")
    elif os.path.exists('/etc/debian_version'):
        # Debian/Ubuntu
        run_command(["rm", "-f", "/etc/apt/sources.list.d/gitlab_gitlab-ce.list"], "Removing apt repository")

def cleanup_all():
    """Perform complete GitLab cleanup"""
    print("="*60)
    print("GitLab Complete Cleanup Script")
    print("="*60)
    print("\n⚠ WARNING: This will completely remove GitLab and all data!")
    print("⚠ This action is irreversible!")
    
    confirm = re.sub(r'[^a-z]', '', input("\nAre you sure you want to proceed? (type 'yes' to confirm): ").strip().lower()[:3])
    if confirm != 'yes':
        print("Cleanup cancelled.")
        return
    
    print("\n" + "="*60)
    print("Starting Cleanup Process")
    print("="*60)
    
    # Stop services
    stop_gitlab_services()
    gitlab_ctl_cleanup()
    
    # Remove packages
    remove_gitlab_packages()
    
    # Remove directories
    remove_gitlab_directories()
    
    # Remove SSL certificates
    remove_ssl_certificates()
    
    # Remove firewall rules
    remove_firewall_rules()
    
    # Remove /etc/hosts entries
    remove_hosts_entries()
    
    # Remove encrypted credentials
    remove_vault_credentials()
    
    # Remove repositories
    remove_gitlab_repositories()
    
    print("\n" + "="*60)
    print("Cleanup Complete!")
    print("="*60)
    print("\nYou can now run install_gitlab_cicd.py for a fresh installation.")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "--help" or command == "-h":
            print("GitLab Cleanup Script")
            print("\nUsage:")
            print("  python3 cleanup_gitlab.py           - Full cleanup (interactive)")
            print("  python3 cleanup_gitlab.py --help    - Show this help message")
            print("\nWhat it removes:")
            print("  - GitLab packages")
            print("  - GitLab configuration files")
            print("  - GitLab data and databases")
            print("  - SSL certificates")
            print("  - Firewall rules")
            print("  - /etc/hosts entries")
            print("  - Encrypted credentials")
            print("  - GitLab package repositories")
            return
        else:
            print(f"Unknown option: {command}")
            print("Use --help for usage information")
            return
    
    cleanup_all()

if __name__ == "__main__":
    main()
