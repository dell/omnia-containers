# Configure LDMS (Lightweight Distributed Metric Service) Telemetry


Configure deployment of Lightweight Distributed Metric Service (LDMS) to collect in-band telemetry from Slurm clusters.

## Overview


LDMS collects system metrics such as CPU, memory, network, I/O, and Slurm job statistics. During deployment, Omnia attaches LDMS aggregator and store pods to the admin network. This improves throughput between Slurm nodes and the Kubernetes cluster.

### Components

- **LDMS producer (collector)** -- Collects local system metrics and runs on Slurm controller, compute, and login nodes.
- **LDMS aggregator** -- Receives and aggregates metrics from producers. Runs as a Kubernetes pod.
- **LDMS store** -- Buffers and stores metric batches reliably. Runs as a Kubernetes pod.
- **Kafka broker** -- Handles telemetry streaming for consumption by downstream systems.

For more details on LDMS, see [Lightweight Distributed Metric Service](https://github.com/ovis-hpc/ldms).

### Data Flow

```
Slurm Compute Nodes (LDMS Sampler) → LDMS Aggregator → LDMS Store → Kafka
                                                                      ↓
                                                        (Optional: Vector-LDMS Bridge)
                                                                      ↓
                                                        Vector-LDMS → vmagent-vector → VictoriaMetrics
```

LDMS data is always sent to Kafka. To route LDMS metrics to VictoriaMetrics, enable the [Vector-LDMS bridge](#step-5-enable-vector-ldms-bridge-optional).

### Supported Metrics

The following LDMS plugins are supported in Omnia:

| Plugin | Metrics Collected |
| --- | --- |
| `meminfo` | Memory usage statistics |
| `procstat2` | Process statistics |
| `vmstat` | Virtual memory statistics |
| `loadavg` | System load average |
| `procnetdev2` | Network interface statistics |

!!! note

    The LDMS Slurm sampler metrics are not supported in the current telemetry deployment.


## Prerequisites


Complete the following before you configure LDMS telemetry. Provisioning the
cluster happens **after** this configuration, as part of the deployment sequence.

- The `omnia_core` container is deployed on the OIM. See
  [Deploy Omnia Core](../Setup/deploy_omnia_core.md).
- The mapping file (`pxe_mapping_file.csv`) is created. See
  [Create Mapping File](../Setup/create_mapping_file.md).
- Ensure that `provision.yml` has been executed successfully with
  `service_kube_control_plane` and `service_kube_node` in the mapping file.
- Access to the `ovis-ldms` RPM repository for each node architecture in your
  cluster (x86_64 and/or aarch64).


## Procedure


### Step 1: Add Required Software to software_config.json

LDMS requires the LDMS sampler on Slurm nodes and the LDMS aggregator on the
service K8s cluster. Add the following entries to the `softwares` list in
`software_config.json`. If any entry is missing, Omnia skips LDMS deployment and
logs an informational message. For the full file structure, see the
[software_config.json reference](../../Reference/Configuration/software_config.md).

```json title="software_config.json -- required for LDMS telemetry"
{
    "softwares": [
        {"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]},
        {"name": "slurm_custom", "arch": ["x86_64", "aarch64"]},
        {"name": "ldms", "arch": ["x86_64", "aarch64"]}
    ]
}
```

!!! note

    List each architecture present in your cluster in the `arch` array. Include
    `aarch64` for `slurm_custom` and `ldms` only if you have aarch64 Slurm nodes.

### Step 2: Configure LDMS Repositories in local_repo_config.yml

The `ldms` software entry pulls the `ovis-ldms` RPM from a repository named `ldms`.
Define this repository for each architecture in your cluster under
`user_repo_url_x86_64` and/or `user_repo_url_aarch64` in `local_repo_config.yml`.

```yaml title="local_repo_config.yml -- LDMS repository"
user_repo_url_x86_64:
  - { url: "http://repos.example.com/ldms-x86_64/", gpgkey: "", sslcacert: "", sslclientkey: "", sslclientcert: "", name: "ldms" }

# Provide the aarch64 repository only if you have aarch64 Slurm nodes
user_repo_url_aarch64:
  - { url: "http://repos.example.com/ldms-aarch64/", gpgkey: "", sslcacert: "", sslclientkey: "", sslclientcert: "", name: "ldms" }
```

!!! important

    The repository `name` must be exactly `ldms` to match the `repo_name` referenced
    by the `ovis-ldms` package. See the
    [local_repo_config.yml reference](../../Reference/Configuration/local_repo_config.md).

### Step 3: Add Required Nodes to the Mapping File

LDMS requires both a service K8s cluster (aggregator) and Slurm nodes (samplers).
In `pxe_mapping_file.csv`, ensure the following functional groups are present:

- `slurm_control_node` (mandatory; Slurm controller running the LDMS sampler)
- `slurm_node` (Slurm compute nodes running the LDMS sampler)
- `service_kube_control_plane` (three control plane nodes)
- `service_kube_node` (at least one worker node)

```csv title="pxe_mapping_file.csv -- example rows"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_control_node_x86_64,grp0,JS8MN34,,scnode,04:32:01:DD:9D:F0,172.16.107.91,6c:3c:8c:85:bd:a6,100.10.0.115,,
slurm_node_x86_64,grp1,1T8MN34,GZF6ZS3,snode1,04:32:01:DE:18:D0,172.16.107.92,6c:3c:8c:85:be:a6,100.10.0.116,,
service_kube_control_plane_x86_64,grp4,H94M8F3,,kcp1,BC:97:E1:F0:94:F0,172.16.107.96,b0:7b:25:d8:4a:f4,100.10.1.99,,
service_kube_control_plane_x86_64,grp5,2LXT933,,kcp2,BC:97:E1:F0:95:10,172.16.107.97,b0:7b:25:d8:4b:04,100.10.1.100,,
service_kube_control_plane_x86_64,grp7,8X697C3,,kcp3,BC:97:E1:F0:95:30,172.16.107.98,b0:7b:25:d8:4b:14,100.10.1.101,,
service_kube_node_x86_64,grp6,GZF6ZS3,,kn,EC:2A:72:32:C6:98,172.16.107.95,ec:2a:72:3b:a8:52,100.10.0.209,,
```

!!! note

    If you have aarch64 Slurm nodes, add rows with the `_aarch64` suffix (for example, `slurm_node_aarch64`) to the mapping file.

For the full format, see the
[PXE mapping file reference](../../Reference/SampleFiles/pxe_mapping_file.md).

### Step 4: Enable LDMS in telemetry_config.yml

Configure LDMS and Kafka settings in `telemetry_config.yml`. For details on all parameters, see the [telemetry_config.yml reference](../../Reference/Configuration/telemetry_config.md).

```yaml title="telemetry_config.yml -- LDMS section"
telemetry_sources:
  ldms:
    metrics_enabled: true
    collection_targets:
      - "kafka"

ldms_configurations:
  agg_port: 6001
  store_port: 6001
  sampler_port: 10001
  sampler_plugins:
    - plugin_name: meminfo
      config_parameters: ""
      activation_parameters: "interval=30000000"
    - plugin_name: procstat2
      config_parameters: ""
      activation_parameters: "interval=30000000"
    - plugin_name: vmstat
      config_parameters: ""
      activation_parameters: "interval=30000000"
    - plugin_name: loadavg
      config_parameters: ""
      activation_parameters: "interval=30000000"
    - plugin_name: procnetdev2
      config_parameters: ""
      activation_parameters: "interval=30000000 offset=0"
```

| Parameter | Description |
| --- | --- |
| `metrics_enabled` | Enable or disable LDMS metrics collection (`true` or `false`) |
| `collection_targets` | LDMS data is sent to Kafka. To route to VictoriaMetrics, enable the [Vector-LDMS bridge](#step-5-enable-vector-ldms-bridge-optional) |
| `agg_port` / `store_port` / `sampler_port` | Network ports for LDMS aggregator, store, and sampler |
| `sampler_plugins` | List of LDMS sampler plugins to activate. At least one plugin is mandatory |

!!! note

    For LDMS telemetry configuration, at least one sampler plugin is mandatory to collect system metrics.

### Step 5: Enable Vector-LDMS Bridge (Optional)

To route LDMS metrics from Kafka to VictoriaMetrics, enable the Vector-LDMS bridge in `telemetry_config.yml`. Vector-LDMS consumes from the Kafka `ldms` topic, transforms Avro-encoded LDMS data to Prometheus metric format, and routes to VictoriaMetrics via a dedicated vmagent-vector instance.

For more details on Vector, see [Vector Documentation](https://vector.dev/docs/).

Configure `telemetry_config.yml` to enable Vector-LDMS:

```yaml title="Example: Enable Vector-LDMS"
telemetry_bridges:
  vector_ldms:
    metrics_enabled: true
```

For details on all parameters, see the [telemetry_config.yml reference](../../Reference/Configuration/telemetry_config.md).

The following components are deployed when `vector_ldms > metrics_enabled = true`:

- **vmagent-vector** -- Dedicated vmagent instance for Vector write-buffer. Accepts `prometheus_remote_write` on port 8429, buffers to disk, and forwards to vminsert.
- **Vector-LDMS** -- Kafka consumer pod for LDMS metrics.

!!! note

    Vector-LDMS reuses the existing `kafkapump` KafkaUser for mTLS credentials.

### Step 6: Deploy the Cluster

Deploy the cluster by running the full playbook sequence
(`prepare_oim.yml` -> `local_repo.yml` -> `build_image` -> `provision.yml`). See
[Deploy the Telemetry Stack](deploy_telemetry.md).

During deployment, Omnia:

- Downloads the `ovis-ldms` RPM and telemetry images via `local_repo.yml`.
- Deploys the LDMS aggregator (Helm chart) and Kafka to the service K8s cluster
  (`provision.yml` -> `telemetry.sh`).
- Installs the LDMS sampler on each Slurm node via cloud-init.
- Deploys the Vector-LDMS bridge if enabled in Step 5.

!!! important

    If you enable LDMS or the Vector-LDMS bridge on an already-provisioned cluster,
    re-run `provision.yml` and then execute the `telemetry.sh` script on the K8s
    control plane. See
    [Update Telemetry on a Running Cluster](deploy_telemetry.md#update-telemetry-on-a-running-cluster).

    ```bash title="Run on K8s control plane"
    <K8s_NFS_mount_point>/telemetry/telemetry.sh
    ```


## Verification


### Verify LDMS Telemetry Pods
1. Verify that the LDMS telemetry pods are running:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry
    ```

    ![ldms Telemetry Pods](../../assets/images/ldms_telemetry_pods.png)

### Verify LDMS Messages in Kafka

To verify that LDMS telemetry data is being successfully published to the `ldms` Kafka topic:

1. Log in to the Service Kubernetes control plane.

2. List the telemetry services to identify the `bridge-bridge-lb` external IP:

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry
    ```

    ![Telemetry Services](../../assets/images/telemetry_services_kafka_lb.png)

3. Set the required variables:

    ```bash title="Run on K8s control plane"
    KAFKA_LB_IP=<external IP of bridge-bridge-lb service>
    TOPIC=ldms
    GROUP=ldms-consumer-group
    INSTANCE=ldms-consumer-1
    ```

4. Create a Kafka consumer:

    ```bash title="Run on K8s control plane"
    curl -X POST http://$KAFKA_LB_IP:8080/consumers/ldms-consumer-group \
    -H 'content-type: application/vnd.kafka.v2+json' \
    -d '{
            "name": "ldms-consumer-1",
            "format": "json",
            "auto.offset.reset": "latest",
            "enable.auto.commit": true
        }'
    ```

5. View the list of LDMS Kafka topics configured:

    ```bash title="Run on K8s control plane"
    curl -s -X GET "http://$KAFKA_LB_IP:8080/topics" | jq '.'
    ```

6. Subscribe the consumer to the LDMS topic:

    ```bash title="Run on K8s control plane"
    curl -X POST http://$KAFKA_LB_IP:8080/consumers/ldms-consumer-group/instances/ldms-consumer-1/subscription \
    -H 'content-type: application/vnd.kafka.v2+json' \
    -d '{"topics": ["ldms"]}'
    ```

7. Consume messages from the topic:

    ```bash title="Run on K8s control plane"
    while true; do curl -X GET http://$KAFKA_LB_IP:8080/consumers/ldms-consumer-group/instances/ldms-consumer-1/records \
    -H 'accept: application/vnd.kafka.json.v2+json' | jq '.' ;  sleep 2; done
    ```

If telemetry is flowing correctly, the output contains JSON-formatted LDMS telemetry records.

!!! note

    When new nodes are added, ensure the nodes are up and cloud-init has completed successfully (check `/var/log/cloud-init-output.log` on each node). Then, create a new Kafka consumer group with a unique name (e.g., `ldms-new-nodes-group`) to verify metrics from the newly added nodes. Wait 2-3 minutes after discovery completes before checking.

### Verify TLS Connectivity

1. Run the Kafka TLS test job:

    ```bash title="Run on K8s control plane"
    cd /<nfs client mount path of the service k8s cluster>/telemetry/deployments/test
    kubectl apply -f kafka.tls_test_job.yaml
    ```

2. After the job completes, check the logs to confirm that the TLS connection is successful:

    ```bash title="Run on K8s control plane"
    kubectl logs kafka-tls-test-xxx -n telemetry
    ```

### View LDMS Metrics in VictoriaMetrics UI (VMUI)

LDMS metrics are routed to VictoriaMetrics via the [Vector-LDMS bridge](#step-5-enable-vector-ldms-bridge-optional).

1. Verify that the Vector-LDMS pod is running:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry | grep vector-ldms
    ```

    ![Vector-LDMS Pod](../../assets/images/victoria_metrics_ldms_1.png)

2. Verify that the vmagent-vector pod is running:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry | grep vmagent-vector
    ```

    ![vmagent-vector Pod](../../assets/images/victoria_metrics_ldms_2.png)

3. Verify that the VictoriaMetrics service is running:

    ```bash title="Run on K8s control plane"
    kubectl get service -n telemetry | grep vm
    ```

    ![VictoriaMetrics Service](../../assets/images/victoria_metrics_ldms_3.png)

4. Note the **External IP** and **port number** of the VictoriaMetrics service.

5. Access the VMUI in a web browser:

    ```
    https://<external vmselect loadbalancer IP>:8481/select/0/vmui
    ```

6. Verify that metrics are reaching VictoriaMetrics by querying the VMUI. For example, the following query displays LDMS-related metrics:

    ```
    {__name__=~"ldms_.*"}
    ```

    ![LDMS Metrics in VMUI](../../assets/images/victoria_metrics_ldms_ui_login.png)


## Next Steps


- [Setup Telemetry](setup_telemetry.md) -- Overview of all telemetry sources.


## Troubleshooting

### LDMS metrics missing

???+ note "Symptom"

    LDMS metrics do not appear in the telemetry dashboard or are missing expected data points.

??? note "Cause"

    - LDMS aggregator pods are not running or experiencing errors.
    - LDMS store daemon service is inactive.
    - LDMS sampler service is not functioning correctly.

??? note "Resolution"

    Check the status of LDMS components and review logs for errors:

    ```bash title="Run on: K8s control plane"
    kubectl logs -n telemetry nersc-ldms-aggr-0
    kubectl logs -n telemetry nersc-ldms-store-slurm-cluster-0
    ```

    ```bash title="Run on: compute node"
    sudo systemctl status ldmsd.sampler.service
    ```

    Verify LDMS sampler is collecting metrics:

    ```bash title="Run on: compute node"
    /opt/ovis-ldms/sbin/ldms_ls -h localhost -p 10001 -x sock -a none
    ```

For additional telemetry issues (Kafka, iDRAC, VictoriaMetrics, VictoriaLogs), see [Troubleshooting Telemetry](../../Troubleshooting/telemetry.md).
