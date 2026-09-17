# Collect Logs from External Clients to VictoriaLogs

Stream logs from external client nodes (network devices, storage systems, fabric managers) to VictoriaLogs deployed in the Service Kubernetes cluster.

## Overview

This procedure describes how to configure external log sources to send logs to VictoriaLogs (cluster mode) for centralized log collection and analysis.

VictoriaLogs accepts syslog (plaintext and TLS) and HTTP forwarding for log ingestion via the VLAgent LoadBalancer service.

## Prerequisites

- Meet the [VictoriaMetrics connection prerequisites](configure_external_victoria.md#prerequisites),
  because the shared utility requires a healthy VictoriaMetrics deployment.
- Deploy VictoriaLogs and VLAgent through a source whose enabled log channel
  targets `victoria_logs`.
- Ensure the VictoriaLogs and VLAgent LoadBalancer services have external IP
  addresses.
- Ensure the external client can reach vlinsert, vlselect, and VLAgent port
  `514` over the required TCP or UDP protocol.
- Export `OMNIA_DATA_PATH` and `OMNIA_PROJECT_NAME` for the project whose
  connection details must be retrieved.

## Procedure

1. Retrieve the shared Victoria connection details. Choose one execution
   method; do not run both commands for the same operation.

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd src/main
        ./omnia.sh --run telemetry --tags external_victoria
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source "$OMNIA_DATA_PATH/activate-omnia.sh"
        cd src/telemetry
        ansible-playbook playbooks/telemetry.yml --tags external_victoria
        ```

2. Review the project-specific output:

    ```text
    $OMNIA_DATA_PATH/telemetry/output/$OMNIA_PROJECT_NAME/external_victoria/external_victoria_connect_details.yml
    ```

    In a multi-domain environment, always use the output below the applicable
    `OMNIA_PROJECT_NAME`. The file provides these values:

    - `victoria_logs.endpoints.vlinsert.write_endpoint`, which uses port
      `9481` and `/insert/jsonline`.
    - `victoria_logs.endpoints.vlselect.query_endpoint`, which uses port
      `9471` and `/select/logsql/query`.
    - `victoria_logs.endpoints.vlselect.ui_url`, which uses port `9471` and
      `/select/vmui`.
    - `vlagent.syslog_endpoint`, which receives plaintext syslog over TCP or
      UDP on port `514`.

3. To send syslog records, set the host and port from the generated `vlagent`
   section and configure the external client to forward to that endpoint. For
   a Linux client, send a test record with either TCP or UDP:

    === "TCP"

        ```bash title="Run on: external log client"
        VLAGENT_HOST=<vlagent.host>
        VLAGENT_PORT=<vlagent.syslog_port>
        logger --tcp --server "$VLAGENT_HOST" --port "$VLAGENT_PORT" \
          --tag omnia-external "External VictoriaLogs TCP test"
        ```

    === "UDP"

        ```bash title="Run on: external log client"
        VLAGENT_HOST=<vlagent.host>
        VLAGENT_PORT=<vlagent.syslog_port>
        logger --udp --server "$VLAGENT_HOST" --port "$VLAGENT_PORT" \
          --tag omnia-external "External VictoriaLogs UDP test"
        ```

4. To send JSON Lines records directly, set the vlinsert URL from the generated
   file and post one JSON object per line:

    ```bash title="Run on: external log client"
    VL_WRITE_ENDPOINT=<victoria_logs.endpoints.vlinsert.write_endpoint>
    VL_JSON_ENDPOINT="${VL_WRITE_ENDPOINT}?_stream_fields=source&_msg_field=_msg"

    printf '%s\n' \
      '{"_msg":"External VictoriaLogs HTTP test","source":"external-client","level":"info"}' | \
      curl --fail-with-body -H 'Content-Type: application/stream+json' \
        --data-binary @- "$VL_JSON_ENDPOINT"
    ```

## Verification

1. Confirm that the generated file contains:

    ```yaml
    victoria_logs:
      available: true
    vlagent:
      available: true
    ```

2. Set the generated vlselect query endpoint and query for the HTTP test
   record:

    ```bash title="Run on: external log client"
    VL_QUERY_ENDPOINT=<victoria_logs.endpoints.vlselect.query_endpoint>

    curl --fail-with-body --silent --show-error \
      --get "$VL_QUERY_ENDPOINT" \
      --data-urlencode 'query={source="external-client"}'
    ```

3. Open `victoria_logs.endpoints.vlselect.ui_url` in a browser and search for
   `omnia-external` to verify the syslog test record.

Receiving the submitted records confirms that the external ingestion and
query paths are working.

## Troubleshooting

- **VictoriaLogs is reported unavailable:** Enable a log source targeting
  `victoria_logs`, deploy Telemetry, and confirm the vlinsert service has an
  external IP address.
- **VLAgent is reported unavailable:** Inspect the `vlagent` LoadBalancer
  service in the `telemetry` namespace and assign an external IP address.
- **Syslog records are missing:** Confirm that port `514` is allowed for the
  protocol selected by the external client.
- **The export stops before checking logs:** Restore the required
  VictoriaMetrics deployment; the shared utility validates it first.

## Next steps

- Use the generated `powerscale.isi_audit_commands` when PowerScale log
  collection is enabled.
- Retain the generated connection file as the authoritative endpoint output
  for the selected project and domain.
