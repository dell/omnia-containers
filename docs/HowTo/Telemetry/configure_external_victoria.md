# Collect Telemetry Data from External Clients to VictoriaMetrics

Send metrics from an external client to the VictoriaMetrics cluster deployed
in the Service Kubernetes cluster.

## Overview

External clients write metrics through the VictoriaMetrics `vminsert`
LoadBalancer and query them through the `vmselect` LoadBalancer. The
`external_victoria` utility validates VictoriaMetrics, discovers the
project-specific endpoints, detects TLS, and exports the CA certificate when
TLS is enabled.

## Prerequisites

- Deploy VictoriaMetrics through the Telemetry workflow.
- Ensure the VictoriaMetrics pods are Running in the `telemetry` namespace.
- Ensure `vminsert-victoria-cluster` and `vmselect-victoria-cluster` have
  LoadBalancer external IP addresses.
- External access to VictoriaMetrics is available through:

    - LoadBalancer port `8480` for ingesting (inserting) data.
    - LoadBalancer port `8481` for querying data.

- Ensure the external client can reach the vminsert and vmselect ports.
- Ensure the OIM can reach the Kubernetes VIP over root SSH.
- Export `OMNIA_DATA_PATH` and `OMNIA_PROJECT_NAME` for the project whose
  connection details must be retrieved.

## Procedure

1. Retrieve the Victoria connection details. Choose one execution method; do
   not run both commands for the same operation.

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
    $OMNIA_DATA_PATH/telemetry/output/$OMNIA_PROJECT_NAME/external_victoria/
    |-- ca.crt    # Present only when TLS is enabled
    `-- external_victoria_connect_details.yml
    ```

    In a multi-domain environment, always use the output below the applicable
    `OMNIA_PROJECT_NAME`. The file provides these VictoriaMetrics values:

    - `victoria_metrics.endpoints.vminsert.write_endpoint`
    - `victoria_metrics.endpoints.vmselect.query_endpoint`
    - `victoria_metrics.endpoints.vmselect.ui_url`
    - `victoria_metrics.tls.ca_crt`

    The generated endpoint scheme is `https` when the
    `victoria-tls-certs` Secret exists and `http` otherwise.

3. Set the values from `external_victoria_connect_details.yml`. The import URL
   below is derived from the generated Prometheus remote-write URL so that a
   text sample can be submitted with `curl`:

    ```bash title="Run on: external metrics client"
    VICTORIA_OUTPUT_DIR="$OMNIA_DATA_PATH/telemetry/output/$OMNIA_PROJECT_NAME/external_victoria"
    VM_WRITE_ENDPOINT=<victoria_metrics.endpoints.vminsert.write_endpoint>
    VM_QUERY_ENDPOINT=<victoria_metrics.endpoints.vmselect.query_endpoint>
    VM_IMPORT_ENDPOINT="${VM_WRITE_ENDPOINT%/api/v1/write}/api/v1/import/prometheus"
    ```

4. Push sample metrics. Choose the command that matches the scheme in the
   generated endpoint.

    === "TLS enabled"

        ```bash title="Run on: external metrics client"
        printf '%s\n' \
          'external_temperature_celsius{source="external-client"} 24.7' \
          'external_fan_speed_rpm{source="external-client"} 4200' | \
          curl --fail-with-body --cacert "$VICTORIA_OUTPUT_DIR/ca.crt" \
            --data-binary @- "$VM_IMPORT_ENDPOINT"
        ```

    === "TLS disabled"

        ```bash title="Run on: external metrics client"
        printf '%s\n' \
          'external_temperature_celsius{source="external-client"} 24.7' \
          'external_fan_speed_rpm{source="external-client"} 4200' | \
          curl --fail-with-body --data-binary @- "$VM_IMPORT_ENDPOINT"
        ```

    Applications that support Prometheus remote write must use the generated
    `victoria_metrics.endpoints.vminsert.write_endpoint` directly.

## Verification

Query the sample metric through the generated vmselect endpoint.

=== "TLS enabled"

    ```bash title="Run on: external metrics client"
    curl --fail-with-body --silent --show-error \
      --cacert "$VICTORIA_OUTPUT_DIR/ca.crt" \
      --get "$VM_QUERY_ENDPOINT" \
      --data-urlencode 'query=external_temperature_celsius'
    ```

=== "TLS disabled"

    ```bash title="Run on: external metrics client"
    curl --fail-with-body --silent --show-error \
      --get "$VM_QUERY_ENDPOINT" \
      --data-urlencode 'query=external_temperature_celsius'
    ```

A successful response containing `external_temperature_celsius` confirms that
the external write and query paths are working. The generated
`victoria_metrics.endpoints.vmselect.ui_url` can also be opened in a browser to
query the metric in VMUI.

## Troubleshooting

- **No VictoriaMetrics pods are found:** Enable a metrics route and deploy
  Telemetry.
- **A pod is not Running:** Inspect the VictoriaMetrics pods in the
  `telemetry` namespace before rerunning the export.
- **An external IP is missing:** Assign external IP addresses to the vminsert
  and vmselect LoadBalancer services.
- **Certificate validation fails:** Use the `ca.crt` from the same project's
  latest export; do not reuse a certificate from another domain.
- **The VIP cannot be reached:** Restore root SSH access from the OIM to the
  configured Kubernetes VIP.

## Next steps

- Use the exported values to [connect SFM](configure_sfm.md) or another metrics
  producer.
- Use [Collect Logs from External Clients to VictoriaLogs](configure_external_victoria_logs.md)
  for log ingestion and syslog endpoints exported by the same utility.
