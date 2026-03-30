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
    get_deployment_mode,
    get_victoria_config,
    verify_victoria_persistence_size,
    verify_victoria_single_node_pods,
    verify_victoria_cluster_pods,
    verify_vmagent_pod,
    verify_victoria_services,
    verify_victoria_tls_secret,
    verify_victoria_tls_health,
    verify_victoria_idrac_data,
)
