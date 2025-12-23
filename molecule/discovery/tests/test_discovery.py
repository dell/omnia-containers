"""Testinfra tests for discovery workflow validation.

Validates post-discovery cluster readiness.

Usage:
    ./run_molecule.sh discovery test
    ./run_molecule.sh discovery verify
"""

import os

from automation_library.core import TestLogger
from automation_library.functions.discovery_func import (
    validate_openchami_container,
    validate_s3_provisioning_images,
    validate_discovery_execution,
    validate_node_boot,
    validate_packages_by_group,
    validate_bmc_group_csv,
    validate_slurm_sinfo,
    validate_slurm_srun,
    validate_slurm_ldap,
    validate_slurm_gpu,
    validate_slurm_ib,
    validate_login_sssd,
    validate_login_munge,
    validate_login_slurmd,
    validate_login_srun,
    validate_login_ldap,
    validate_login_compiler_sssd,
    validate_login_compiler_munge,
    validate_login_compiler_slurmd,
    validate_login_compiler_openmpi,
    validate_login_compiler_ucx,
    validate_login_compiler_srun,
    validate_login_compiler_ldap,
    validate_external_ldap_proxy,
)


def _assert_result(log: TestLogger, result: dict):
    if result.get("success"):
        log.passed(result.get("name", "check"), result.get("details") or "")
    else:
        log.failed(result.get("name", "check"), result.get("error") or result.get("details") or "")

    assert result.get("success"), result.get("error") or result.get("details") or "Validation failed"


def _is_verbose() -> bool:
    return str(os.environ.get("DISCOVERY_VERBOSE", "")).strip().lower() in {"1", "true", "yes", "y"}


def _assert_result_with_success_msg(log: TestLogger, result: dict, success_msg: str):
    if result.get("success"):
        log.passed(result.get("name", "check"), success_msg)
    else:
        log.failed(result.get("name", "check"), result.get("error") or result.get("details") or "")

    assert result.get("success"), result.get("error") or result.get("details") or "Validation failed"


def test_openchami_container(host):
    log = TestLogger("Validate OpenCHAMI container")
    log.check("Checking OpenCHAMI container")
    result = validate_openchami_container(host)

    if _is_verbose() and result.get("podman_ps"):
        log.check(f"podman ps -a output:\n{result['podman_ps']}")

    _assert_result_with_success_msg(
        log,
        result,
        "The openchami container is running without errors.",
    )


def test_provisioning_images_in_s3(host):
    log = TestLogger("Validate provisioning images in S3")
    log.check("Checking required objects")
    result = validate_s3_provisioning_images(host)
    _assert_result_with_success_msg(
        log,
        result,
        "All required images for provisioning are available in the S3 bucket.",
    )


def test_discovery_execution(host):
    log = TestLogger("Validate discovery execution")
    log.check("Running discovery playbook and checking success")
    result = validate_discovery_execution(host)
    
    # Show playbook output if available
    if _is_verbose() and result.get("output"):
        output_lines = result["output"].split("\n")[-20:]  # Last 20 lines
        output_summary = "\n".join(line for line in output_lines if line.strip())
        if output_summary:
            log.check(f"Playbook output:\n{output_summary}")
    
    _assert_result_with_success_msg(
        log,
        result,
        "discovery.yml runs successfully with exit code 0.",
    )


def test_node_boot_validation(host):
    log = TestLogger("Validate node boot")
    log.check("Checking nodes are reachable via ping and SSH")
    result = validate_node_boot(host)
    
    # Show booted and non-booted node lists
    booted = result.get("booted_nodes", [])
    non_booted = result.get("non_booted_nodes", [])
    if _is_verbose():
        if booted:
            log.check(f"Booted nodes: {', '.join(booted)}")
        if non_booted:
            log.check(f"Non-booted nodes: {', '.join(non_booted)}")
    
    _assert_result_with_success_msg(
        log,
        result,
        "Nodes are reachable via ping and SSH; report includes booted and non-booted node lists.",
    )


def test_package_installation(host):
    log = TestLogger("Validate package installation")
    log.check("Checking required packages are installed on nodes")
    result = validate_packages_by_group(host)
    
    # Show missing packages if any
    missing = result.get("missing", [])
    if _is_verbose() and missing:
        for m in missing[:10]:  # Show first 10 missing
            log.check(f"Missing: {m.get('package')} on {m.get('node')} ({m.get('group')})")
    
    _assert_result_with_success_msg(
        log,
        result,
        "All required packages are installed on nodes according to their functional group.",
    )


def test_bmc_group_file(host):
    log = TestLogger("Validate BMC Group File")
    log.check("Checking bmc_group_data.csv generation")
    result = validate_bmc_group_csv(host)

    if _is_verbose() and result.get("csv_content"):
        log.check(f"bmc_group_data.csv content:\n{result['csv_content']}")

    _assert_result_with_success_msg(
        log,
        result,
        "BMC Group File: bmc_group.csv is generated correctly when idrac_telemetry_support is enabled.",
    )


