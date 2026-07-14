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
Generate dataset overlay directories from dataset_manifest.yml.

Reads the manifest, deep-merges each TC's overrides with project_default/
base files, and writes only changed files into datasets/<tc_name>/.

Usage:
    python generate_datasets.py                  # generate all TCs
    python generate_datasets.py tc01 tc03        # generate specific TCs
    python generate_datasets.py --clean          # remove generated dirs first
    python generate_datasets.py --dry-run        # preview without writing
"""

import argparse
import copy
import json
import os
import shutil
import sys
from pathlib import Path

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
MANIFEST_FILE = SCRIPT_DIR / "dataset_manifest.yml"
BASE_DIR = SCRIPT_DIR / "project_default"

# Files that are always written as-is from manifest (not merged with base)
RAW_FILES = {"pxe_mapping_file.csv"}

# Common base keys in local_repo_config.yml that use default (empty) values
LOCAL_REPO_DEFAULTS = {
    "user_registry": None,
    "user_repo_url_x86_64": None,
    "user_repo_url_aarch64": None,
    "rhel_os_url_x86_64": None,
    "rhel_os_url_aarch64": None,
    "rhel_subscription_repo_config_x86_64": None,
    "rhel_subscription_repo_config_aarch64": None,
    "omnia_repo_url_rhel_x86_64": None,
    "omnia_repo_url_rhel_aarch64": None,
    "additional_repos_x86_64": None,
    "additional_repos_aarch64": None,
}

# Common defaults for software_config.json
SOFTWARE_CONFIG_DEFAULTS = {
    "cluster_os_type": "rhel",
    "cluster_os_version": "10.0",
}

# Default omnia repos (used when TC doesn't specify them)
DEFAULT_OMNIA_REPOS_X86 = [
    {"url": "https://download.docker.com/linux/centos/10/x86_64/stable/",
     "gpgkey": "https://download.docker.com/linux/centos/gpg", "name": "docker-ce"},
    {"url": "https://dl.fedoraproject.org/pub/epel/10/Everything/x86_64/",
     "gpgkey": "https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-10", "name": "epel"},
    {"url": "https://pkgs.k8s.io/core:/stable:/v1.35/rpm/",
     "gpgkey": "https://pkgs.k8s.io/core:/stable:/v1.35/rpm/repodata/repomd.xml.key",
     "name": "kubernetes-v1-35"},
    {"url": "https://download.opensuse.org/repositories/isv:/cri-o:/stable:/v1.35/rpm/",
     "gpgkey": "https://download.opensuse.org/repositories/isv:/cri-o:/stable:/v1.35/rpm/repodata/repomd.xml.key",
     "name": "cri-o-v1-35"},
    {"url": "https://linux.mellanox.com/public/repo/doca/3.2.1/rhel10/x86_64/",
     "gpgkey": "https://linux.mellanox.com/public/repo/doca/3.2.1/rhel10/x86_64/repodata/repomd.xml.key",
     "name": "doca"},
    {"url": "https://developer.download.nvidia.com/compute/cuda/repos/rhel10/x86_64/",
     "gpgkey": "https://developer.download.nvidia.com/compute/cuda/repos/rhel10/x86_64/repodata/repomd.xml.key",
     "name": "cuda"},
    {"url": "https://developer.download.nvidia.com/hpc-sdk/rhel/x86_64",
     "gpgkey": "https://developer.download.nvidia.com/hpc-sdk/rhel/RPM-GPG-KEY-NVIDIA-HPC-SDK",
     "name": "nvidia-hpc-sdk"},
]


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base. Override values win."""
    result = copy.deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = deep_merge(result[key], val)
        else:
            result[key] = copy.deepcopy(val)
    return result


def load_base_file(filename: str):
    """Load a file from project_default/."""
    filepath = BASE_DIR / filename
    if not filepath.exists():
        return None
    if filename.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    elif filename.endswith((".yml", ".yaml")):
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    else:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()


def build_software_config(tc_overrides: dict) -> dict:
    """Build complete software_config.json from TC overrides."""
    result = copy.deepcopy(SOFTWARE_CONFIG_DEFAULTS)
    result.update(tc_overrides)
    return result


def build_local_repo_config(tc_overrides: dict) -> dict:
    """Build complete local_repo_config.yml from TC overrides."""
    result = copy.deepcopy(LOCAL_REPO_DEFAULTS)
    # Apply overrides
    for key, val in tc_overrides.items():
        result[key] = val
    # Fill in default omnia repos if not specified
    if result.get("omnia_repo_url_rhel_x86_64") is None:
        result["omnia_repo_url_rhel_x86_64"] = copy.deepcopy(DEFAULT_OMNIA_REPOS_X86)
    return result


def build_telemetry_config(tc_overrides: dict) -> dict:
    """Build telemetry_config.yml: merge TC overrides with base telemetry."""
    base = load_base_file("telemetry_config.yml")
    if base is None:
        return tc_overrides
    return deep_merge(base, tc_overrides)


