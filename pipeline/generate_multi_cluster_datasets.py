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
Multi-Cluster Dataset Generator for omnia-artifactory.

Reads cluster definitions from clusters/*/cluster.env, generates per-cluster
datasets using the generate_datasets.py engine from omnia-artifactory, and
outputs them into datasets/<cluster_dataset_name>/ so they are ready for
the GitLab multi-cluster pipeline.

When run via install_gitlab_cicd.py, datasets are uploaded to GitLab automatically.
When run standalone, datasets must be committed and pushed manually.

Usage:
    # Generate datasets for all clusters defined in clusters/
    python generate_multi_cluster_datasets.py

    # Generate for specific clusters
    python generate_multi_cluster_datasets.py --clusters cluster1,cluster2

    # Use a specific base TC as the template for all clusters
    python generate_multi_cluster_datasets.py --base-tc tc01_production_standard

    # Point to a custom omnia-artifactory path
    python generate_multi_cluster_datasets.py --artifactory-path /path/to/omnia-artifactory

    # Clean existing datasets before generating
    python generate_multi_cluster_datasets.py --clean
"""

import importlib.util
import sys
import copy
import json
import shutil
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
CLUSTERS_DIR = SCRIPT_DIR / "clusters"

# DATASETS_DIR is at the omnia-artifactory root (one level up from pipeline/)
DATASETS_DIR = SCRIPT_DIR.parent / "datasets"

# DEFAULT_ARTIFACTORY_PATH is the omnia-artifactory root (parent of pipeline/)
DEFAULT_ARTIFACTORY_PATH = SCRIPT_DIR.parent


def load_cluster_env(env_path):
    """Parse a cluster.env file into a dict."""
    config = {}
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Remove inline comments
            if "#" in line:
                line = line.split("#", 1)[0].strip()
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip().strip("\"'")
    return config


def discover_clusters(clusters_dir, cluster_filter=None):
    """Discover all cluster definitions under clusters_dir.

    Returns a list of (cluster_name, cluster_config) tuples.
    """
    clusters = []
    if not clusters_dir.exists():
        print(f"ERROR: Clusters directory not found: {clusters_dir}")
        sys.exit(1)

    for entry in sorted(clusters_dir.iterdir()):
        env_file = entry / "cluster.env"
        if entry.is_dir() and env_file.exists():
            cluster_name = entry.name
            if cluster_filter and cluster_name not in cluster_filter:
                continue
            config = load_cluster_env(env_file)
            clusters.append((cluster_name, config))

    return clusters


def build_custom_overrides_yaml(clusters, base_tc_name, artifactory_path):
    """Build a custom_overrides.yml structure for generate_datasets.py.

    Each cluster gets a TC named after its DATASET value from cluster.env.
    If BASE_TC is specified in cluster.env, that cluster uses that specific base TC.
    Otherwise, all clusters use the global --base-tc default.

    The base TC's overrides are used as a starting point, with cluster-specific
    values (network IPs, etc.) applied on top.
    """
    # Import the generator's data structures to get the base TC overrides
    gen_module_path = artifactory_path / "utility"
    sys.path.insert(0, str(gen_module_path))

    # We need to import carefully since the module has side-effects
    spec = importlib.util.spec_from_file_location(
        "generate_datasets",
        str(gen_module_path / "generate_datasets.py")
    )
    gen_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen_mod)

    custom_tcs = {}
    for cluster_name, cluster_config in clusters:
        dataset_name = cluster_config.get("DATASET", f"{cluster_name}_config")

        # Use cluster-specific BASE_TC if present, otherwise use global default
        cluster_base_tc = cluster_config.get("BASE_TC", base_tc_name)

        # Get the base TC's overrides (or use defaults if base TC not found)
        base_overrides = gen_mod.TC_OVERRIDES.get(cluster_base_tc, {})
        base_metadata = gen_mod.TC_METADATA.get(cluster_base_tc, {})
        base_software = gen_mod.SOFTWARE_CONFIGS.get(cluster_base_tc, None)

        tc_overrides = copy.deepcopy(base_overrides)

        # Apply cluster-specific overrides from cluster.env
        target_ip = cluster_config.get("TARGET_IP", "")

        # Update admin network with the cluster's target IP as the primary OIM IP
        if "admin_network" not in tc_overrides:
            tc_overrides["admin_network"] = {}
        if target_ip:
            tc_overrides["admin_network"]["primary_oim_admin_ip"] = target_ip

        # Update the provision PXE mapping path to point to this cluster's dataset
        tc_overrides["provision_pxe_mapping_file_path"] = (
            f"/opt/omnia/input/{dataset_name}/pxe_mapping_file.csv"
        )

        tc_def = {
            "metadata": copy.deepcopy(base_metadata),
            "overrides": tc_overrides,
        }

        # Update metadata description to indicate the base TC used
        tc_def["metadata"]["description"] = (
            f"Multi-cluster dataset for {cluster_name} "
            f"(based on {cluster_base_tc})"
        )

        # Include software_config if the base TC had one
        if base_software:
            tc_def["software_config"] = copy.deepcopy(base_software)

        custom_tcs[dataset_name] = tc_def

    return custom_tcs, gen_mod


def generate_datasets(custom_tcs, gen_mod, targets, clean=False):
    """Use the generate_datasets engine to create the dataset directories."""
    # Register custom TCs into the generator's registries
    for tc_name, tc_def in custom_tcs.items():
        if tc_name not in gen_mod.TC_NAMES:
            gen_mod.TC_NAMES.append(tc_name)
        if tc_def.get("metadata"):
            gen_mod.TC_METADATA[tc_name] = tc_def["metadata"]
        if tc_def.get("overrides"):
            gen_mod.TC_OVERRIDES[tc_name] = tc_def["overrides"]
        if tc_def.get("software_config"):
            gen_mod.SOFTWARE_CONFIGS[tc_name] = tc_def["software_config"]
        elif tc_name not in gen_mod.SOFTWARE_CONFIGS:
            default_sw = gen_mod.PROJECT_DEFAULT / "software_config.json"
            gen_mod.SOFTWARE_CONFIGS[tc_name] = json.loads(
                default_sw.read_text(encoding="utf-8")
            )

    # Generate only the requested TCs
    print(f"\nGenerating datasets: {', '.join(targets)}")
    gen_mod.generate(targets=targets, clean=clean)
    print("Dataset generation complete.")


def copy_datasets_to_automation(gen_mod, targets, automation_datasets_dir):
    """Verify generated datasets are in the correct location.

    When integrated into omnia-artifactory, the datasets are generated
    directly in the correct location, so this step is a verification only.
    """
    # If source and destination are the same, skip copying
    if gen_mod.DATASETS_DIR == automation_datasets_dir:
        print("  Datasets are in the correct location (integrated mode).")
        return

    for tc_name in targets:
        src_dir = gen_mod.DATASETS_DIR / tc_name
        dst_dir = automation_datasets_dir / tc_name

        if not src_dir.exists():
            print(f"  WARNING: Source dataset not found: {src_dir}")
            continue

        if dst_dir.exists():
            shutil.rmtree(dst_dir)

        shutil.copytree(src_dir, dst_dir)
        file_count = sum(1 for _ in dst_dir.iterdir())
        print(f"  Copied {tc_name} ({file_count} files) -> {dst_dir}")


def update_cluster_env_datasets(clusters, clusters_dir):
    """Update cluster.env files so DATASET points to the generated dataset name."""
    for cluster_name, cluster_config in clusters:
        env_path = clusters_dir / cluster_name / "cluster.env"
        dataset_name = cluster_config.get("DATASET", f"{cluster_name}_config")

        lines = env_path.read_text().splitlines()
        new_lines = []
        found_dataset = False
        for line in lines:
            if line.strip().startswith("DATASET="):
                new_lines.append(f'DATASET="{dataset_name}"')
                found_dataset = True
            else:
                new_lines.append(line)
        if not found_dataset:
            new_lines.append(f'DATASET="{dataset_name}"')

        env_path.write_text("\n".join(new_lines) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate per-cluster datasets for the multi-cluster pipeline"
    )
    parser.add_argument(
        "--clusters",
        help="Comma-separated list of cluster names to generate for (default: all)",
    )
    parser.add_argument(
        "--base-tc",
        default="tc01_production_standard",
        help="Base test case to use as template (default: tc01_production_standard)",
    )
    parser.add_argument(
        "--artifactory-path",
        default=str(DEFAULT_ARTIFACTORY_PATH),
        help=f"Path to omnia-artifactory repo (default: {DEFAULT_ARTIFACTORY_PATH})",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove existing dataset directories before generating",
    )
    parser.add_argument(
        "--list-base-tcs",
        action="store_true",
        help="List available base test cases and exit",
    )
    args = parser.parse_args()

    artifactory_path = Path(args.artifactory_path)
    if not (artifactory_path / "utility" / "generate_datasets.py").exists():
        print(f"ERROR: generate_datasets.py not found at {artifactory_path}/utility/")
        print("Use --artifactory-path to specify the omnia-artifactory location.")
        sys.exit(1)

    # Quick import to list TCs if requested
    if args.list_base_tcs:
        sys.path.insert(0, str(artifactory_path / "utility"))
        spec = importlib.util.spec_from_file_location(
            "generate_datasets",
            str(artifactory_path / "utility" / "generate_datasets.py")
        )
        gen_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen_mod)
        print("Available base test cases:")
        for tc in gen_mod.TC_NAMES:
            meta = gen_mod.TC_METADATA.get(tc, {})
            desc = meta.get("description", "")
            print(f"  {tc}: {desc}")
        return

    # Discover clusters
    cluster_filter = None
    if args.clusters:
        cluster_filter = [c.strip() for c in args.clusters.split(",")]

    clusters = discover_clusters(CLUSTERS_DIR, cluster_filter)
    if not clusters:
        print("ERROR: No clusters found. Check clusters/ directory.")
        sys.exit(1)

    print(f"Found {len(clusters)} cluster(s):")
    for name, config in clusters:
        base_tc = config.get("BASE_TC", args.base_tc)
        print(f"  {name}: TARGET_IP={config.get('TARGET_IP', 'N/A')}, "
              f"DATASET={config.get('DATASET', 'N/A')}, "
              f"BASE_TC={base_tc}")

    # Build custom TCs and generate datasets
    custom_tcs, gen_mod = build_custom_overrides_yaml(
        clusters, args.base_tc, artifactory_path
    )

    targets = list(custom_tcs.keys())
    generate_datasets(custom_tcs, gen_mod, targets, clean=args.clean)

    # Verify datasets are in the correct location
    print("\nVerifying dataset location...")
    copy_datasets_to_automation(gen_mod, targets, DATASETS_DIR)

    # Ensure cluster.env DATASET values are consistent
    update_cluster_env_datasets(clusters, CLUSTERS_DIR)

    print("\n" + "=" * 60)
    print("Multi-cluster dataset generation complete!")
    print("=" * 60)
    print("\nGenerated datasets:")
    for tc_name in targets:
        dataset_path = DATASETS_DIR / tc_name
        if dataset_path.exists():
            files = sorted(f.name for f in dataset_path.iterdir())
            print(f"\n  {tc_name}/ ({len(files)} files)")
            for f in files:
                print(f"    - {f}")

    print("\nNext steps:")
    print("  1. Review/edit the generated datasets in datasets/")
    print("     (Update IPs, MACs, credentials, etc. for each cluster)")
    print("  2. If run via install_gitlab_cicd.py, files are uploaded to GitLab automatically")
    print("     Otherwise, commit and push to GitLab manually")
    print("  3. Edit datasets in GitLab UI if needed")
    print("  4. Trigger the multi-cluster pipeline")


if __name__ == "__main__":
    main()
