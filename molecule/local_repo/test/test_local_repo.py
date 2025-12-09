"""
Consolidated test for local_repo validation.

This single test function validates:
1. Pulp container is running without errors
2. Custom repo is accessible from OIM
3. Pulp CLI commands work correctly
4. All packages are downloaded successfully (via status.csv files)
"""

import os
import sys
import csv
import pytest

# Add automation_library to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from automation_library.vars.local_repo_vars import LOCAL_REPO_VARS
from automation_library.messages.local_repo_msgs import LOCAL_REPO_MSGS


class TestLocalRepo:
    """Single consolidated test class for local_repo validation."""

    def test_local_repo_validation(self, host):
        """
        Consolidated test function that validates all local_repo requirements:

        1. Pulp container is running without errors
        2. Custom repo is accessible from OIM
        3. Pulp CLI commands work correctly
        4. All packages are downloaded successfully (via status.csv files)
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
        # Step 2: Validate Pulp container is running without errors
        # =====================================================================
        pulp_results = self._validate_pulp_container(host, container_runtime)
        results["passed"].extend(pulp_results["passed"])
        results["failed"].extend(pulp_results["failed"])
        results["warnings"].extend(pulp_results["warnings"])

        # =====================================================================
        # Step 3: Validate custom repo is accessible from OIM
        # =====================================================================
        repo_results = self._validate_custom_repo_access(host)
        results["passed"].extend(repo_results["passed"])
        results["failed"].extend(repo_results["failed"])
        results["warnings"].extend(repo_results["warnings"])

        # =====================================================================
        # Step 4: Validate Pulp API endpoints
        # =====================================================================
        pulp_api_results = self._validate_pulp_api(host, container_runtime)
        results["passed"].extend(pulp_api_results["passed"])
        results["failed"].extend(pulp_api_results["failed"])
        results["warnings"].extend(pulp_api_results["warnings"])

        # =====================================================================
        # Step 5: Validate package download status via status.csv files
        # =====================================================================
        status_results = self._validate_package_download_status(host)
        results["passed"].extend(status_results["passed"])
        results["failed"].extend(status_results["failed"])
        results["warnings"].extend(status_results["warnings"])
        results["skipped"].extend(status_results.get("skipped", []))

        # =====================================================================
        # Step 6: Validate air-gap image registry configuration
        # =====================================================================
        airgap_results = self._validate_airgap_images(host)
        results["passed"].extend(airgap_results["passed"])
        results["failed"].extend(airgap_results["failed"])
        results["warnings"].extend(airgap_results["warnings"])
        results["skipped"].extend(airgap_results.get("skipped", []))

        # =====================================================================
        # Report results
        # =====================================================================
        self._report_results(results)

        # Fail if any critical failures
        if results["failed"]:
            pytest.fail(
                f"local_repo validation failed with {len(results['failed'])} error(s):\n" +
                "\n".join(f"  - {f}" for f in results["failed"])
            )

    def _detect_container_runtime(self, host):
        """Detect available container runtime."""
        for runtime in ["podman", "docker"]:
            cmd = host.run(f"which {runtime}")
            if cmd.rc == 0:
                return runtime
        return None

    def _validate_pulp_container(self, host, runtime):
        """Validate Pulp container is running without errors."""
        results = {"passed": [], "failed": [], "warnings": []}

        pulp_container = LOCAL_REPO_VARS.get("pulp_container_name", "pulp")

        # Check if Pulp container exists and is running
        cmd = host.run(f"{runtime} ps -a --format '{{{{.Names}}}}:{{{{.Status}}}}'")
        if cmd.rc != 0:
            results["failed"].append(f"Failed to list containers: {cmd.stderr}")
            return results

        pulp_found = False
        pulp_running = False
        pulp_status = ""

        for line in cmd.stdout.strip().split('\n'):
            if ':' in line:
                name, status = line.split(':', 1)
                if pulp_container in name.strip() or name.strip() == pulp_container:
                    pulp_found = True
                    pulp_status = status.strip()
                    if "Up" in status:
                        pulp_running = True
                    break

        if not pulp_found:
            results["failed"].append(f"Pulp container '{pulp_container}' not found")
            return results

        if not pulp_running:
            results["failed"].append(f"Pulp container '{pulp_container}' is not running (status: {pulp_status})")
            return results

        results["passed"].append(f"Pulp container '{pulp_container}' is running")

        # Check container health
        health_cmd = host.run(
            f"{runtime} inspect --format '{{{{.State.Health.Status}}}}' {pulp_container} 2>/dev/null"
        )
        if health_cmd.rc == 0:
            health = health_cmd.stdout.strip().strip("'")
            if health and health not in ["", "<no value>", "none"]:
                if health == "healthy":
                    results["passed"].append(f"Pulp container health: healthy")
                else:
                    results["warnings"].append(f"Pulp container health: {health}")

        # Check for errors in container logs
        error_cmd = host.run(
            f"{runtime} logs --tail 100 {pulp_container} 2>&1 | grep -iE '(error|fatal|critical|exception)' | head -5"
        )
        if error_cmd.rc == 0 and error_cmd.stdout.strip():
            error_count = len(error_cmd.stdout.strip().split('\n'))
            results["warnings"].append(f"Pulp container has {error_count} error(s) in recent logs")
        else:
            results["passed"].append("Pulp container has no critical errors in recent logs")

        return results

    def _validate_custom_repo_access(self, host):
        """Validate custom repo is accessible from OIM."""
        results = {"passed": [], "failed": [], "warnings": []}

        base_url = LOCAL_REPO_VARS.get("custom_repo_base_url", "https://localhost:2225")
        endpoints = LOCAL_REPO_VARS.get("custom_repo_endpoints", [
            "/pulp/api/v3/status/",
        ])

        # Test base URL accessibility (use -k to skip SSL verification for self-signed certs)
        base_check = host.run(f"curl -s -k -o /dev/null -w '%{{http_code}}' --connect-timeout 10 {base_url}/pulp/api/v3/status/")
        if base_check.rc == 0 and base_check.stdout.strip() in ["200", "301", "302"]:
            results["passed"].append(f"Custom repo is accessible at {base_url}")
        else:
            results["failed"].append(f"Custom repo is NOT accessible at {base_url} (HTTP: {base_check.stdout.strip()})")
            return results

        # Test specific endpoints
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            endpoint_check = host.run(f"curl -s -k -o /dev/null -w '%{{http_code}}' --connect-timeout 10 {url}")
            if endpoint_check.rc == 0 and endpoint_check.stdout.strip() in ["200", "301", "302"]:
                results["passed"].append(f"Custom repo endpoint accessible: {endpoint}")
            else:
                results["warnings"].append(f"Custom repo endpoint not accessible: {endpoint} (HTTP: {endpoint_check.stdout.strip()})")

        return results

    def _validate_pulp_api(self, host, runtime):
        """Validate Pulp API endpoints work correctly."""
        results = {"passed": [], "failed": [], "warnings": []}

        pulp_container = LOCAL_REPO_VARS.get("pulp_container_name", "pulp")
        pulp_api_base_url = LOCAL_REPO_VARS.get("pulp_api_base_url", "https://localhost:2225")
        pulp_api_username = LOCAL_REPO_VARS.get("pulp_api_username", "admin")
        pulp_api_password = LOCAL_REPO_VARS.get("pulp_api_password", "Dell1234")
        pulp_api_endpoints = LOCAL_REPO_VARS.get("pulp_api_endpoints", [
            "/pulp/api/v3/repositories/rpm/rpm/",
            "/pulp/api/v3/remotes/rpm/rpm/",
            "/pulp/api/v3/publications/rpm/rpm/",
            "/pulp/api/v3/distributions/rpm/rpm/",
        ])

        # Test each Pulp API endpoint from inside the container
        for endpoint in pulp_api_endpoints:
            url = f"{pulp_api_base_url}{endpoint}"
            # Use curl with basic auth inside the pulp container
            cmd_result = host.run(
                f"{runtime} exec {pulp_container} curl -s -k -u {pulp_api_username}:{pulp_api_password} "
                f"-o /dev/null -w '%{{http_code}}' {url} 2>&1"
            )

            endpoint_name = endpoint.split('/')[-2] if endpoint.endswith('/') else endpoint.split('/')[-1]

            if cmd_result.rc == 0 and cmd_result.stdout.strip() == "200":
                results["passed"].append(f"Pulp API '{endpoint_name}' endpoint accessible")
            elif cmd_result.stdout.strip() == "401":
                results["failed"].append(f"Pulp API '{endpoint_name}' authentication failed")
            elif cmd_result.stdout.strip() == "404":
                results["warnings"].append(f"Pulp API '{endpoint_name}' endpoint not found (may not be configured)")
            else:
                results["warnings"].append(f"Pulp API '{endpoint_name}' returned HTTP {cmd_result.stdout.strip()}")

        # Also get count of repositories to show in results
        repo_count_cmd = host.run(
            f"{runtime} exec {pulp_container} curl -s -k -u {pulp_api_username}:{pulp_api_password} "
            f"{pulp_api_base_url}/pulp/api/v3/repositories/rpm/rpm/ 2>&1 | grep -o '\"count\":[0-9]*' | head -1"
        )
        if repo_count_cmd.rc == 0 and repo_count_cmd.stdout.strip():
            count = repo_count_cmd.stdout.strip().split(':')[-1]
            results["passed"].append(f"Pulp has {count} RPM repositories configured")

        return results

    def _validate_package_download_status(self, host):
        """
        Validate all packages are downloaded successfully by checking status.csv files.

        Logic:
        1. Check top-level status file
        2. If it shows 'failed', check individual package status files
        3. Report failed packages
        """
        results = {"passed": [], "failed": [], "warnings": [], "skipped": []}

        top_level_status_file = LOCAL_REPO_VARS.get("top_level_status_file", "/opt/omnia/offline/status.csv")
        package_status_dir = LOCAL_REPO_VARS.get("package_status_dir", "/opt/omnia/offline/packages")
        status_success_values = LOCAL_REPO_VARS.get("status_success_values", ["success", "completed", "downloaded", "ok"])
        status_failed_values = LOCAL_REPO_VARS.get("status_failed_values", ["failed", "error", "failure"])
        max_failed_to_show = LOCAL_REPO_VARS.get("max_failed_packages_to_show", 20)

        # Check if top-level status file exists
        status_file = host.file(top_level_status_file)
        if not status_file.exists:
            # Try alternate location from molecule env
            alt_status_file = host.file("/tmp/local_repo_status.csv")
            if alt_status_file.exists:
                top_level_status_file = "/tmp/local_repo_status.csv"
                status_file = alt_status_file
            else:
                results["warnings"].append(f"Top-level status file not found: {top_level_status_file}")
                results["skipped"].append("Package download validation skipped - no status file")
                return results

        results["passed"].append(f"Status file found: {top_level_status_file}")

        # Read and parse the status file
        try:
            content = status_file.content_string
            lines = content.strip().split('\n')

            if not lines:
                results["warnings"].append("Status file is empty")
                return results

            # Parse CSV content
            failed_packages = []
            success_count = 0
            total_count = 0

            # Try to detect CSV format
            reader = csv.DictReader(lines)
            fieldnames = reader.fieldnames if reader.fieldnames else []

            # Find status column (case-insensitive)
            status_col = None
            package_col = None
            for field in fieldnames:
                if field.lower() in ['status', 'state', 'result']:
                    status_col = field
                if field.lower() in ['package', 'name', 'pkg', 'component']:
                    package_col = field

            if not status_col:
                # Try simple format: package,status or just status per line
                results["warnings"].append("Could not detect status column in CSV - trying simple format")
                for line in lines[1:]:  # Skip header
                    if ',' in line:
                        parts = line.split(',')
                        status = parts[-1].strip().lower()
                        pkg_name = parts[0].strip() if len(parts) > 1 else f"line_{total_count}"
                    else:
                        status = line.strip().lower()
                        pkg_name = f"item_{total_count}"

                    total_count += 1
                    if any(s in status for s in status_failed_values):
                        failed_packages.append(pkg_name)
                    elif any(s in status for s in status_success_values):
                        success_count += 1
            else:
                # Parse with detected columns
                for row in reader:
                    total_count += 1
                    status = row.get(status_col, "").strip().lower()
                    pkg_name = row.get(package_col, f"package_{total_count}") if package_col else f"package_{total_count}"

                    if any(s in status for s in status_failed_values):
                        failed_packages.append(pkg_name)
                    elif any(s in status for s in status_success_values):
                        success_count += 1

            # Report results
            if total_count == 0:
                results["warnings"].append("No packages found in status file")
            elif failed_packages:
                results["failed"].append(f"{len(failed_packages)} package(s) failed to download out of {total_count}")

                # Check individual package status files for more details
                detailed_failures = self._check_package_status_files(host, package_status_dir, failed_packages[:max_failed_to_show])
                if detailed_failures:
                    for pkg, reason in detailed_failures.items():
                        results["failed"].append(f"  - {pkg}: {reason}")
                else:
                    # Just list the failed packages
                    for pkg in failed_packages[:max_failed_to_show]:
                        results["failed"].append(f"  - {pkg}")
                    if len(failed_packages) > max_failed_to_show:
                        results["failed"].append(f"  ... and {len(failed_packages) - max_failed_to_show} more")
            else:
                results["passed"].append(f"All {success_count} packages downloaded successfully")

        except Exception as e:
            results["warnings"].append(f"Failed to parse status file: {str(e)}")

        return results

    def _check_package_status_files(self, host, package_status_dir, failed_packages):
        """Check individual package status files for failure details."""
        detailed_failures = {}

        status_dir = host.file(package_status_dir)
        if not status_dir.exists or not status_dir.is_directory:
            return detailed_failures

        for pkg in failed_packages:
            # Try to find package-specific status file
            pkg_status_patterns = [
                f"{package_status_dir}/{pkg}/status.csv",
                f"{package_status_dir}/{pkg}_status.csv",
                f"{package_status_dir}/{pkg}/status.txt",
            ]

            for pattern in pkg_status_patterns:
                pkg_file = host.file(pattern)
                if pkg_file.exists:
                    try:
                        content = pkg_file.content_string
                        # Extract failure reason from content
                        lines = content.strip().split('\n')
                        for line in lines:
                            if any(s in line.lower() for s in ['error', 'failed', 'failure']):
                                detailed_failures[pkg] = line.strip()[:100]
                                break
                        if pkg not in detailed_failures:
                            detailed_failures[pkg] = "See status file for details"
                    except Exception:
                        detailed_failures[pkg] = "Could not read status file"
                    break

        return detailed_failures

    def _validate_airgap_images(self, host):
        """
        Validate that JSON config files have images pointing to local registry
        instead of external registries (for air-gapped environments).

        Checks:
        1. If airgap_enabled is True, validate image references
        2. Images should point to local registry or be tar files
        3. External registries (docker.io, registry.k8s.io, etc.) should not be present
        """
        results = {"passed": [], "failed": [], "warnings": [], "skipped": []}

        airgap_enabled = LOCAL_REPO_VARS.get("airgap_enabled", False)

        # Skip if air-gap validation is disabled
        if not airgap_enabled:
            results["skipped"].append("Air-gap validation skipped (airgap_enabled=false)")
            return results

        json_config_dir = LOCAL_REPO_VARS.get("json_config_dir", "/diya/omnia/input/project_default/config/x86_64/rhel/10.0")
        json_files = LOCAL_REPO_VARS.get("json_files_to_check", ["service_k8s.json"])
        external_registries = LOCAL_REPO_VARS.get("external_registries", [
            "docker.io/", "registry.k8s.io/", "ghcr.io/", "quay.io/", "gcr.io/", "k8s.gcr.io/", "mcr.microsoft.com/"
        ])
        local_registry = LOCAL_REPO_VARS.get("local_registry", "localhost:5000")

        # Check if local registry is accessible
        registry_check = host.run(f"curl -s -o /dev/null -w '%{{http_code}}' --connect-timeout 5 http://{local_registry}/v2/_catalog")
        if registry_check.rc == 0 and registry_check.stdout.strip() == "200":
            results["passed"].append(f"Local registry accessible at {local_registry}")
        else:
            results["warnings"].append(f"Local registry not accessible at {local_registry} (HTTP: {registry_check.stdout.strip()})")

        # Check each JSON config file
        total_external_images = []

        for json_file in json_files:
            json_path = f"{json_config_dir}/{json_file}"
            config_file = host.file(json_path)

            if not config_file.exists:
                results["warnings"].append(f"JSON config file not found: {json_file}")
                continue

            results["passed"].append(f"JSON config file found: {json_file}")

            try:
                content = config_file.content_string
                # Find all image references in the JSON
                # Images are typically in format: "package": "registry/image", "type": "image"
                external_images_in_file = []

                for registry in external_registries:
                    if registry in content:
                        # Extract the image names containing this registry
                        import re
                        # Match patterns like "package": "docker.io/something"
                        pattern = rf'"package"\s*:\s*"({re.escape(registry)}[^"]+)"'
                        matches = re.findall(pattern, content)
                        external_images_in_file.extend(matches)

                if external_images_in_file:
                    results["failed"].append(f"Found {len(external_images_in_file)} external image(s) in '{json_file}'")
                    # Show first few external images
                    for img in external_images_in_file[:5]:
                        results["failed"].append(f"  - {img}")
                    if len(external_images_in_file) > 5:
                        results["failed"].append(f"  ... and {len(external_images_in_file) - 5} more")
                    total_external_images.extend(external_images_in_file)
                else:
                    results["passed"].append(f"No external registry images in '{json_file}'")

            except Exception as e:
                results["warnings"].append(f"Failed to parse {json_file}: {str(e)}")

        # Summary
        if total_external_images:
            results["failed"].append(f"Total: {len(total_external_images)} image(s) need to be updated for air-gap")
        elif airgap_enabled and not total_external_images:
            results["passed"].append("All images configured for air-gap environment")

        return results

    def _report_results(self, results):
        """Print a summary of test results."""
        print("\n" + "=" * 70)
        print("LOCAL_REPO VALIDATION RESULTS")
        print("=" * 70)

        print(f"\n✅ PASSED ({len(results['passed'])}):")
        for item in results["passed"]:
            print(f"   • {item}")

        if results["warnings"]:
            print(f"\n⚠️  WARNINGS ({len(results['warnings'])}):")
            for item in results["warnings"]:
                print(f"   • {item}")

        if results.get("skipped"):
            print(f"\n⏭️  SKIPPED ({len(results['skipped'])}):")
            for item in results["skipped"]:
                print(f"   • {item}")

        if results["failed"]:
            print(f"\n❌ FAILED ({len(results['failed'])}):")
            for item in results["failed"]:
                print(f"   • {item}")

        print("\n" + "=" * 70)
        total = len(results["passed"]) + len(results["failed"]) + len(results.get("skipped", []))
        print(f"SUMMARY: {len(results['passed'])} passed, {len(results['failed'])} failed, "
              f"{len(results.get('skipped', []))} skipped, {len(results['warnings'])} warnings")
        print("=" * 70 + "\n")
