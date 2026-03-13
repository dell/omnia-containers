Telemetry
==========

⦾ **When a Kubernetes worker node fails, affected telemetry services may take time to fail over to available worker nodes.**

**Resolution**: No manual intervention is required.  Wait for the telemetry services to recover and fail over automatically. Do not restart pods or nodes during this period, as it may extend recovery time.