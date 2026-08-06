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

"""Playbook execution and iso_config helpers for install_os automation.

Provides helpers to:
- Load the active iso_config.yml from inside the omnia_core container.
- Run install_os_arm_node.yml with a modified iso_config and capture output.
"""

import re
from typing import Dict, Any, List, Optional

from automation_library.core import run_in_container
from automation_library.install_os.vars import INSTALL_OS_VARS

# Paths inside the omnia_core container
_ISO_CONFIG_PATH = "/opt/omnia/input/project_default/iso_config.yml"
_PLAYBOOK_DIR = "/omnia/utils/install_os_arm_node"
_PLAYBOOK_NAME = "install_os_arm_node.yml"
_CONTAINER = INSTALL_OS_VARS["container_name"]

# Regex for extracting Ansible fatal messages
_FATAL_RE = re.compile(r'fatal:.*?msg"?:\s*"?(.+?)(?:"|$)', re.IGNORECASE)


def load_iso_config_from_container(host) -> Dict[str, Any]:
    """Read the active iso_config.yml from inside omnia_core.

    Returns a dict with the parsed YAML keys, or an error dict
    if the file is missing / unparseable.
    """
    cmd = run_in_container(host, f"cat {_ISO_CONFIG_PATH} 2>/dev/null")
    if cmd.rc != 0:
        return {
            "success": False,
            "error": f"iso_config.yml not found at {_ISO_CONFIG_PATH}",
        }
    try:
        import yaml
        data = yaml.safe_load(cmd.stdout) or {}
        data["success"] = True
        data["error"] = ""
        return data
    except Exception as exc:
        return {"success": False, "error": f"Failed to parse iso_config.yml: {exc}"}


def run_install_os_playbook(
    host,
    config_content: Optional[str] = None,
    remove_config: bool = False,
    extra_vars: Optional[str] = None,
    syntax_check_only: bool = True,
) -> Dict[str, Any]:
    """Run install_os_arm_node.yml inside omnia_core and capture result.

    Args:
        host: testinfra host fixture.
        config_content: If provided, overwrite iso_config.yml with this
            content before running.  The original is backed up and
            restored after the run.
        remove_config: If True, temporarily rename iso_config.yml so
            the playbook encounters a missing file.
        extra_vars: Optional ``-e`` string to pass to ansible-playbook.
        syntax_check_only: If True (default), run with --syntax-check
            to validate YAML syntax only. Set to False to actually execute
            the playbook (which will run validation roles and fail early
            on invalid config).

    Returns:
        Dict with keys: rc, output, errors, error_summary,
        validation_passed.
    """
    backup_cmd = ""
    restore_cmd = ""

    if config_content is not None:
        backup_cmd = (
            f"cp {_ISO_CONFIG_PATH} {_ISO_CONFIG_PATH}.bak 2>/dev/null; "
            f"cat > {_ISO_CONFIG_PATH} << 'EOFCFG'\n{config_content}\nEOFCFG"
        )
        restore_cmd = (
            f"cp {_ISO_CONFIG_PATH}.bak {_ISO_CONFIG_PATH} 2>/dev/null; "
            f"rm -f {_ISO_CONFIG_PATH}.bak"
        )
    elif remove_config:
        backup_cmd = f"mv {_ISO_CONFIG_PATH} {_ISO_CONFIG_PATH}.bak 2>/dev/null"
        restore_cmd = f"mv {_ISO_CONFIG_PATH}.bak {_ISO_CONFIG_PATH} 2>/dev/null"

    # Apply pre-run modification
    if backup_cmd:
        run_in_container(host, backup_cmd)

    # Build playbook command
    pb_cmd = f"ansible-playbook {_PLAYBOOK_NAME}"
    if syntax_check_only:
        pb_cmd += " --syntax-check"
    else:
        pb_cmd += " -v"
    if extra_vars:
        pb_cmd += f" -e '{extra_vars}'"

    result = run_in_container(
        host, f"bash -c 'cd {_PLAYBOOK_DIR} && timeout 120 {pb_cmd}'"
    )

    # Always restore original config
    if restore_cmd:
        run_in_container(host, restore_cmd)

    output = (result.stdout or "") + "\n" + (result.stderr or "")
    errors = _extract_errors(output)

    return {
        "rc": result.rc,
        "output": output,
        "errors": errors,
        "error_summary": "; ".join(errors) if errors else "",
        "validation_passed": result.rc == 0,
    }


def _extract_errors(output: str) -> List[str]:
    """Pull Ansible fatal / failed messages from playbook output."""
    errors: List[str] = []
    for match in _FATAL_RE.finditer(output):
        msg = match.group(1).strip().rstrip('"').rstrip("}")
        if msg:
            errors.append(msg)
    # Also catch "FAILED!" lines
    for line in output.splitlines():
        if "FAILED!" in line and line not in errors:
            stripped = line.strip()
            if stripped and stripped not in errors:
                errors.append(stripped)
    return errors
