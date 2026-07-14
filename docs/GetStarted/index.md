# Get Started

## Omnia deployment flow

<div class="flow-container">
<div class="wrap">
  <p class="sub">Pick a path to expand its steps. Yes/No branches inside a path are shown in full.</p>
  <div class="legend">
    <span><i class="swatch" style="background:var(--neutral-fill);border:1px solid var(--neutral-stroke)"></i>Step</span>
    <span><i class="diamond-swatch"></i>Decision</span>
    <span><i class="swatch" style="background:var(--retry-fill);border:1px solid var(--retry-stroke)"></i>Retry</span>
  </div>

  <div class="flow">
    <div class="node terminal">Start Omnia Deployment</div>

    <div class="top-fork-wrap">
      <div class="top-fork-bar"></div>
      <div class="top-fork">
        <div class="top-fork-col">
          <div class="select-btn" id="btn-manual" onclick="window.selectPath('manual')">Manual Deployment</div>
          <div class="conn-stem line-v state-dotted" id="stem-manual"></div>
        </div>
        <div class="top-fork-col">
          <div class="select-btn" id="btn-buildstream" onclick="window.selectPath('buildstream')">BuildStream</div>
          <div class="conn-stem line-v state-dotted" id="stem-buildstream"></div>
        </div>
      </div>
    </div>
    <div class="merge-row-top">
      <div class="half-line line-h state-dotted" id="half-manual"></div>
      <div class="half-line line-h state-dotted" id="half-buildstream"></div>
    </div>
    <div class="final-connector state-dotted" id="final-connector"></div>

    <div class="placeholder" id="placeholder">Select a path above</div>

    <!-- ===================== MANUAL PATH ===================== -->
    <div class="branch-body" id="branch-manual">
      <div class="node neutral">Build Omnia Images</div>
      <div class="arrow"></div>
      <div class="node neutral">Create the Omnia Core Container</div>
      <div class="arrow"></div>
      <div class="node neutral">Update Input Files</div>
      <div class="arrow"></div>

      <div class="diamond">Discover Devices<br/>Using OME?</div>
      <div class="fork-wrap">
        <div class="fork-bar"></div>
        <div class="merge-bar-wrap">
          <div class="merge-bar"></div>
          <div class="fork">
            <div class="fork-col">
              <div class="branch-tag">No</div>
              <div class="node neutral">Create PXE mapping file manually</div>
              <div class="col-spacer"></div>
              <div class="col-stem"></div>
            </div>
            <div class="fork-col">
              <div class="branch-tag">Yes</div>
              <div class="node neutral">Generate PXE mapping file via OME-based BMC discovery</div>
              <div class="col-spacer"></div>
              <div class="col-stem"></div>
            </div>
          </div>
        </div>
      </div>
      <div class="arrow"></div>
      <div class="node neutral">Run Input Validator</div>
      <div class="arrow"></div>
      <div class="node neutral">Deploy Container on OIM</div>
      <div class="arrow"></div>
      <div class="node neutral">Download Packages to Pulp Repo</div>
      <div class="arrow"></div>
      <div class="node neutral">Build Images</div>
      <div class="arrow"></div>

      <div class="diamond">aarch64<br/>Required?</div>
      <div class="fork-wrap">
        <div class="fork-bar"></div>
        <div class="merge-bar-wrap">
          <div class="merge-bar"></div>
          <div class="fork">
            <div class="fork-col">
              <div class="branch-tag">No</div>
              <div class="arrow-continue"></div>
              <div class="col-spacer"></div>
              <div class="col-stem"></div>
            </div>
            <div class="fork-col">
              <div class="branch-tag">Yes</div>
              <div class="node neutral">Install RHEL10 diskfull OS on aarch64 node</div>
              <div class="arrow"></div>
              <div class="node neutral">Run <code>build_image_aarch64.yml</code></div>
              <div class="col-spacer"></div>
              <div class="col-stem"></div>
            </div>
            <div class="fork-col">
            </div>
          </div>
        </div>
      </div>
      <div class="arrow"></div>
      <div class="node neutral">Provision the Nodes</div>
      <div class="arrow"></div>
      <div class="node neutral">PXE Boot Nodes to Load Images</div>
      <div class="arrow"></div>
      <div class="node neutral">Enable Telemetry</div>
      <div class="arrow"></div>
      <div class="node terminal">End of Deployment</div>
    </div>

    <!-- ===================== BUILDSTREAM PATH ===================== -->
    <div class="branch-body" id="branch-buildstream">
      <div class="node neutral">Build Omnia Images</div>
      <div class="arrow"></div>
      <div class="node neutral">Create the Omnia Core Container</div>
      <div class="arrow"></div>
      <div class="node neutral">Update Input Files</div>
      <div class="arrow"></div>

      <div class="diamond">Discover Devices<br/>Using OME?</div>
      <div class="fork-wrap">
        <div class="fork-bar"></div>
        <div class="merge-bar-wrap">
          <div class="merge-bar"></div>
          <div class="fork">
            <div class="fork-col">
              <div class="branch-tag">No</div>
              <div class="node neutral">Create PXE mapping file manually</div>
              <div class="col-spacer"></div>
              <div class="col-stem"></div>
            </div>
            <div class="fork-col">
              <div class="branch-tag">Yes</div>
              <div class="node neutral">Generate PXE mapping file via OME-based BMC discovery</div>
              <div class="col-spacer"></div>
              <div class="col-stem"></div>
            </div>
          </div>
        </div>
      </div>
      <div class="arrow"></div>
      <div class="node neutral">Run Input Validator</div>
      <div class="arrow"></div>

      <div class="diamond">aarch64<br/>Required?</div>
      <div class="fork-wrap">
        <div class="fork-bar"></div>
        <div class="merge-bar-wrap">
          <div class="merge-bar"></div>
          <div class="fork">
            <div class="fork-col">
              <div class="branch-tag">No</div>
              <div class="arrow-continue"></div>
              <div class="col-spacer"></div>
              <div class="col-stem"></div>
            </div>
            <div class="fork-col">
              <div class="branch-tag">Yes</div>
              <div class="node neutral">Install RHEL10 diskfull OS on aarch64 node</div>
              <div class="col-spacer"></div>
              <div class="col-stem"></div>
            </div>
          </div>
        </div>
      </div>
      <div class="arrow"></div>
      <div class="node neutral">Deploy BuildStreaM Container on OIM</div>
      <div class="arrow"></div>
      <div class="node neutral">Deploy BuildStreaM GitLab Instance</div>
      <div class="arrow"></div>
      <div class="node neutral">Update Catalog File</div>
      <div class="arrow"></div>

      <div class="node neutral">Build Pipeline</div>
      <div class="arrow"></div>
      <div class="node neutral">Modify PXE Mapping</div>
      <div class="arrow"></div>
      <div class="node neutral">Deploy Pipeline</div>
      <div class="arrow"></div>
      <div class="node neutral">Enable Telemetry</div>
      <div class="arrow"></div>
      <div class="node terminal">End of Deployment</div>
    </div>
  </div>
