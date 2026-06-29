
# Telemetry from OME & SFM


Collect telemetry data from Dell OpenManage Enterprise (OME) and Smart Fabric
Manager (SFM) in addition to direct iDRAC and LDMS metrics.

## Overview


OpenManage Enterprise (OME) aggregates hardware health, alerts, and inventory
data from all Dell servers it manages. Smart Fabric Manager (SFM) provides
network fabric metrics from Dell switches. By integrating OME and SFM
telemetry into Omnia's pipeline, you get:

- Aggregated server health dashboards from OME.
- Network fabric metrics (port throughput, errors) from SFM.
- Correlated views of compute + network performance in Grafana.


## Prerequisites


- OME is deployed and managing the Dell servers in your cluster.
- SFM is deployed and managing Dell networking switches (optional).
- The [Setup Telemetry](setup_telemetry.md) procedure is complete.
- Network connectivity from the K8s service cluster to OME and SFM
  management IPs.
- OME API credentials (read-only user recommended).


## Procedure


1. **Enter the omnia_core container**:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```


2. **Configure OME telemetry** in `omnia_config.yml`:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/omnia_config.yml
   ```


   ```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
   ---
   # OME telemetry configuration
   ome_telemetry_enabled: true
   ome_ip: "10.5.1.50"
   ome_port: 443
   ome_username: "omnia_readonly"
   ome_password: ""  # Set via credentials utility
   ome_collection_interval: 300  # seconds

   # SFM telemetry configuration (optional)
   sfm_telemetry_enabled: true
   sfm_ip: "10.5.1.51"
   sfm_port: 443
   sfm_username: "omnia_readonly"
   sfm_password: ""  # Set via credentials utility
   sfm_collection_interval: 300
   ```


3. **Set OME/SFM credentials** using the credential utility:

   ```bash title="Run on: omnia_core container"
   cd /omnia/utils/credential_utility
   ansible-playbook get_config_credentials.yml --tags telemetry
   ```


4. **Verify OME API access** from the K8s cluster:

   ```bash title="Run on: K8s control plane node"
   curl -sk https://10.5.1.50/api/SessionService/Sessions \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"UserName":"omnia_readonly","Password":"YourPassword","SessionType":"API"}'
   ```


5. **Run the telemetry playbook** to deploy the OME/SFM collectors:

   ```bash title="Run on: omnia_core container"
   cd /omnia
   ansible-playbook telemetry.yml --ask-vault-pass
   ```


   The playbook will:

   - Deploy an OME telemetry collector pod on the K8s cluster.
   - Deploy an SFM telemetry collector pod (if enabled).
   - Configure collectors to push metrics to Kafka.
   - Import pre-built Grafana dashboards for OME and SFM data.


## Verification


1. **Verify OME/SFM collector pods are running**:

   ```bash title="Run on: K8s control plane node"
   kubectl get pods -n telemetry | grep -E "ome|sfm"
   ```


2. **Check collector logs** for successful data collection:

   ```bash title="Run on: K8s control plane node"
   kubectl logs -n telemetry -l app=ome-collector --tail=20
   kubectl logs -n telemetry -l app=sfm-collector --tail=20
   ```


3. **Verify OME metrics in VictoriaMetrics**:

   ```bash title="Run on: K8s control plane node"
   VM_POD=$(kubectl get pod -n telemetry -l app=victoriametrics -o jsonpath='{.items[0].metadata.name}')
   kubectl exec -n telemetry $VM_POD -- \
     curl -s "http://localhost:8428/api/v1/query?query=ome_device_health"
   ```


4. **Check Grafana dashboards** for OME/SFM panels:

   Open Grafana and navigate to the **OME Overview** and **SFM Fabric Health**
   dashboards.


## Next Steps


- [Verify Telemetry](verify_telemetry.md) -- End-to-end telemetry verification.
- [Configure Ldms](configure_ldms.md) -- Add LDMS metrics alongside OME data.


## Troubleshooting


**OME collector returns "authentication failed"**
   Verify credentials:

   ```bash title="Run on: K8s control plane node"
   curl -sk https://10.5.1.50/api/SessionService/Sessions \
     -X POST -H "Content-Type: application/json" \
     -d '{"UserName":"omnia_readonly","Password":"YourPassword","SessionType":"API"}'
   ```


**OME collector returns "connection refused"**
   Check network connectivity:

   ```bash title="Run on: K8s worker node"
   curl -sk https://10.5.1.50/api/ApplicationService/Info
   ```


**SFM metrics not appearing**
   Verify SFM is accessible and the API version is supported:

   ```bash title="Run on: K8s worker node"
   curl -sk https://10.5.1.51/api/
   ```


**Certificate errors with OME/SFM**
   If using self-signed certificates, configure the collectors to skip
   TLS verification (development only) or import the CA certificate.
