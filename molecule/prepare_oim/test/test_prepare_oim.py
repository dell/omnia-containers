"""
Consolidated test for prepare_oim validation.

This single test function validates:
1. OpenCHAMI containers and service status
2. Auth container and service (only if LDAP/openldap is present in software_config.json)
3. omnia.target is running successfully with all dependencies
4. slapd.conf configuration and user listing via ldapsearch (if LDAP enabled)
"""

import os
import sys
import json
import pytest

# Add automation_library to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from automation_library.vars.prepare_oim_vars import PREPARE_OIM_VARS
from automation_library.messages.prepare_oim_msgs import PREPARE_OIM_MSGS


class TestPrepareOIM:
    """Single consolidated test class for prepare_oim validation."""

    def test_prepare_oim_validation(self, host):
        """
        Consolidated test function that validates all prepare_oim requirements:

        1. OpenCHAMI containers and service status
        2. Auth container and service (if LDAP/openldap enabled in software_config.json)
        3. omnia.target and all dependencies running properly
        4. slapd.conf configuration and ldapsearch validation (if LDAP enabled)
        """
        results = {
            "passed": [],
            "failed": [],
            "skipped": [],
            "warnings": []
        }

        # =====================================================================
        # Step 1: Detect container runtime
        # =====================================================================
        container_runtime = self._detect_container_runtime(host)
        if not container_runtime:
            results["failed"].append("No container runtime (podman/docker) found")
            self._report_results(results)
            pytest.fail("No container runtime available")
        results["passed"].append(f"Container runtime detected: {container_runtime}")

        # =====================================================================
        # Step 2: Validate OpenCHAMI containers
        # =====================================================================
        openchami_results = self._validate_openchami_containers(host, container_runtime)
        results["passed"].extend(openchami_results["passed"])
        results["failed"].extend(openchami_results["failed"])
        results["warnings"].extend(openchami_results["warnings"])

        # =====================================================================
        # Step 3: Validate omnia.target and ALL dependencies
        # =====================================================================
        omnia_results = self._validate_omnia_target(host)
        results["passed"].extend(omnia_results["passed"])
        results["failed"].extend(omnia_results["failed"])
        results["warnings"].extend(omnia_results["warnings"])

        # =====================================================================
        # Step 4: Check LDAP configuration (openldap in software_config.json)
        # =====================================================================
        ldap_enabled = self._check_ldap_enabled(host, container_runtime)

        if ldap_enabled:
            results["passed"].append("OpenLDAP is enabled in software_config.json")

            # Validate auth container (omnia_auth)
            auth_results = self._validate_auth_containers(host, container_runtime)
            results["passed"].extend(auth_results["passed"])
            results["failed"].extend(auth_results["failed"])
            results["warnings"].extend(auth_results["warnings"])

            # Validate auth service (omnia_auth.service)
            auth_svc_results = self._validate_auth_service(host)
            results["passed"].extend(auth_svc_results["passed"])
            results["failed"].extend(auth_svc_results["failed"])
            results["warnings"].extend(auth_svc_results["warnings"])

            # Validate slapd.conf and ldapsearch
            ldap_results = self._validate_ldap_configuration(host, container_runtime)
            results["passed"].extend(ldap_results["passed"])
            results["failed"].extend(ldap_results["failed"])
            results["warnings"].extend(ldap_results["warnings"])
        else:
            results["skipped"].append("OpenLDAP not enabled - skipping auth container/service validation")
            results["skipped"].append("OpenLDAP not enabled - skipping LDAP configuration validation")

        # =====================================================================
        # Report results
        # =====================================================================
        self._report_results(results)

        # Fail if any critical failures
        if results["failed"]:
            pytest.fail(
                f"prepare_oim validation failed with {len(results['failed'])} error(s):\n" +
                "\n".join(f"  - {f}" for f in results["failed"])
            )

    def _detect_container_runtime(self, host):
        """Detect available container runtime."""
        for runtime in ["podman", "docker"]:
            cmd = host.run(f"which {runtime}")
            if cmd.rc == 0:
                return runtime
        return None

    def _validate_openchami_containers(self, host, runtime):
        """Validate OpenCHAMI containers exist and are running."""
        results = {"passed": [], "failed": [], "warnings": []}
        
        expected_containers = PREPARE_OIM_VARS.get("openchami_containers", [])
        
        # Get running containers
        cmd = host.run(f"{runtime} ps --format '{{{{.Names}}}}:{{{{.Status}}}}'")
        if cmd.rc != 0:
            results["failed"].append(f"Failed to list containers: {cmd.stderr}")
            return results
        
        running_containers = {}
        for line in cmd.stdout.strip().split('\n'):
            if ':' in line:
                name, status = line.split(':', 1)
                running_containers[name.strip()] = status.strip()
        
        # Check each expected container
        for container in expected_containers:
            found = False
            is_running = False
            
            for name, status in running_containers.items():
                if container in name or name == container:
                    found = True
                    if "Up" in status:
                        is_running = True
                        results["passed"].append(f"Container '{container}' is running")
                    else:
                        results["failed"].append(f"Container '{container}' exists but not running (status: {status})")
                    break
            
            if not found:
                results["failed"].append(f"Container '{container}' not found")
        
        # Check container health for running containers
        for container in expected_containers:
            health_cmd = host.run(
                f"{runtime} inspect --format '{{{{.State.Health.Status}}}}' {container} 2>/dev/null"
            )
            if health_cmd.rc == 0:
                health = health_cmd.stdout.strip().strip("'")
                if health and health not in ["", "<no value>", "none"]:
                    if health == "healthy":
                        results["passed"].append(f"Container '{container}' health: healthy")
                    else:
                        results["warnings"].append(f"Container '{container}' health: {health}")
        
        return results

    def _validate_omnia_target(self, host):
        """Validate omnia.target, omnia_core.service, and ALL dependencies are running properly."""
        results = {"passed": [], "failed": [], "warnings": []}

        # =====================================================================
        # Validate omnia_core.service
        # =====================================================================
        core_service = PREPARE_OIM_VARS.get("omnia_core_service", "omnia_core.service")
        core_active = host.run(f"systemctl is-active {core_service} 2>/dev/null")
        if core_active.stdout.strip() == "active":
            results["passed"].append(f"{core_service} is active (running)")
        else:
            results["failed"].append(f"{core_service} is not active (state: {core_active.stdout.strip()})")

        core_enabled = host.run(f"systemctl is-enabled {core_service} 2>/dev/null")
        if core_enabled.stdout.strip() in ["enabled", "static", "generated"]:
            results["passed"].append(f"{core_service} is enabled ({core_enabled.stdout.strip()})")
        else:
            results["warnings"].append(f"{core_service} is not enabled (state: {core_enabled.stdout.strip()})")

        # =====================================================================
        # Validate omnia.target
        # =====================================================================
        # Check if omnia.target exists
        cmd = host.run("systemctl list-unit-files omnia.target 2>/dev/null")
        if "omnia.target" not in cmd.stdout:
            results["failed"].append("omnia.target not found")
            return results

        results["passed"].append("omnia.target exists")

        # Check if enabled
        enabled_cmd = host.run("systemctl is-enabled omnia.target 2>/dev/null")
        if enabled_cmd.stdout.strip() in ["enabled", "static"]:
            results["passed"].append(f"omnia.target is enabled ({enabled_cmd.stdout.strip()})")
        else:
            results["failed"].append(f"omnia.target is not enabled (state: {enabled_cmd.stdout.strip()})")

        # Check if active
        active_cmd = host.run("systemctl is-active omnia.target 2>/dev/null")
        if active_cmd.stdout.strip() == "active":
            results["passed"].append("omnia.target is active")
        else:
            results["failed"].append(f"omnia.target is not active (state: {active_cmd.stdout.strip()})")

        # Get ALL dependencies and check each one
        deps_cmd = host.run("systemctl list-dependencies omnia.target --plain 2>/dev/null")
        if deps_cmd.rc == 0:
            dependencies = [d.strip() for d in deps_cmd.stdout.strip().split('\n') if d.strip() and d.strip() != "omnia.target"]
            results["passed"].append(f"omnia.target has {len(dependencies)} dependencies")

            # Check ALL dependencies
            failed_deps = []
            active_deps = []
            for dep in dependencies:
                dep_status = host.run(f"systemctl is-active '{dep}' 2>/dev/null")
                status = dep_status.stdout.strip()
                if status == "active":
                    active_deps.append(dep)
                elif status in ["inactive", "failed", "dead"]:
                    failed_deps.append(f"{dep} ({status})")

            if active_deps:
                results["passed"].append(f"{len(active_deps)} dependencies are active")

            if failed_deps:
                results["failed"].append(f"Dependencies not running: {', '.join(failed_deps[:5])}" +
                                        (f" and {len(failed_deps)-5} more" if len(failed_deps) > 5 else ""))

        # Check for failed units
        failed_cmd = host.run(
            "systemctl list-units --state=failed | grep -iE 'omnia|openchami|pulp|auth|minio|registry' || true"
        )
        if failed_cmd.stdout.strip():
            results["failed"].append(f"Failed units found: {failed_cmd.stdout.strip()}")
        else:
            results["passed"].append("No failed omnia/openchami related units")

        # Validate openchami.target specifically
        openchami_cmd = host.run("systemctl is-active openchami.target 2>/dev/null")
        if openchami_cmd.stdout.strip() == "active":
            results["passed"].append("openchami.target is active")
        else:
            results["warnings"].append(f"openchami.target status: {openchami_cmd.stdout.strip()}")

        return results

    def _check_ldap_enabled(self, host, container_runtime):
        """Check if OpenLDAP is enabled in software_config.json (softwares list)."""
        # First check molecule env vars set by converge
        env_file = host.file("/tmp/molecule_env_vars")
        if env_file.exists:
            content = env_file.content_string
            if "LDAP_ENABLED=true" in content.lower():
                return True
            if "LDAP_ENABLED=false" in content.lower():
                return False

        # Read software_config.json from omnia_core container
        config_path = PREPARE_OIM_VARS.get("software_config_path")
        omnia_core = PREPARE_OIM_VARS.get("omnia_core_container", "omnia_core")

        cmd = host.run(f"{container_runtime} exec {omnia_core} cat {config_path} 2>/dev/null")
        if cmd.rc != 0:
            return False

        try:
            config = json.loads(cmd.stdout)
            softwares = config.get("softwares", [])
            ldap_name = PREPARE_OIM_VARS.get("ldap_software_name", "openldap")
            # Check if openldap is in the softwares list
            for sw in softwares:
                if isinstance(sw, dict) and sw.get("name") == ldap_name:
                    return True
            return False
        except (json.JSONDecodeError, Exception):
            return False

    def _validate_auth_containers(self, host, runtime):
        """Validate auth containers (when LDAP is enabled)."""
        results = {"passed": [], "failed": [], "warnings": []}
        
        auth_containers = PREPARE_OIM_VARS.get("auth_containers", [])
        
        # Get running containers
        cmd = host.run(f"{runtime} ps --format '{{{{.Names}}}}:{{{{.Status}}}}'")
        if cmd.rc != 0:
            results["failed"].append(f"Failed to list containers: {cmd.stderr}")
            return results
        
        running_containers = {}
        for line in cmd.stdout.strip().split('\n'):
            if ':' in line:
                name, status = line.split(':', 1)
                running_containers[name.strip()] = status.strip()
        
        for container in auth_containers:
            found = False
            for name, status in running_containers.items():
                if container in name or name == container:
                    found = True
                    if "Up" in status:
                        results["passed"].append(f"Auth container '{container}' is running")
                    else:
                        results["failed"].append(f"Auth container '{container}' not running (status: {status})")
                    break
            
            if not found:
                results["failed"].append(f"Auth container '{container}' not found (LDAP is enabled)")
        
        return results

    def _validate_auth_service(self, host):
        """Validate auth systemd service (when LDAP is enabled)."""
        results = {"passed": [], "failed": [], "warnings": []}
        
        auth_service_names = PREPARE_OIM_VARS.get("auth_service_names", [
            "openchami-auth.service",
            "openchami-opaal.service", 
            "auth.service",
            "opaal.service"
        ])
        
        service_found = False
        service_running = False
        
        for service in auth_service_names:
            active_cmd = host.run(f"systemctl is-active {service} 2>/dev/null")
            if active_cmd.stdout.strip() == "active":
                service_found = True
                service_running = True
                results["passed"].append(f"Auth service '{service}' is running")
                break
            elif active_cmd.rc == 0:
                service_found = True
        
        if not service_found:
            results["warnings"].append("No auth service found (checked: " + ", ".join(auth_service_names) + ")")
        elif not service_running:
            results["warnings"].append("Auth service exists but not running")
        
        return results

    def _validate_ldap_configuration(self, host, runtime):
        """
        Validate LDAP configuration:
        - Check slapd.conf configuration in omnia_auth container
        - Validate users can be listed via ldapsearch inside omnia_auth container
        """
        results = {"passed": [], "failed": [], "warnings": []}

        auth_container = PREPARE_OIM_VARS.get("omnia_auth_container", "omnia_auth")
        slapd_conf_path = PREPARE_OIM_VARS.get("slapd_conf_path", "/etc/openldap/slapd.conf")
        ldap_base_dn = PREPARE_OIM_VARS.get("ldap_base_dn", "dc=omnia,dc=test")

        # =====================================================================
        # Step 1: Validate slapd.conf exists and is configured
        # =====================================================================
        slapd_check = host.run(
            f"{runtime} exec {auth_container} test -f {slapd_conf_path} && echo EXISTS"
        )
        if "EXISTS" not in slapd_check.stdout:
            results["failed"].append(f"slapd.conf not found at {slapd_conf_path} in {auth_container}")
            return results

        results["passed"].append(f"slapd.conf found at {slapd_conf_path}")

        # Read slapd.conf content
        slapd_content_cmd = host.run(
            f"{runtime} exec {auth_container} cat {slapd_conf_path} 2>/dev/null"
        )
        if slapd_content_cmd.rc == 0:
            slapd_content = slapd_content_cmd.stdout

            # Check for required configurations
            if "suffix" in slapd_content:
                results["passed"].append("slapd.conf has suffix configured")
            else:
                results["warnings"].append("slapd.conf missing suffix configuration")

            if "rootdn" in slapd_content:
                results["passed"].append("slapd.conf has rootdn configured")
            else:
                results["warnings"].append("slapd.conf missing rootdn configuration")

            if "database" in slapd_content:
                results["passed"].append("slapd.conf has database configured")

            # Check for TLS configuration
            if "TLSCertificateFile" in slapd_content:
                results["passed"].append("slapd.conf has TLS configured")

            # Check for external LDAP proxy configuration (ldap-back or meta backend)
            if "ldap://" in slapd_content or "uri" in slapd_content.lower():
                results["passed"].append("External LDAP proxy configuration found in slapd.conf")

        # =====================================================================
        # Step 2: Check if ldapsearch is available
        # =====================================================================
        ldapsearch_check = host.run(
            f"{runtime} exec {auth_container} which ldapsearch 2>/dev/null"
        )

        if ldapsearch_check.rc != 0:
            results["warnings"].append(f"ldapsearch not found in {auth_container} container")
            # Check if LDAP port is listening
            port_check = host.run("ss -tlnp | grep ':389' || true")
            if port_check.stdout.strip():
                results["passed"].append("LDAP port 389 is listening on host")
            else:
                results["warnings"].append("LDAP port 389 not detected on host")
            return results

        results["passed"].append("ldapsearch is available in auth container")

        # =====================================================================
        # Step 3: Execute ldapsearch to list users
        # =====================================================================
        # Try ldapsearch with the configured base DN
        ldapsearch_cmd = host.run(
            f"{runtime} exec {auth_container} ldapsearch -x -H ldap://localhost -b '{ldap_base_dn}' '(objectClass=*)' dn 2>/dev/null"
        )

        if ldapsearch_cmd.rc == 0 and "dn:" in ldapsearch_cmd.stdout:
            entry_count = ldapsearch_cmd.stdout.count("dn:")
            results["passed"].append(f"ldapsearch successful - found {entry_count} entries with base DN '{ldap_base_dn}'")

            # Try to list users specifically (posixAccount or inetOrgPerson)
            user_search = host.run(
                f"{runtime} exec {auth_container} ldapsearch -x -H ldap://localhost -b '{ldap_base_dn}' "
                f"'(|(objectClass=posixAccount)(objectClass=inetOrgPerson))' uid cn 2>/dev/null | grep -E '^(uid|cn):' | head -10"
            )
            if user_search.rc == 0 and user_search.stdout.strip():
                user_lines = [l for l in user_search.stdout.strip().split('\n') if l.startswith('uid:') or l.startswith('cn:')]
                results["passed"].append(f"Users found via ldapsearch: {len(user_lines)} attributes returned")
                # Show first few users
                for line in user_lines[:3]:
                    results["passed"].append(f"  - {line}")
            else:
                results["warnings"].append("No user entries found (may need to add users to LDAP)")
        else:
            # Try anonymous base search
            anon_cmd = host.run(
                f"{runtime} exec {auth_container} ldapsearch -x -H ldap://localhost -s base '(objectClass=*)' 2>/dev/null"
            )
            if anon_cmd.rc == 0:
                results["passed"].append("LDAP server responding (base search successful)")
            else:
                results["failed"].append(f"ldapsearch failed - LDAP may not be running or misconfigured")

        # =====================================================================
        # Step 4: Verify LDAP service is running inside container
        # =====================================================================
        slapd_running = host.run(
            f"{runtime} exec {auth_container} pgrep -x slapd 2>/dev/null"
        )
        if slapd_running.rc == 0:
            results["passed"].append("slapd process is running inside auth container")
        else:
            results["warnings"].append("slapd process not detected inside auth container")

        return results

    def _report_results(self, results):
        """Print a summary of test results."""
        print("\n" + "=" * 70)
        print("PREPARE_OIM VALIDATION RESULTS")
        print("=" * 70)
        
        print(f"\n✅ PASSED ({len(results['passed'])}):")
        for item in results["passed"]:
            print(f"   • {item}")
        
        if results["warnings"]:
            print(f"\n⚠️  WARNINGS ({len(results['warnings'])}):")
            for item in results["warnings"]:
                print(f"   • {item}")
        
        if results["skipped"]:
            print(f"\n⏭️  SKIPPED ({len(results['skipped'])}):")
            for item in results["skipped"]:
                print(f"   • {item}")
        
        if results["failed"]:
            print(f"\n❌ FAILED ({len(results['failed'])}):")
            for item in results["failed"]:
                print(f"   • {item}")
        
        print("\n" + "=" * 70)
        total = len(results["passed"]) + len(results["failed"]) + len(results["skipped"])
        print(f"SUMMARY: {len(results['passed'])} passed, {len(results['failed'])} failed, "
              f"{len(results['skipped'])} skipped, {len(results['warnings'])} warnings")
        print("=" * 70 + "\n")
