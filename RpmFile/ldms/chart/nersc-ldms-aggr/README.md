Abstract
----

The LDMS Loftsman/Helm Chart enables horizontal scaling of LDMS daemons by distributing producer nodes across multiple LDMS aggregator and storage daemons.

This ensures that no single daemon is overloaded, helping to prevent data loss.

Specifically, the chart divides the list of nodes to be monitored among several ldmsd aggregator daemons (which collect data from producers) and ldmsd storage daemons (which receive data from aggregators and write to Kafka). 

This balanced distribution maximizes reliability and scalability.

This LDMS orchestration depends on a predefined list of nodes already running ldmsd with sampler plugins, provided as JSON host_map files.

Additionally, the orchestration depends on predefined Kubernetes Secrets for ldmsd communication, supporting both LDMS OVIS and Munge authentication mechanisms.

Optionally, the orchestration can use a predefined Kubernetes Secret from pulling container images from a private registry.

Prerequisites
---

1. Create a config file for your system.

```console
cp ldms_machine_config.dell.json ldms_machine_config.json
```

Key Areas: `sys_opts`, `node_types`, and `stream`

```
sys_opts: 
  system                  dell|csm, used in the Makefile to choose script that generates the host map file
  namespace               namespace to deploy into
  imagePullSecretsOption  If your container images are in a private repo, specify k8s Secret with creds to pull

node_types:               List of dict, for each node type with variables used to generate the config files

stream:                   Specific auth for the stream pod. it listens to all Aggregator pods
```

2. Create k8s Secrets for each ldmsd node type and add to the ldms_machine_config.json (in sections auth_type, auth_secret, and auth_secret_file).

3. If needed create a k8s Secrets allowing the pods to pull the image from the image registry, and add to the ldms_machine_config.json in imagePullSecretsOption).

4. Create a scripts to generate the host_map files.

* On a csm system, make_host_map.csm.py will discover nodes using the Shasta Hardware State Manager (HSM) and System Layout Service (SLS).

* On a Dell system, make_host_map.dell.py just copies a manually created file, until we have a better solution.

5. Run Make

```console
1. Creates out_dir
2. Runs script to create host_map files
3. Runs scripts to create ldmsd files, and bundles them into a Config Map
4. Scales the Statefulset 

For csm: make_host_map.csm.py:
1. Discover all nodes using the Shasta Hardware State Manager (HSM) and System Layout Service (SLS).
2. Group the nodes by Type (HPE EX Shasta Application, Compute, and Worker), then by sub-type (GPU, CPU), and finally by node count.
3. Write to out_dir/host_map.json

For dell: make_host_map.dell.py:
1. Copy host_map.r7525.json to out_dir/host_map.json

Create ldms config and prepare chart (nersc_ldms_make_ldms_config.py)
1. Create `ldmsd` config and environment variable files for each `ldmsd` to distribute the producers across daemons and enable daemons to find each other.
2. Create ConfigMaps, which bundle the config and environment files, along with supporting scripts, into mountable Kubernetes objects.
3. Scale the aggregator StatefulSets to the appropriate number of `ldmsd` instances to service all producers.
4. Scale the storage StatefulSets to match the number of `ldmsd` instances needed to service all aggregators and distribute writes to Kafka.
5. Scale StatefulSets and ServiceMonitors for Prometheus node exporters to expose `ldmsd` internal metrics from each daemon.
6. Create an LDMS Streams container that aggregates profiling data about computational jobs and persists it for analysis.
```

Horizontal Scaling
---

* The volume of metrics from all producers is too high for a single `ldmsd` aggregator and storage daemon, and `ldmsd` does not auto-scale, and the storage plugin does not benefit from more threads.

* This set of scripts and Helm charts distributes the collection of metrics across several aggregator and storage daemons to prevent metric loss.

* Each Aggregator daemons is given a subset of the nodes.

* Each storage daemon is assigned a specific Aggregator plus a subset of the nodes on that Aggregator.

* A single stream daemon can collect all stream data from the aggregator daemons.

```
# Basic Fanout strategy
nodes
 |--> Agg
 |     |---> Store -> Kafka
 |     |---> Store -> Kafka
 |     `---> Store -> Kafka
 `--> Agg
       |---> Store -> Kafka
       |---> Store -> Kafka
       `---> Store -> Kafka