def _assert_simple_command_result(log: TestLogger, result: dict, success_msg: str):
    if _is_verbose() and (result.get("out") or result.get("err") or result.get("status")):
        status = (result.get("status") or "").strip()
        if status:
            log.check(
                f"rc={result.get('rc')}\nstdout:\n{(result.get('out') or '').strip()}\nstderr:\n{(result.get('err') or '').strip()}\nstatus:\n{status}"
            )
        else:
            log.check(
                f"rc={result.get('rc')}\nstdout:\n{(result.get('out') or '').strip()}\nstderr:\n{(result.get('err') or '').strip()}"
            )
    _assert_result_with_success_msg(log, result, success_msg)


def test_slurm_sinfo(host):
    log = TestLogger("Validate Slurm sinfo")
    log.check("Checking sinfo")
    result = validate_slurm_sinfo(host)
    _assert_simple_command_result(log, result, "Slurm sinfo succeeded")


def test_slurm_srun(host):
    log = TestLogger("Validate Slurm srun")
    log.check("Checking srun")
    result = validate_slurm_srun(host)
    _assert_simple_command_result(log, result, "Slurm srun succeeded")


def test_slurm_ldap(host):
    log = TestLogger("Validate Slurm LDAP")
    log.check("Checking LDAP lookup from Slurm controller")
    result = validate_slurm_ldap(host)
    _assert_simple_command_result(log, result, "Slurm LDAP lookup succeeded")


def test_slurm_gpu(host):
    log = TestLogger("Validate Slurm GPU")
    log.check("Checking GPU via srun")
    result = validate_slurm_gpu(host)
    _assert_simple_command_result(log, result, "Slurm GPU check succeeded")


def test_slurm_ib(host):
    log = TestLogger("Validate Slurm IB")
    log.check("Checking IB via srun")
    result = validate_slurm_ib(host)
    _assert_simple_command_result(log, result, "Slurm IB check succeeded")


def test_login_node_sssd(host):
    log = TestLogger("Validate Login Node sssd")
    log.check("Checking sssd")
    result = validate_login_sssd(host)
    _assert_simple_command_result(log, result, "Login Node sssd is active")


def test_login_node_munge(host):
    log = TestLogger("Validate Login Node munge")
    log.check("Checking munge")
    result = validate_login_munge(host)
    _assert_simple_command_result(log, result, "Login Node munge is active")


def test_login_node_slurmd(host):
    log = TestLogger("Validate Login Node slurmd")
    log.check("Checking slurmd")
    result = validate_login_slurmd(host)
    _assert_simple_command_result(log, result, "Login Node slurmd is active")


def test_login_node_srun(host):
    log = TestLogger("Validate Login Node srun")
    log.check("Checking srun")
    result = validate_login_srun(host)
    _assert_simple_command_result(log, result, "Login Node srun succeeded")


def test_login_node_ldap(host):
    log = TestLogger("Validate Login Node LDAP")
    log.check("Checking LDAP lookup")
    result = validate_login_ldap(host)
    _assert_simple_command_result(log, result, "Login Node LDAP lookup succeeded")


def test_login_compiler_sssd(host):
    log = TestLogger("Validate Login Compiler sssd")
    log.check("Checking sssd")
    result = validate_login_compiler_sssd(host)
    _assert_simple_command_result(log, result, "Login Compiler sssd is active")


def test_login_compiler_munge(host):
    log = TestLogger("Validate Login Compiler munge")
    log.check("Checking munge")
    result = validate_login_compiler_munge(host)
    _assert_simple_command_result(log, result, "Login Compiler munge is active")


def test_login_compiler_slurmd(host):
    log = TestLogger("Validate Login Compiler slurmd")
    log.check("Checking slurmd")
    result = validate_login_compiler_slurmd(host)
    _assert_simple_command_result(log, result, "Login Compiler slurmd is active")


def test_login_compiler_openmpi(host):
    log = TestLogger("Validate Login Compiler OpenMPI")
    log.check("Checking OpenMPI")
    result = validate_login_compiler_openmpi(host)
    _assert_simple_command_result(log, result, "OpenMPI is installed")


def test_login_compiler_ucx(host):
    log = TestLogger("Validate Login Compiler UCX")
    log.check("Checking UCX")
    result = validate_login_compiler_ucx(host)
    _assert_simple_command_result(log, result, "UCX is installed")


def test_login_compiler_srun(host):
    log = TestLogger("Validate Login Compiler srun")
    log.check("Checking srun")
    result = validate_login_compiler_srun(host)
    _assert_simple_command_result(log, result, "Login Compiler srun succeeded")


def test_login_compiler_ldap(host):
    log = TestLogger("Validate Login Compiler LDAP")
    log.check("Checking LDAP lookup")
    result = validate_login_compiler_ldap(host)
    _assert_simple_command_result(log, result, "Login Compiler LDAP lookup succeeded")


def test_external_ldap_proxy(host):
    log = TestLogger("Validate External LDAP Proxy")
    log.check("Checking external LDAP proxy via ldapsearch in omnia_auth")
    result = validate_external_ldap_proxy(host)

    if _is_verbose() and (result.get("out") or result.get("err")):
        log.check(
            f"ldapsearch (target={result.get('target')} user={result.get('ldap_user')}): rc={result.get('rc')}\nstdout:\n{(result.get('out') or '').strip()}\nstderr:\n{(result.get('err') or '').strip()}"
        )

    _assert_result_with_success_msg(
        log,
        result,
        "External LDAP Proxy Validation: ldapsearch succeeded and expected user is visible.",
    )
