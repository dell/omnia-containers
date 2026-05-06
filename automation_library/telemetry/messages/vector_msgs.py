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
Vector Automation - Messages.

This module contains test names and messages for Vector telemetry verification.
"""

# =============================================================================
# Test Names
# =============================================================================

VECTOR_TEST_NAMES = {
    # Functional Tests
    "vector_deployment": "TC-F001: Vector Deployment and End-to-End Pipeline Verification",
    "content_routing": "TC-F002: Content-Type Based Message Routing",
    "topic_discovery": "TC-F003: Dynamic Topic Discovery",
    "metric_normalization": "TC-F004: Metric Format Normalization (PromQL-Queryable)",
    "event_normalization": "TC-F005: Event Format Normalization (LogsQL-Searchable)",
    "dead_letter_routing": "TC-F006: Dead-Letter Routing for Malformed Messages",
    "custom_transforms": "TC-F007: Custom Transform Application and Verification",
    "resource_compliance": "TC-F008: Vector Resource Specification Compliance",
    "metric_enrichment": "TC-F009: Metric Enrichment and Schema Normalization",
    "self_metrics": "TC-F010: Vector Self-Metrics Exposure",
    
    # Negative/Error Tests
    "malformed_handling": "TC-E001: Malformed Message Handling (Multiple Formats)",
    "pipeline_recovery": "TC-E002: Vector Pipeline Failure and Recovery",
    "kafka_unavailability": "TC-E003: Kafka Unavailability and Retry Behavior",
    "vminsert_unavailability": "TC-E004: VictoriaMetrics vminsert Unavailability and Buffering",
    "schema_tolerance": "TC-E004B: Schema Change Tolerance",
    "dead_letter_accumulation": "TC-E005: Dead-Letter Topic Accumulation",
    "transform_modification": "TC-E006: Runtime Transform Modification Constraint",
    
    # Idempotency Tests
    "redeployment_idempotency": "TC-I001: Vector Redeployment Idempotency",
    
    # Security Tests
    "mtls_authentication": "TC-S001: mTLS Authentication to Kafka Brokers",
    "no_plaintext_credentials": "TC-S002: No Plaintext Credentials in Deployed Artifacts",
}

# =============================================================================
# Test Log Messages
# =============================================================================

VECTOR_TEST_LOG_MSGS = {
    # Deployment Verification
    "check_vector_pod": "Checking Vector pod status in telemetry namespace",
    "verify_resource_specs": "Verifying Vector resource specifications",
    "verify_no_pvc": "Verifying Vector has no PVC attached (stateless)",
    "check_pod_running": "Verifying Vector pod is in Running state",
    
    # Message Routing
    "produce_ldms_messages": "Producing LDMS metric messages to Kafka",
    "produce_idrac_messages": "Producing iDRAC event messages to Kafka",
    "query_victoria_metrics": "Querying VictoriaMetrics for LDMS metrics",
    "query_victoria_logs": "Querying VictoriaLogs for iDRAC events",
    "verify_routing": "Verifying message routing to correct databases",
    
    # Topic Discovery
    "create_new_topic": "Creating new Kafka topic for discovery test",
    "wait_discovery": "Waiting for Vector to discover new topic",
    "verify_consumption": "Verifying Vector consumes from new topic",
    
    # Format Normalization
    "verify_promql_queryable": "Verifying metrics are PromQL-queryable",
    "verify_logsql_searchable": "Verifying events are LogsQL-searchable",
    "check_metric_names": "Checking metric names follow Prometheus conventions",
    "check_labels": "Verifying labels are extracted correctly",
    
    # Dead-Letter Routing
    "produce_malformed": "Producing malformed messages to Kafka",
    "check_dead_letter": "Checking dead-letter topic for malformed messages",
    "verify_error_logs": "Verifying errors are logged with message context",
    "check_error_counter": "Checking Vector error counter",
    
    # Custom Transforms
    "verify_transform_config": "Verifying custom transform in Vector ConfigMap",
    "check_transform_applied": "Checking transform is applied to messages",
    "verify_labels_added": "Verifying custom labels are added",
    
    # Self-Metrics
    "discover_metrics_endpoint": "Discovering Vector metrics endpoint",
    "query_self_metrics": "Querying Vector self-metrics",
    "verify_metrics_scraped": "Verifying metrics are scraped by vmagent",
    
    # Failure Recovery
    "kill_vector_pod": "Killing Vector pod to simulate failure",
    "wait_restart": "Waiting for Kubernetes to restart Vector pod",
    "verify_reconnection": "Verifying Vector reconnects to Kafka",
    "check_offset_resume": "Checking Vector resumes from last committed offset",
    
    # Kafka Unavailability
    "scale_kafka_down": "Scaling Kafka StatefulSet to 0 replicas",
    "check_retry_behavior": "Checking Vector retry behavior",
    "scale_kafka_up": "Restoring Kafka cluster",
    "verify_auto_reconnect": "Verifying Vector auto-reconnects after Kafka restoration",
    
    # vminsert Unavailability
    "scale_vminsert_down": "Scaling vminsert Deployment to 0 replicas",
    "verify_buffering": "Verifying Vector buffers messages internally",
    "scale_vminsert_up": "Restoring vminsert",
    "verify_buffer_flush": "Verifying buffered metrics are delivered",
    
    # Security
    "check_mtls_config": "Checking mTLS configuration in Vector ConfigMap",
    "verify_tls_handshake": "Verifying TLS handshake with Kafka brokers",
    "search_credentials": "Searching for plaintext credentials",
    "verify_secrets_usage": "Verifying credentials are stored in Kubernetes Secrets",
}

# =============================================================================
# Test Assert Messages
# =============================================================================

VECTOR_TEST_ASSERT_MSGS = {
    # Deployment
    "vector_pod_running": "Vector pod must be in Running state",
    "resource_specs_match": "Vector resource specs must match FSpec (512Mi/1Gi, 250m/1000m)",
    "no_pvc_attached": "Vector must have no PVC attached (stateless deployment)",
    "zero_restarts": "Vector pod must have 0 restarts",
    
    # Message Routing
    "metrics_in_victoria": "LDMS metrics must appear in VictoriaMetrics",
    "events_in_logs": "iDRAC events must appear in VictoriaLogs",
    "no_cross_routing": "No cross-routing between metrics and events",
    "latency_within_threshold": "Ingestion latency must be ≤ 2 minutes",
    
    # Topic Discovery
    "topic_discovered": "New topic must be discovered within 60 seconds",
    "no_manual_intervention": "No manual Vector restart required",
    
    # Format Normalization
    "promql_queryable": "Metrics must be queryable via PromQL",
    "logsql_searchable": "Events must be searchable via LogsQL",
    "prometheus_naming": "Metric names must follow Prometheus conventions",
    "labels_present": "All expected labels must be present",
    
    # Dead-Letter Routing
    "malformed_in_dead_letter": "Malformed messages must be routed to dead-letter topic",
    "errors_logged": "Errors must be logged with message context",
    "error_counter_incremented": "Error counter must be incremented",
    "no_pipeline_blocking": "Valid messages must not be blocked by malformed messages",
    
    # Custom Transforms
    "transform_applied": "Custom transform must be applied to matching messages",
    "custom_labels_added": "Custom labels must be added correctly",
    "filtering_works": "Filtering logic must work as expected",
    
    # Self-Metrics
    "metrics_endpoint_exists": "Vector must expose metrics endpoint",
    "self_metrics_present": "All expected self-metrics must be present",
    "metrics_scrapable": "Metrics must be scrapable by vmagent",
    
    # Failure Recovery
    "auto_restart": "Kubernetes must automatically restart Vector pod",
    "kafka_reconnect": "Vector must reconnect to Kafka after restart",
    "offset_preserved": "Consumer offset must be preserved",
    "no_data_loss": "No data loss within Kafka retention",
    "no_duplicates": "No duplicate messages in destination databases",
    
    # Kafka Unavailability
    "retry_with_backoff": "Vector must retry with backoff when Kafka unavailable",
    "no_crash": "Vector must not crash when Kafka unavailable",
    "auto_reconnect": "Vector must auto-reconnect after Kafka restoration",
    
    # vminsert Unavailability
    "buffering_enabled": "Vector must buffer messages when vminsert unavailable",
    "buffered_delivered": "Buffered metrics must be delivered after vminsert restoration",
    
    # Security
    "mtls_configured": "Vector must be configured with mTLS for Kafka",
    "tls_encrypted": "All Kafka traffic must be TLS-encrypted",
    "no_plaintext_creds": "No plaintext credentials in logs, ConfigMaps, or manifests",
    "secrets_only": "All credentials must be stored in Kubernetes Secrets",
}

# =============================================================================
# Success/Failure Messages
# =============================================================================

VECTOR_SUCCESS_MSGS = {
    "deployment": "Vector deployment verified successfully",
    "routing": "Message routing verified successfully",
    "normalization": "Format normalization verified successfully",
    "dead_letter": "Dead-letter routing verified successfully",
    "transforms": "Custom transforms verified successfully",
    "self_metrics": "Vector self-metrics verified successfully",
    "recovery": "Pipeline recovery verified successfully",
    "security": "Security configuration verified successfully",
}

VECTOR_FAILURE_MSGS = {
    "deployment": "Vector deployment verification failed",
    "routing": "Message routing verification failed",
    "normalization": "Format normalization verification failed",
    "dead_letter": "Dead-letter routing verification failed",
    "transforms": "Custom transforms verification failed",
    "self_metrics": "Vector self-metrics verification failed",
    "recovery": "Pipeline recovery verification failed",
    "security": "Security configuration verification failed",
}