```

Observability
---

`ldmsd` offers an API for querying internal metrics, including memory usage, processing time, etc.

A Prometheus-style node exporter allows metrics to be scraped and stored in VictoriaMetrics for visualization in Grafana.

This Helm chart includes a metric exporter, which connects to each aggregator and storage daemon, reads internal metrics via the API, and exposes them as Prometheus metrics.

The `ServiceMonitor` advertises the `Service` attached to each node exporter `Pod`, allowing vmagent (VictoriaMetrics Agent, running in Kubernetes) to locate the metrics, and set the scraping frequency.

The Grafan Dashboard Sections:
* Metric Rates Fidelity
  * Sample rate (metric_set/minute) Application, GPU, and CPU Nodes
* LDMS Producer Host Count
  * Node Counts:  Application, Compute, Management Nodes
* LDMSD Metrics
  * Memory usage, Producer State, Metric Rate
* Kubernetes Pod Metrics
  * CPU, Memory, Network for Aggregators, Storage, and Stram Pods
* Kafka Topic: ldms_nersc
  * messages-in/sec, messages-out/sec, consumer-lag
* LDMS Streams
  * console logs showing ldms stream json data
* LDMSD damon logs
  * Connection error count rate
  * Inconsistent error count rate
  * Outstanding updae count rate
  * Oversampling count rate


Kubernetes Objects:
---

StatefulSets create Pods:

```
nersc-ldms-aggr               -> All aggregators daemons in one pod (potentially using multus IPVLAN) to Nodes
nersc-ldms-store              -> Scaled per node_type (in ldms_machine_config.json), read from aggr and write to kafka
nersc-ldms-exporter           -> One pod per ldmsd, read from each dameon, and expose metircs as prometheus exporter 
nersc-ldms-stream             -> One pod, reads from all aggregators daemins (potentially using multus IPVLAN) for extenral access.
```

Service:

```
nersc-ldms-aggr               -> Expose hostname and ports for aggregator daemons
nersc-ldms-store              -> Expose hostname and ports for storage daemons
nersc-ldms-exporter           -> Expose hostname and ports for exporters daemons
nersc-ldms-stream             -> Expose hostname and ports for stream pod
```

ServiceMonitor:

```
nersc-ldms-exporter           -> Signal vmagent to scrape the exporters
```

NetworkAttachmentDefinition:

```
ipvlan-ldms-agg-hsn           -> Multus IpVlan expose Aggregator pod to nodes over HSN interface
ipvlan-ldms-agg-cmn           -> Multus IpVlan expose Steam pod to external host, over CMN interface
```

ConfigMap

```
nersc-ldms-bin                -> Generated script bundle, mounted in pods, to run ldmsd and checking health
nersc-ldms-conf               -> Generated config and environment files, mounted in pods, to run ldmsd and checking health
```

Secrets

```
None provided, but this relies on an externally provided Munge key secret for authentication, mounted in each pod.
```

Build, Deploy, and Test
---

`make` runs the following scripts: `nersc_ldms_init.py`  `mkmanifest.py`, and copies `ConfigMaps` into the Helm chart template directory.

```
make
```

Helm Lint Test: Watch for failed render

```
helm template --debug ls nersc-ldms-aggr
# -or-                                                                          
helm template --debug  --values values.yaml nersc-ldms-aggr                   
```

Deploy:

```
cd .. && ./deploy.py -c nersc-ldms_aggr
# -or-                                                                          
helm install -n telem nersc-ldms-aggr nersc-ldms-aggr --values values.yaml    
```

Watch Deployment: wait until all nodes are complete 1/1 or more for the nersc-ldms-aggr

```
kubectl -n sma get pods -w |grep ldms
```

Test:

Once deployed and running, you can view the resource usage:

```
kubectl -n sma top pods --containers |grep ldms
```

Once deployed and running, you can exec into a specific container and talk to ldmsd

```
# Aggregators all run in the same pod, so specify the container name
kubectl -n sma top pods --containers nersc-ldms-aggr-0
POD                 NAME         CPU(cores)   MEMORY(bytes)
nersc-ldms-aggr-0   comp-gpu-2   242m         154Mi
nersc-ldms-aggr-0   comp-gpu-0   256m         169Mi
nersc-ldms-aggr-0   appl         52m          49Mi
nersc-ldms-aggr-0   comp-cpu-2   213m         341Mi
nersc-ldms-aggr-0   comp-gpu-1   237m         149Mi
nersc-ldms-aggr-0   comp-cpu-1   272m         219Mi
nersc-ldms-aggr-0   mana         43m          29Mi
nersc-ldms-aggr-0   comp-gpu-3   199m         198Mi
nersc-ldms-aggr-0   comp-cpu-0   268m         243Mi

# Get a shell on Agg
kubectl -n sma exec -it nersc-ldms-aggr-0 -c comp-cpu-1 -- /bin/bash
# Source the env
source /ldms_conf/ldms-env.nersc-ldms-aggr.compute-cpu-1.sh
# Now talk to the daemon
/ldms_bin/ldms_ls.bash
/ldms_bin/ldms_stats.bash

# Get shell on Store
kubectl -n sma exec -it nersc-ldms-store-compute-cpu-1 -- /bin/bash
# Source the env
source /ldms_conf/ldms-env.${MY_POD_NAME}.sh
# Now talk to the daemon
/ldms_bin/ldms_ls.bash
/ldms_bin/ldms_stats.bash


# Quick round trip
helm -n telem delete nersc-ldms-aggr
make clean
make
helm install -n telem nersc-ldms-aggr nersc-ldms-aggr --values values.yaml

# Let it startup
kubectl  -n telem top pods --containers |grep ldms
nersc-ldms-aggr-0                           r7525-0                    2m           16Mi            
nersc-ldms-exporter-0                       exporter                   1m           27Mi            
nersc-ldms-exporter-1                       exporter                   1m           24Mi            
nersc-ldms-exporter-2                       exporter                   1m           24Mi            
nersc-ldms-store-r7525-0                    store                      2m           10Mi            
nersc-ldms-stream-0                         stream                     1m           13Mi  

```


Unintall
---

```
helm -n sma delete nersc-ldms-aggr
```

Container
---

The container image used by all the pods is built from the oci dir in this repo, which contains directions.

After building a new image infomraiton in update the manifest.yaml.in

TODO:
---

* Abstract constants used for splitting nodes, into variables
* Write units for nersc_ldms_init.py
* Make a test harness that runs a new k8s cluster and deploys
  - deploy
  - perform actions, state, api functional
  - do kubectl commands to interact with services api
  - make fake sls and hsm



