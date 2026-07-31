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

"""Upgrade and Rollback Functions Module."""

from .common_func import (
    compare_versions,
    get_oim_metadata,
    check_container_service_status,
)
from .upgrade_core_func import (
    validate_upgrade_versions,
    validate_versions,
    validate_config,
    validate_clone_path_conflict,
    check_backup_exists,
    check_pre_upgrade_container,
    clone_upgrade_repo,
    build_core_image,
    verify_podman_image,
    download_omnia_sh,
    run_omnia_upgrade,
    verify_backup_directory,
    verify_post_upgrade_state,
)
from .prepare_upgrade_func import run_prepare_upgrade
from .backup_verify_func import verify_backup_md5sum
from .rollback_core_func import (
    verify_rollback_precondition,
    check_rollback_image,
    download_omnia_sh_for_rollback,
    run_omnia_rollback,
    verify_rollback_container,
    verify_rollback_backup_md5sum,
)
from .upgrade_yml_func import (
    check_upgrade_yml_exists,
    run_upgrade_yml,
    verify_upgrade_manifest,
    verify_manifest_component_status,
    check_software_component_enabled,
    verify_cps_at_target,
    verify_workers_at_target,
    verify_etcd_backup_exists,
    verify_pdbs_healthy,
    verify_crio_storage_preserved,
    verify_bss_params_updated,
    verify_kube_vip_ha,
    verify_strimzi_upgraded,
    verify_kraft_migration,
    verify_telemetry_phase1_gate,
    verify_security_permissions,
    verify_cluster_unchanged,
    verify_rollback_to_source,
    verify_rollback_etcd_restored,
    verify_rollback_helm_restored,
    verify_rollback_telemetry_healthy,
    verify_rollback_metallb_cleaned,
    verify_rollback_csi_cleaned,
)
from .slurm_upgrade_func import (
    check_slurm_upgrade_state,
    run_slurm_upgrade,
    verify_slurm_pre_upgrade,
    capture_slurm_pre_upgrade_state,
    save_slurm_pre_upgrade_state,
    verify_slurm_nfs_mount,
    verify_slurm_conf_backup,
    verify_mysql_datadir_backup,
    verify_hpc_tracking_cleanup,
    verify_no_running_jobs,
    verify_all_nodes_idle,
    verify_slurmctld_post_upgrade,
    verify_slurmd_post_upgrade,
    verify_munge_post_upgrade,
    verify_sbatch_post_upgrade,
    verify_srun_post_upgrade,
)
from .snapshot_func import (
    save_precheck_snapshot,
    load_precheck_snapshot,
)

__all__ = [
    "compare_versions",
    "get_oim_metadata",
    "check_container_service_status",
    "validate_upgrade_versions",
    "validate_versions",
    "validate_config",
    "validate_clone_path_conflict",
    "check_backup_exists",
    "check_pre_upgrade_container",
    "clone_upgrade_repo",
    "build_core_image",
    "verify_podman_image",
    "download_omnia_sh",
    "run_omnia_upgrade",
    "verify_backup_directory",
    "verify_post_upgrade_state",
    "run_prepare_upgrade",
    "verify_backup_md5sum",
    "verify_rollback_precondition",
    "check_rollback_image",
    "download_omnia_sh_for_rollback",
    "run_omnia_rollback",
    "verify_rollback_container",
    "verify_rollback_backup_md5sum",
    "check_upgrade_yml_exists",
    "run_upgrade_yml",
    "verify_upgrade_manifest",
    "verify_manifest_component_status",
    "check_software_component_enabled",
]
