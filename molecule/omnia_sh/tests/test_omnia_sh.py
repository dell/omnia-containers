"""
Testinfra tests for omnia.sh installation verification.
"""

from automation_library.testing import TestLogger
from automation_library.messages.omnia_sh_msgs import (
    TEST_VARS as VARS, TEST_NAMES, TEST_LOG_MSGS as LOG_MSGS, TEST_ASSERT_MSGS as ASSERT_MSGS
)


def test_omnia_core_container_file_exists(host):
    """Verify omnia_core.container file is present."""
    log = TestLogger(TEST_NAMES["container_file"])
    path = VARS["container_file"]
    
    log.check(f"Checking file: {path}")
    f = host.file(path)
    
    if f.exists:
        info = host.run(f"ls -la {path}").stdout.strip()
        log.passed(LOG_MSGS["file_exists"], info)
    else:
        log.failed(LOG_MSGS["file_not_found"], f"Expected: {path}")
    
    assert f.exists, ASSERT_MSGS["file_not_found"].format(path=path)


def test_omnia_core_service_running(host):
    """Verify omnia_core systemd service is running."""
    log = TestLogger(TEST_NAMES["service_running"])
    service = VARS["service_name"]
    
    log.check(f"Checking service: {service}")
    status = host.run(f"systemctl is-active {service}").stdout.strip()
    info = host.run(f"systemctl status {service} --no-pager -l 2>/dev/null | head -10").stdout.strip()
    
    if status == "active":
        log.passed(LOG_MSGS["service_active"], info)
    else:
        log.failed(LOG_MSGS["service_inactive"].format(status=status), info)
    
    assert status == "active", ASSERT_MSGS["service_not_active"].format(status=status)


def test_oim_metadata_file_exists(host):
    """Verify oim_metadata.yml file is present."""
    log = TestLogger(TEST_NAMES["metadata_file"])
    path = VARS["metadata_file"]
    
    log.check(f"Checking file: {path}")
    f = host.file(path)
    
    if f.exists:
        content = host.run(f"head -15 {path}").stdout.strip()
        log.passed(LOG_MSGS["file_exists"], content)
    else:
        log.failed(LOG_MSGS["file_not_found"], f"Expected: {path}")
    
    assert f.exists, ASSERT_MSGS["file_not_found"].format(path=path)


def test_passwordless_ssh_to_container(host):
    """Verify passwordless SSH from OIM server to omnia_core container."""
    log = TestLogger(TEST_NAMES["ssh_to_container"])
    alias = VARS["ssh_alias"]
    timeout = VARS["ssh_timeout"]
    
    log.check(f"Testing SSH: OIM server → {alias}")
    cmd = host.run(f"ssh -o BatchMode=yes -o ConnectTimeout={timeout} {alias} 'whoami && pwd && echo SSH_OK'")
    output = cmd.stdout.strip()
    success = cmd.rc == 0 and "SSH_OK" in output
    
    if success:
        log.passed(LOG_MSGS["ssh_success"], output)
    else:
        log.failed(LOG_MSGS["ssh_failed"], f"RC: {cmd.rc}\nError: {cmd.stderr}")
    
    assert success, ASSERT_MSGS["ssh_failed"].format(error=cmd.stderr)


def test_passwordless_ssh_from_container_to_host(host):
    """Verify passwordless SSH from omnia_core container to OIM server."""
    log = TestLogger(TEST_NAMES["ssh_from_container"])
    alias = VARS["ssh_alias"]
    oim_ip = VARS["oim_server_ip"]
    timeout = VARS["ssh_timeout"]
    
    assert oim_ip, ASSERT_MSGS["config_missing"]
    
    log.check(f"Testing SSH: {alias} → OIM server ({oim_ip})")
    cmd = host.run(
        f"ssh -o BatchMode=yes -o ConnectTimeout={timeout} {alias} "
        f"'ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout={timeout} {oim_ip} "
        f"whoami && echo SSH_REVERSE_OK'"
    )
    output = cmd.stdout.strip()
    success = cmd.rc == 0 and "SSH_REVERSE_OK" in output
    
    if success:
        log.passed(LOG_MSGS["ssh_success"], output)
    else:
        log.failed(LOG_MSGS["ssh_failed"], f"RC: {cmd.rc}\nError: {cmd.stderr}")
    
    assert success, ASSERT_MSGS["ssh_failed"].format(error=cmd.stderr)
