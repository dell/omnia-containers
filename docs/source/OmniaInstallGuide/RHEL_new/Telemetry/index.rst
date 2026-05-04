Step 8: Configure Telemetry Requirements
========================================

Omnia enables telemetry collection using both iDRAC Telemetry and LDMS
(Lightweight Distributed Metric Service) in HPC environments. This design ensures that
telemetry components are dynamically provisioned with stateless provisioning tool, 
providing flexible deployment and simplified lifecycle management.

* **iDRAC Telemetry** provides out-of-band system metrics from Dell servers, including
  power, thermal, and hardware health information. The iDRAC Telemetry data can be collected
  and streamed to **Kafka** or **VictoriaMetrics**, depending on the deployment needs. When **VictoriaMetrics** is selected,
  **VictoriaLogs** is deployed alongside it for centralized log management.

* **LDMS Telemetry** collects in-band performance metrics such as CPU, memory,
  network, and I/O statistics from compute nodes. The LDMS Telemetry data can be collected
  and streamed to **Kafka**.

* **PowerScale Telemetry** collects storage performance metrics and logs from PowerScale storage nodes. The PowerScale Telemetry data and logs can be collected and streamed to **VictoriaMetrics** and **VictoriaLogs**, respectively.



.. note::

   Ensure that the ``service_k8s`` entry is mentioned in the ``software_config.json`` file when ``idrac_telemetry_support`` is set to ``true`` in the ``telemetry_config.yml`` file.


Omnia Telemetry Architecture
-----------------------------

Omnia collects telemetry data from HPC cluster nodes using: **LDMS** for OS-level metrics and **iDRAC** for hardware telemetry.

The following diagram illustrates the telemetry services that can be deployed using Omnia and the data flow between the components.

.. image:: ../../../images/omnia_telemetry_architecture.png

  
Telemetry Components
---------------------

The following components are involved in the telmetry services deployed by Omnia:

**OIM (Omnia Infrastructure Manager)**

Central management node that deploys and configures all telemetry services across the cluster.

**Service Kubernetes Cluster**

Hosts telemetry collection and storage services:

- **LDMS Aggregator** – Receives metrics from slurm compute node samplers.
- **LDMS Store** – Stores aggregated LDMS data
- **iDRAC Collector** – Collects hardware telemetry via Redfish API
- **Kafka Broker** – Streams telemetry data
- **VMAgent** – Forwards metrics to Victoria Metrics
- **Victoria Metrics** – Time-series database for metric storage
- **VictoriaLogs Cluster** – Distributed log storage system with vlstorage, vlinsert, vlselect components
- **VLAgent** – Platform-managed log collection agent that receives logs from external sources


**Slurm Cluster**

Each slurm compute node runs:

- **LDMS Sampler** – Collects OS metrics (CPU, memory, network, and I/O)
- **iDRAC** – Provides hardware health data (temperature, power, and fans)

iDRAC and LDMS Telemetry Data Flows
------------------------------------

**LDMS Flow (OS Metrics)**

::

   Slurm Compute Nodes (LDMS Sampler) → LDMS Aggregator → LDMS Store → Kafka

**iDRAC Flow (Hardware Metrics)**

::

   iDRAC (BMC) → iDRAC Collector → Kafka
   iDRAC (BMC) → iDRAC Collector → VMAgent → Victoria Metrics
   iDRAC (BMC) → iDRAC Collector → VLAgent → Victoria Logs

PowerScale Telemetry Data Flows
------------------------------------

::

   PowerScale Nodes → csm-metrics → otel-collector → vmagent → Victoria Metrics
   PowerScale Nodes → csm-metrics → otel-collector → vlagent → Victoria Logs


.. toctree::
    :maxdepth: 2

    service_cluster_telemetry
    ldms_telemetry
    power_scale_telemetry