def build_storage_config(tc_overrides: dict) -> dict:
    """Build storage_config.yml with default mount_params if not specified."""
    base = load_base_file("storage_config.yml")
    if base is None:
        return tc_overrides
    # Start with base, override with TC values
    result = deep_merge(base, tc_overrides)
    return result


def write_file(output_dir: Path, filename: str, content, dry_run: bool = False):
    """Write a config file to the TC output directory."""
    filepath = output_dir / filename
    if dry_run:
        print(f"  [DRY-RUN] Would write: {filepath}")
        return

    if filename.endswith(".json"):
        with open(filepath, "w", newline="\n", encoding="utf-8") as f:
            json.dump(content, f, indent=4, ensure_ascii=False)
            f.write("\n")
    elif filename.endswith((".yml", ".yaml")):
        with open(filepath, "w", newline="\n", encoding="utf-8") as f:
            f.write("---\n")
            yaml.dump(content, f, default_flow_style=False, sort_keys=False,
                      allow_unicode=True, width=120)
    else:
        with open(filepath, "w", newline="\n", encoding="utf-8") as f:
            f.write(content.rstrip("\n") + "\n")


def generate_tc(tc_name: str, tc_config: dict, dry_run: bool = False, clean: bool = False):
    """Generate a single TC overlay directory."""
    output_dir = SCRIPT_DIR / tc_name

    if clean and output_dir.exists():
        if dry_run:
            print(f"  [DRY-RUN] Would remove: {output_dir}")
        else:
            shutil.rmtree(output_dir)

    if not dry_run:
        output_dir.mkdir(exist_ok=True)

    file_count = 0
    for filename, overrides in tc_config.items():
        if filename in RAW_FILES:
            # CSV: write raw string content
            write_file(output_dir, filename, overrides, dry_run)
            file_count += 1
            continue

        if filename == "software_config.json":
            content = build_software_config(overrides)
        elif filename == "local_repo_config.yml":
            content = build_local_repo_config(overrides)
        elif filename == "telemetry_config.yml":
            content = build_telemetry_config(overrides)
        elif filename == "storage_config.yml":
            content = build_storage_config(overrides)
        elif filename.endswith((".yml", ".yaml")):
            # For other YAML files: just use overrides directly (full replacement)
            content = overrides
        else:
            content = overrides

        write_file(output_dir, filename, content, dry_run)
        file_count += 1

    return file_count


def main():
    parser = argparse.ArgumentParser(
        description="Generate dataset overlay directories from dataset_manifest.yml"
    )
    parser.add_argument("datasets", nargs="*",
                        help="Specific TC names to generate (default: all)")
    parser.add_argument("--clean", action="store_true",
                        help="Remove existing TC directories before generating")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview what would be generated without writing")
    parser.add_argument("--manifest", type=str, default=str(MANIFEST_FILE),
                        help="Path to manifest file (default: dataset_manifest.yml)")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"ERROR: Manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    if not BASE_DIR.exists():
        print(f"ERROR: Base directory not found: {BASE_DIR}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path, "r") as f:
        manifest = yaml.safe_load(f)

    # Filter to requested TCs
    tc_names = list(manifest.keys())
    if args.datasets:
        # Allow partial matching (e.g., "tc01" matches "tc01_production_standard")
        filtered = []
        for req in args.datasets:
            matches = [t for t in tc_names if req in t]
            if not matches:
                print(f"WARNING: No TC matching '{req}' in manifest", file=sys.stderr)
            filtered.extend(matches)
        tc_names = filtered

    if not tc_names:
        print("No TCs to generate.")
        sys.exit(0)

    total_files = 0
    print(f"Generating {len(tc_names)} dataset(s) from {manifest_path.name}...\n")

    for tc_name in tc_names:
        tc_config = manifest[tc_name]
        count = generate_tc(tc_name, tc_config, dry_run=args.dry_run, clean=args.clean)
        total_files += count
        status = "[DRY-RUN]" if args.dry_run else "[OK]"
        print(f"  {status} {tc_name}: {count} overlay files")

    print(f"\nDone — {total_files} files across {len(tc_names)} datasets.")

    # Validation pass (skip in dry-run)
    if not args.dry_run:
        print("\nValidating generated files...")
        errors = []
        for tc_name in tc_names:
            tc_dir = SCRIPT_DIR / tc_name
            for f in tc_dir.iterdir():
                try:
                    if f.suffix == ".json":
                        with open(f, encoding="utf-8") as fh:
                            json.load(fh)
                    elif f.suffix in (".yml", ".yaml"):
                        with open(f, encoding="utf-8") as fh:
                            yaml.safe_load(fh)
                    elif f.suffix == ".csv":
                        with open(f, encoding="utf-8") as fh:
                            lines = fh.readlines()
                        assert len(lines) >= 2, f"CSV too short: {len(lines)} lines"
                except Exception as e:
                    errors.append(f"  {tc_name}/{f.name}: {e}")

        if errors:
            print("VALIDATION ERRORS:")
            for e in errors:
                print(e)
            sys.exit(1)
        else:
            print(f"All files parse correctly.")


if __name__ == "__main__":
    main()