</div>


</div>
</div>

Choose your deployment path based on your cluster requirements, available
hardware, and desired workload. Each path is a self-contained, end-to-end
tutorial that takes you from a bare set of PowerEdge servers to a fully
operational cluster.

!!! note

    Before selecting a path, complete the [Prerequisites Checklist](prerequisites_checklist.md) to
    ensure your hardware, networking, and software environment are ready.

## Deployment Paths at a Glance


| Path | Name | Workload | Nodes | Time | Description |
| --- | --- | --- | --- | --- | --- |
| **A** | [Slurm Quickstart](slurm_quickstart.md) | Traditional HPC (Slurm) | 4+ | ~2 hrs | Overview page with links to detailed Slurm deployment guides. Covers Slurm setup, GPU provisioning, node management, configuration backup, and HPC benchmarks. Ideal for first-time users and large-scale HPC workloads. |
| **B** | [K8S Telemetry Only](k8s_telemetry_only.md) | Kubernetes + Telemetry (no Slurm) | 5 | ~2 hrs | Deploys a 3-control-plane + 1-worker Kubernetes cluster with the complete telemetry pipeline (iDRAC metrics, LDMS, Kafka, VictoriaMetrics, Grafana). No Slurm. Use this when you need infrastructure monitoring without a job scheduler. |
| **C** | [Full Deployment](full_deployment.md) | Slurm + Service K8s + Telemetry | 8 | ~4 hrs | Production-grade deployment with Slurm scheduling, a highly available 3-node Kubernetes service cluster, LDAP/FreeIPA authentication, and full telemetry (iDRAC, Grafana, VictoriaMetrics). Best for teams running mixed HPC/AI workloads with monitoring requirements. |
| **D** | [Buildstream Deployment](buildstream_deployment.md) | BuildStreaM (Catalog-Driven CI/CD) | 8+ | ~6 hrs | Automated, catalog-driven deployment using GitLab CI/CD pipelines. BuildStreaM reads a declarative catalog to provision and configure the entire cluster. Best for organizations with GitOps workflows or repeated, reproducible deployments at scale. |

## Which Path Should I Choose?


**"I just want Slurm running as fast as possible."**
    Start with [Slurm Quickstart](slurm_quickstart.md) (Path A). You can always add
    Kubernetes and telemetry later.

**"I only need telemetry dashboards -- no job scheduler."**
    Choose [K8S Telemetry Only](k8s_telemetry_only.md) (Path B). This gives you
    iDRAC-to-Grafana visibility without the overhead of Slurm.

**"I need a production cluster with monitoring and authentication."**
    Go with [Full Deployment](full_deployment.md) (Path C). This is the canonical Omnia
    deployment that exercises every major subsystem.

**"I want CI/CD-driven, repeatable infrastructure."**
    Use [Buildstream Deployment](buildstream_deployment.md) (Path D). BuildStreaM automates the
    entire lifecycle through GitLab pipelines and a declarative catalog.

## Before You Begin


Every path assumes you have completed the items in
[Prerequisites Checklist](prerequisites_checklist.md). That page covers:

- Supported hardware and firmware versions
- OIM (management node) requirements (RAM, OS, Podman, NICs)
- Network switch configuration (admin + BMC VLANs)
- NFS / storage preparation
- BIOS and iDRAC settings on target nodes
- Required RHEL subscriptions and Docker credentials

!!! tip

    Print or bookmark the [Prerequisites Checklist](prerequisites_checklist.md) -- it doubles as a
    day-of-deployment runbook you can hand to a datacenter technician.
