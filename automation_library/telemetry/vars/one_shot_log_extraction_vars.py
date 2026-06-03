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
One Shot Log Extraction Automation - Configuration Variables.

Contains all constants, paths, and command templates for one-shot combined
log extraction from Kubernetes and Slurm cluster nodes.

Reference Specs:
- BSPEC-LOGEX-2026-001 (Behavior Specification)
- FSPEC-LOGEX-2026-001 (Functional Specification)
- ESPEC-LOGEX-2026-001 (Engineering Specification)
- CSPEC-LOGEX-2026-001 (Component Specification)
- MSPEC-LOGEX-2026-001 (Module Specification)
"""

from typing import Dict, List

# =============================================================================
# Command Configuration (Actual Implementation)
# =============================================================================

# Default mode (full collection scope)
LOG_COLLECTION_COMMAND = "cd /omnia/log_collector && ansible-playbook collect.yml"

# Curated support mode (exclude temporary/stale-old logs)
LOG_COLLECTION_CURATED_MODE = "cd /omnia/log_collector && ansible-playbook collect.yml -e collection_mode=curated_support"

# Playbook path (inside omnia_core container)
COLLECT_PLAYBOOK_PATH = "/omnia/log_collector/collect.yml"

# =============================================================================
# Bundle Naming Pattern
# =============================================================================

# Actual implementation uses: omnia_logs_<YYYYMMDD-HHMMSS>.tar.gz
BUNDLE_NAME_PATTERN = r"omnia_logs_(?P<timestamp>\d{8}-\d{6})\.tar\.gz"
BUNDLE_NAME_FORMAT = "omnia_logs_<YYYYMMDD-HHMMSS>.tar.gz"

# =============================================================================
# Output Paths
# =============================================================================

OUTPUT_PATHS = {
    "default_output_root": "/opt/omnia/collector_logs",
    "workspace_prefix": "omnia_logs_",
    "bundle_extension": ".tar.gz",
    "metadata_filename": "metadata.json",
    "bundle_dir_pattern": "omnia_logs_*",
}

# =============================================================================
# Metadata Fields - Expected in metadata.json (per CSPEC-LOGEX-2026-001 Section 4)
# =============================================================================

# Metadata fields from actual implementation
METADATA_REQUIRED_FIELDS = [
    "bundle_name",
    "tar_relative_path",
    "tar_sha256",
    "bundle_generated_at_utc",
    "bundle_generated_at_local",
    "trigger_user",
    "oim_host_os",
    "identifier",
    "collection_mode",
    "exclusions_applied",
    "warning_count",
    "warnings",
]

# Warning Entry Schema (per CSPEC-LOGEX-2026-001 Section 4.2)
WARNING_ENTRY_FIELDS = [
    "source",
    "node_name",
    "node_ip",
    "reason",
    "message",
    "timestamp",
]

# =============================================================================
# Log Sources - Kubernetes and Slurm
# =============================================================================

LOG_SOURCES = {
    "kubernetes": {
        "description": "Kubernetes cluster logs",
        "sources": [
            "pod_logs",
            "node_logs", 
            "system_logs",
        ],
    },
    "slurm": {
        "description": "Slurm workload manager logs",
        "sources": [
            "job_logs",
            "scheduler_logs",
            "node_logs",
        ],
    },
}

# =============================================================================
# Collection Modes
# =============================================================================

# Collection Modes (Actual Implementation)
COLLECTION_MODES = {
    "full": {
        "description": "Include all available logs including temporary and stale files",
        "excludes_temp": False,
        "excludes_stale": False,
        "extra_vars": None,
        "command": "cd /omnia/log_collector && ansible-playbook collect.yml",
    },
    "curated_support": {
        "description": "Exclude temporary files and stale/old logs",
        "excludes_temp": True,
        "excludes_stale": True,
        "extra_vars": "collection_mode=curated_support",
        "command": "cd /omnia/log_collector && ansible-playbook collect.yml -e collection_mode=curated_support",
        "exclusion_patterns": ["*.tmp", "*.temp", "*.bak", "*.gz", "*.bz2", "*.1", "*.2", "*.3", "*.4", "*.5"],
    },
}

# =============================================================================
# Test File Patterns - For Compatibility Tests
# =============================================================================

TEST_FILES = {
    "temp_files": [
        "/tmp/test.tmp",
        "/var/log/test.swp",
    ],
    "stale_log": "/var/log/old.log",
    "stale_age_days": 60,
}

# =============================================================================
# SHA256 Configuration
# =============================================================================

SHA256_CONFIG = {
    "hash_length": 64,
    "hash_pattern": r"SHA256\s*:\s*([a-fA-F0-9]{64})",
    "compute_command": "sha256sum {bundle_path}",
    "max_compute_time_seconds": 120,
}

# =============================================================================
# Timeouts
# =============================================================================

TIMEOUTS = {
    "collection_start": 30,
    "collection_complete": 600,
    "hash_generation": 120,
    "ssh_connect": 30,
    "command_execution": 300,
}

# =============================================================================
# Exit Codes
# =============================================================================

EXIT_CODES = {
    "success": 0,
    "partial_success": 1,
    "failure": 2,
    "permission_error": 126,
    "not_found": 127,
}

# =============================================================================
# Warning Patterns
# =============================================================================

# Warning Patterns (per CSPEC-LOGEX-2026-001 Section 3.1)
WARNING_PATTERNS = {
    # Unreachable node warning format: "Node <hostname> (<ip>) unreachable; continuing collection for remaining nodes."
    "unreachable_node": r"Node\s+(\S+)\s+\(([0-9.]+)\)\s+unreachable;\s+continuing\s+collection\s+for\s+remaining\s+nodes",
    "missing_source": r"Source file\s+(\S+)\s+not found on node\s+(\S+)",
    "output_not_writable": r"Output directory not writable:\s+(\S+)",
    "archive_failure": r"Archive generation failed:\s+(.+)",
    "disk_full": r"No space left on device",
}

# Actual warning message format from implementation
UNREACHABLE_NODE_MSG_FORMAT = "Node {hostname} ({ip}) not reachable via SSH during stage {stage}: {detail}. Continuing bundle generation."

# =============================================================================
# Command Templates
# =============================================================================

CMD_TEMPLATES: Dict[str, str] = {
    # Execute log collection
    "collect_logs": (
        "{command}"
    ),
    
    # Check if output directory is writable
    "check_writable": (
        "test -w {path} && echo 'writable' || echo 'not_writable'"
    ),
    
    # Set directory permissions
    "set_permissions": (
        "chmod {mode} {path}"
    ),
    
    # Create test temp file
    "create_temp_file": (
        "touch {path}"
    ),
    
    # Create stale file with old timestamp
    "create_stale_file": (
        "touch -d '{days} days ago' {path}"
    ),
    
    # Remove file
    "remove_file": (
        "rm -f {path}"
    ),
    
    # Check file exists
    "file_exists": (
        "test -f {path} && echo 'exists' || echo 'not_exists'"
    ),
    
    # Extract tar archive
    "extract_archive": (
        "tar -xzf {archive_path} -C {extract_dir}"
    ),
    
    # List archive contents
    "list_archive": (
        "tar -tzf {archive_path}"
    ),
    
    # Compute SHA256
    "compute_sha256": (
        "sha256sum {file_path} | awk '{{print $1}}'"
    ),
    
    # Fill disk (for error testing)
    "fill_disk": (
        "dd if=/dev/zero of={path}/fillfile bs=1M count={size_mb} 2>/dev/null || true"
    ),
    
    # Get workspace directory
    "find_workspace": (
        "ls -td {output_root}/{workspace_prefix}* 2>/dev/null | head -1"
    ),
    
    # Get latest bundle
    "find_bundle": (
        "ls -t {output_root}/omnia-logs-*.tar.gz 2>/dev/null | head -1"
    ),
    
    # Read metadata JSON
    "read_metadata": (
        "cat {workspace_path}/metadata.json"
    ),
    
    # Check JSON validity
    "validate_json": (
        "python3 -c \"import json; json.load(open('{file_path}'))\""
    ),
    
    # Get file checksum (excluding metadata timestamp)
    "content_checksum": (
        "find {dir_path} -type f ! -name 'metadata.json' -exec md5sum {{}} \\; | sort | md5sum"
    ),
}

# =============================================================================
# Test Configuration
# =============================================================================

TEST_CONFIG = {
    "idempotency_wait_seconds": 5,
    "verify_archive_integrity": True,
    "cleanup_after_test": True,
}
