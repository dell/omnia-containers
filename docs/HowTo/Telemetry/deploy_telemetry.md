# Deploy the Telemetry Stack

## Overview

The telemetry domain deploys and manages a comprehensive telemetry stack for HPC and AI clusters. It collects metrics and logs from multiple sources (iDRAC, LDMS, OME, UFM, PowerScale, VAST, SFM) and stores them in sink backends (Kafka, VictoriaMetrics, VictoriaLogs). Telemetry runs as Kubernetes workloads on the kube_vip cluster.

### When to Use This Page

- **First-time deployment** -- You are deploying the telemetry stack for the first time
- **Re-deployment** -- You are re-deploying telemetry after configuration changes

## Prerequisites

- The [Setup the OIM](../main/setup_oim.md) procedure is complete (main domain setup is complete)
- The [Initialize Domains](../main/initialize_domains.md) procedure is complete (telemetry domain is initialized)
- The [Deploy Kubernetes](../orchestrator/deploy_kubernetes.md) procedure is complete (kube_vip cluster is running)
- The telemetry source you want has been configured. See the per-source guides under [Telemetry Setup](setup_telemetry.md)

## Procedure

Run the telemetry domain deployment using omnia.sh CLI.

### Step 1: Initialize the telemetry domain

```bash title="Run on: OIM host"
./omnia.sh -i telemetry
```

This stages input files and installs dependencies.

### Step 2: Configure telemetry settings

```bash title="Run on: OIM host"
vi /opt/omnia/telemetry/input/project_default/telemetry_config.yml
```

Configure the telemetry sources, sinks, and bridges as needed.

### Step 3: Deploy the telemetry stack

```bash title="Run on: OIM host"
./omnia.sh --run telemetry --tags deploy
```

This performs the following:
- Validates K8s prerequisites (kube_vip, nodes, pods)
- Validates telemetry configuration files
- Deploys sink infrastructure (Kafka, VictoriaMetrics, VictoriaLogs)
- Deploys enabled source components (iDRAC, LDMS, OME, UFM, PowerScale, VAST, SFM)
- Generates and applies Kubernetes manifests via kustomize

### Update Telemetry on a Running Cluster

If the cluster is already provisioned and you want to enable or reconfigure a telemetry source:

1. Update `telemetry_config.yml`
2. Re-run the telemetry deployment:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run telemetry --tags deploy
    ```

## Verification

Verify that the input files were successfully processed and the telemetry stack is operational.

```bash title="Run on: service_kube_control_plane node"
kubectl get pods -n telemetry -o wide
```

All pods should show `Running` status. Use the component-specific verification pages listed in Next Steps to confirm each enabled telemetry source is collecting data.

## Next Steps

After deployment, verify that each enabled telemetry source is collecting data. Each component has its own verification page:

- [Verify iDRAC Telemetry](verify_idrac.md)
- [Verify LDMS Telemetry](verify_ldms.md)
- [Verify PowerScale Telemetry](verify_powerscale.md)
- [Verify UFM Telemetry](verify_ufm.md)
- [Verify VAST Telemetry](verify_vast.md)
- [Verify OME Telemetry](verify_ome.md)
- [Verify Vector-LDMS Bridge](verify_vector_ldms.md)

## Troubleshooting

[Telemetry Troubleshooting](../../Troubleshooting/telemetry.md)




















