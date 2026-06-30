
# LDMS Metrics


This page catalogs the metrics collected by the Lightweight Distributed Metric
Service (LDMS) samplers running on compute nodes. LDMS provides high-frequency,
low-overhead OS-level metrics.

## Collection method


| Property | Value |
| --- | --- |
| **Agent** | LDMS sampler daemon (`ldmsd`) on each compute node |
| **Aggregation** | LDMS aggregator daemon on the telemetry entry node |
| **Default interval** | 10 seconds (configurable via `ldms_sample_interval` in `telemetry_config.yml`) |
| **Kafka topic** | `ldms_telemetry` (configurable via `kafka_topic_ldms`) |
| **Storage** | VictoriaMetrics time-series database |

## meminfo sampler


Collects data from `/proc/meminfo`. Provides memory utilization metrics.

| Metric | Unit | Description |
| --- | --- | --- |
| `ldms_meminfo_MemTotal` | kB | Total physical memory available. |
| `ldms_meminfo_MemFree` | kB | Free memory (not used by any process or cache). |
| `ldms_meminfo_MemAvailable` | kB | Estimated memory available for starting new applications. |
| `ldms_meminfo_Buffers` | kB | Memory used by kernel buffers. |
| `ldms_meminfo_Cached` | kB | Memory used by the page cache (file data). |
| `ldms_meminfo_SwapTotal` | kB | Total swap space. |
| `ldms_meminfo_SwapFree` | kB | Free swap space. |
| `ldms_meminfo_Dirty` | kB | Memory waiting to be written to disk. |
| `ldms_meminfo_Writeback` | kB | Memory actively being written to disk. |
| `ldms_meminfo_AnonPages` | kB | Memory used by anonymous (non-file-backed) pages. |
| `ldms_meminfo_Slab` | kB | In-kernel data structures cache. |
| `ldms_meminfo_HugePages_Total` | Count | Total number of hugepages allocated. |
| `ldms_meminfo_HugePages_Free` | Count | Number of unused hugepages. |

## vmstat sampler


Collects data from `/proc/vmstat`. Provides virtual memory statistics.

| Metric | Unit | Description |
| --- | --- | --- |
| `ldms_vmstat_pgpgin` | Pages | Total pages paged in from disk (cumulative). |
| `ldms_vmstat_pgpgout` | Pages | Total pages paged out to disk (cumulative). |
| `ldms_vmstat_pswpin` | Pages | Pages swapped in (cumulative). |
| `ldms_vmstat_pswpout` | Pages | Pages swapped out (cumulative). |
| `ldms_vmstat_pgfault` | Count | Total page faults (minor + major, cumulative). |
| `ldms_vmstat_pgmajfault` | Count | Major page faults (required disk I/O, cumulative). |
| `ldms_vmstat_oom_kill` | Count | Number of OOM (Out-Of-Memory) kill events. |
| `ldms_vmstat_numa_hit` | Count | Memory allocations satisfied from the preferred NUMA node. |
| `ldms_vmstat_numa_miss` | Count | Memory allocations that fell back to a remote NUMA node. |

## procstat sampler


Collects data from `/proc/stat`. Provides CPU utilization metrics.

| Metric | Unit | Description |
| --- | --- | --- |
| `ldms_procstat_user` | Jiffies | Time spent in user mode (cumulative, per CPU and total). |
| `ldms_procstat_nice` | Jiffies | Time spent in user mode with low priority (nice). |
| `ldms_procstat_system` | Jiffies | Time spent in kernel mode. |
| `ldms_procstat_idle` | Jiffies | Time spent idle. |
| `ldms_procstat_iowait` | Jiffies | Time waiting for I/O to complete. |
| `ldms_procstat_irq` | Jiffies | Time servicing hardware interrupts. |
| `ldms_procstat_softirq` | Jiffies | Time servicing software interrupts. |
| `ldms_procstat_steal` | Jiffies | Time stolen by hypervisor (VM environments). |
| `ldms_procstat_processes` | Count | Number of processes created since boot (cumulative). |
| `ldms_procstat_procs_running` | Count | Number of processes currently in runnable state. |
| `ldms_procstat_procs_blocked` | Count | Number of processes currently blocked on I/O. |
| `ldms_procstat_context_switches` | Count | Total context switches since boot (cumulative). |

## procnetdev sampler


Collects data from `/proc/net/dev`. Provides per-interface network
statistics.

| Metric | Unit | Description |
| --- | --- | --- |
| `ldms_procnetdev_rx_bytes` | Bytes | Total bytes received on the interface (cumulative). |
| `ldms_procnetdev_rx_packets` | Count | Total packets received (cumulative). |
| `ldms_procnetdev_rx_errors` | Count | Total receive errors (cumulative). |
| `ldms_procnetdev_rx_dropped` | Count | Total received packets dropped (cumulative). |
| `ldms_procnetdev_tx_bytes` | Bytes | Total bytes transmitted on the interface (cumulative). |
| `ldms_procnetdev_tx_packets` | Count | Total packets transmitted (cumulative). |
| `ldms_procnetdev_tx_errors` | Count | Total transmit errors (cumulative). |
| `ldms_procnetdev_tx_dropped` | Count | Total transmitted packets dropped (cumulative). |

## Metric labels


All LDMS metrics include the following common labels:

| Label | Description |
| --- | --- |
| `host` | Hostname of the compute node. |
| `component_id` | Unique component identifier assigned by LDMS. |
| `job_id` | Slurm job ID (if job-level tagging is enabled). |
| `interface` | Network interface name (procnetdev metrics only). |
| `cpu` | CPU core number (procstat per-core metrics only). |

!!! info

    - [Telemetry Config](../Configuration/telemetry_config.md) -- LDMS configuration
      parameters.
    - [Idrac Metrics](idrac_metrics.md) -- Hardware-level metrics from iDRAC.
    - [Gpu Metrics](gpu_metrics.md) -- GPU telemetry metrics.
