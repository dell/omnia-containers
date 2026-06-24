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

"""Telemetry functions module."""

from .idrac_telemetry_func import (
    get_service_kube_node_count,
    verify_idrac_telemetry_pod_count,
    verify_all_telemetry_pods_running,
    verify_mysql_data_in_pods,
    verify_receiver_collecting_metrics,
    has_activated_ips,
)

# Shared functions (used across all telemetry modules)
from .shared_func import (
    # Cache management
    clear_cache,
    # Config reading (with caching)
    get_telemetry_config,
    get_telemetry_storage_config,
    get_software_config,
    # Enable checks
    is_kafka_enabled,
    is_victoria_enabled,
    is_idrac_telemetry_enabled,
    is_ldms_enabled,
    get_activated_service_tags,
    # Test helper functions
    get_admin_ip,
    skip_if_kafka_not_enabled,
    skip_if_victoria_not_enabled,
    skip_if_ldms_not_enabled,
    # VictoriaLogs checks
    is_victoria_logs_enabled,
    skip_if_victoria_logs_not_enabled,
    # PowerScale checks
    is_powerscale_metrics_enabled,
    is_powerscale_logs_enabled,
    skip_if_powerscale_not_enabled,
)

from .kafka_func import (
    get_kafka_config_from_telemetry,
    verify_kafka_config_match,
    verify_kafka_topics_via_rest,
    get_kafka_bridge_ip,
    verify_ldms_pods_running,
    verify_ldms_services_ports,
    verify_idrac_data_in_kafka,
    verify_ldms_data_in_kafka,
    verify_ldms_earliest_data_in_kafka,
    get_ldms_sampler_plugins,
    get_domain_name,
    get_ldms_node_hostnames,
)

from .victoria_func import (
    get_victoria_config,
    verify_victoria_persistence_size,
    verify_victoria_cluster_pods,
    verify_vmagent_pod,
    verify_victoria_services,
    verify_victoria_tls_secret,
    verify_victoria_tls_health,
    verify_victoria_idrac_data,
)

# Delete node verification functions
from .delete_node_func import (
    get_deleted_nodes,
    get_deleted_nodes_cached,
    clear_deleted_nodes_cache,
    update_pxe_backup,
    get_deleted_ldms_hostnames,
    get_deleted_service_tags,
    get_deleted_bmc_ips,
    save_pxe_backup,
    skip_if_no_deleted_nodes,
    verify_ldms_deleted_node_in_kafka,
    verify_idrac_deleted_node_in_kafka,
    verify_idrac_deleted_node_in_mysql,
    verify_idrac_deleted_node_in_victoria,
)

# VictoriaLogs functions (all consolidated in victoria_logs_func.py)
from .victoria_logs_func import (
    get_victoria_logs_config,
    get_victoria_logs_storage_config,
    verify_victoria_logs_storage_size,
    verify_victoria_logs_cluster_pods,
    verify_vlagent_pod,
    verify_victoria_logs_services,
    verify_victoria_logs_tls_secret,
    verify_victoria_logs_health,
    verify_victoria_logs_query,
    verify_vlagent_configmap,
    verify_vlagent_pvc,
    verify_vlagent_syslog_service,
    inject_test_syslog,
    verify_syslog_received,
    # Destructive test functions
    verify_all_vlstorage_pods_down_behavior,
    verify_all_vlinsert_pods_down_behavior,
    verify_all_vlselect_pods_down_behavior,
    verify_complete_cluster_failure_recovery,
    verify_single_vlstorage_pod_failure,
    verify_single_vlinsert_pod_failure,
    verify_single_vlselect_pod_failure,
    # Cleanup test functions
    verify_retention_cleanup_cycle,
    verify_default_retention_period,
    verify_victoria_logs_independent_cleanup,
)

# PowerScale functions
from .powerscale_func import (
    get_powerscale_config,
    get_powerscale_deployment_mode,
    is_onefs_api_configured,
    verify_powerscale_deployment,
    verify_powerscale_metrics,
    verify_powerscale_syslog,
    verify_victoria_powerscale_data,
)

# Failover test functions (poweroff/reboot)
from .failover_func import (
    get_k8s_worker_nodes,
    select_target_node_for_poweroff,
    poweroff_node,
    wait_for_node_down,
    get_telemetry_pods_on_node,
    get_all_telemetry_pods,
    wait_for_pods_reschedule,
    verify_pods_not_on_node,
    verify_all_pods_running,
    reboot_node,
    wait_for_node_online,
    wait_for_cloudinit_done,
    wait_for_node_rejoin_cluster,
)

# VAST telemetry functions
from .vast_telemetry_func import (
    is_vast_telemetry_enabled,
    get_vast_config,
    verify_vast_scrape_active,
    verify_vast_tls_basic_auth,
    verify_vast_label_enrichment,
    verify_vast_internal_remotewrite,
    verify_vast_scrape_interval,
    verify_vast_deployment,
    verify_vast_scrape_duration,
    verify_vast_metric_coverage,
    verify_vast_tls_enforcement,
    verify_vast_no_plaintext_credentials,
    verify_vast_pod_delete_and_recovery,
)

# UFM telemetry functions
from .ufm_telemetry_func import (
    is_ufm_telemetry_enabled,
    is_ufm_logs_enabled,
    get_ufm_config,
    get_additional_remote_write_endpoints,
    verify_ufm_scrape_active,
    verify_ufm_dual_remotewrite,
    verify_ufm_syslog_ingestion,
    verify_ufm_deployment,
    verify_ufm_tls_basic_auth,
    verify_ufm_label_enrichment,
    verify_ufm_internal_remotewrite,
    verify_ufm_scrape_interval,
    verify_ufm_scrape_latency,
    verify_ufm_tls_enforcement,
    verify_ufm_no_plaintext_credentials,
)

# Vector verification functions
from .vector_func import (
    verify_vector_pod_running,
    verify_vector_resource_specs,
    verify_vector_no_pvc,
    verify_vector_configmap_exists,
    verify_all_vector_configmaps,
    verify_vector_mtls_config,
    get_vector_pod_logs,
    verify_vector_no_errors_in_logs,
    verify_no_plaintext_credentials,
    verify_vector_self_metrics_endpoint,
    delete_vector_pod,
    rollout_restart_vector,
    scale_vector_deployment,
    create_kafka_topic,
    produce_test_message_to_kafka,
    query_victoria_metrics,
    query_victoria_logs,
)
