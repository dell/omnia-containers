# Get Started

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Omnia deployment flow</title>
<style>
  :root {
    --bg: #ffffff;
    --text: #1a1a1a;
    --text-secondary: #5f5e5a;
    --border: #d3d1c7;
    --neutral-fill: #DAEEF9;
    --neutral-stroke: #5B9BD5;
    --neutral-text: #1B3B5F;
    --decision-fill: #1F6FB2;
    --decision-stroke: #14507F;
    --retry-fill: #FCE4D6;
    --retry-stroke: #E8843C;
    --retry-text: #C15F1E;
    --arrow: #E8843C;
    --arrow-fail: #C0392B;
  }
  @media (prefers-color-scheme: dark) {
    :root { --bg: #1a1a18; --text: #e8e6dd; --text-secondary: #b4b2a9; --border: #444441; }
  }
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg); color: var(--text);
    margin: 0; padding: 32px 16px 64px;
  }
  .wrap { max-width: 700px; margin: 0 auto; }
  h1 { font-size: 19px; font-weight: 600; margin: 0 0 4px; }
  .sub { font-size: 12.5px; color: var(--text-secondary); margin: 0 0 20px; }
  .legend { display: flex; gap: 14px; flex-wrap: wrap; font-size: 11.5px; color: var(--text-secondary); margin: 0 0 26px; }
  .legend span { display: inline-flex; align-items: center; gap: 5px; }
  .swatch { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
  .diamond-swatch { width: 12px; height: 12px; background: var(--decision-fill); transform: rotate(45deg); display:inline-block; }

  .flow { display: flex; flex-direction: column; align-items: center; }

  .node {
    width: 230px;
    padding: 10px 14px;
    border-radius: 8px;
    text-align: center;
    font-size: 12.5px;
    line-height: 1.35;
  }
  .node.neutral { background: var(--neutral-fill); border: 1px solid var(--neutral-stroke); color: var(--neutral-text); }
  .node.terminal { background: var(--decision-fill); border: 1px solid var(--decision-stroke); color: #fff; font-weight: 600; border-radius: 999px; width: auto; max-width: 230px; padding: 10px 20px; }
  .node.retry { background: var(--retry-fill); border: 1px solid var(--retry-stroke); color: var(--retry-text); }
  .node code { font-size: 11.5px; }

  .diamond {
    width: 150px;
    height: 100px;
    clip-path: polygon(50% 0, 100% 50%, 50% 100%, 0 50%);
    background: var(--decision-fill);
    color: #fff;
    font-weight: 600;
    font-size: 12px;
    line-height: 1.3;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 0 28px;
  }

  .arrow {
    width: 2px; height: 18px; background: var(--arrow); position: relative;
  }
  .arrow::after {
    content: ""; position: absolute; bottom: -1px; left: 50%; transform: translateX(-50%);
    border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid var(--arrow);
  }
  .arrow.fail { background: var(--arrow-fail); }
  .arrow.fail::after { border-top-color: var(--arrow-fail); }

  .row { display: flex; gap: 12px; }

  /* ---- generic line utilities (solid vs dotted) ---- */
  .line-v { width: 2px; margin: 0 auto; }
  .line-v.state-solid { background: var(--arrow); }
  .line-v.state-dotted { background: repeating-linear-gradient(to bottom, var(--text-secondary) 0 4px, transparent 4px 8px); }
  .line-h { height: 2px; }
  .line-h.state-solid { background: var(--arrow); }
  .line-h.state-dotted { background: repeating-linear-gradient(to right, var(--text-secondary) 0 4px, transparent 4px 8px); }

  .final-connector { width: 2px; height: 18px; margin: 0 auto; position: relative; }
  .final-connector.state-solid { background: var(--arrow); }
  .final-connector.state-solid::after {
    content: ""; position: absolute; bottom: -1px; left: 50%; transform: translateX(-50%);
    border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid var(--arrow);
  }
  .final-connector.state-dotted { background: repeating-linear-gradient(to bottom, var(--text-secondary) 0 4px, transparent 4px 8px); }

  /* ---- Two-column fork (from a diamond, Yes/No both shown, no click) ---- */
  .fork-wrap { position: relative; padding-top: 16px; }
  .fork-wrap::before {
    content: ""; position: absolute; top: 0; left: 50%; width: 2px; height: 16px;
    background: var(--arrow); transform: translateX(-50%);
  }
  .fork-wrap.fail-top::before { background: var(--arrow-fail); }
  .fork-bar { position: absolute; top: 16px; left: calc(50% - 135px); width: 270px; height: 2px; background: var(--arrow); }
  .fork-bar.fail-bar { background: var(--arrow-fail); }
  .fork { display: flex; gap: 40px; justify-content: center; width: 100%; }
  .fork-col { width: 230px; display: flex; flex-direction: column; align-items: center; position: relative; padding-top: 16px; }
  .fork-col::before {
    content: ""; position: absolute; top: 0; left: 50%; width: 2px; height: 16px;
    background: var(--arrow); transform: translateX(-50%);
  }
  .fork-col.fail-col::before { background: var(--arrow-fail); }
  .branch-tag {
    font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3px;
    padding: 2px 9px; border-radius: 8px; margin-bottom: 8px;
    background: var(--bg); border: 1.5px solid var(--arrow); color: var(--arrow);
  }
  .branch-tag.fail-tag { border-color: var(--arrow-fail); color: var(--arrow-fail); }
  .empty-note { font-size: 11px; color: var(--text-secondary); font-style: italic; padding: 4px 0; }
  .loop-note {
    font-size: 10.5px; color: var(--retry-text); font-style: italic; text-align: center;
    padding: 6px 10px; border: 1px dashed var(--retry-stroke); border-radius: 8px; background: var(--retry-fill);
  }

  /* ---- Merge (reverse fork): both columns always converge, always solid, no interactivity ---- */
  .col-spacer { flex: 1 1 auto; }
  .col-stem { width: 2px; height: 16px; background: var(--arrow); }
  .fork-col.fail-col .col-stem { background: var(--arrow-fail); }
  .merge-bar-wrap { position: relative; width: 100%; }
  .merge-bar-wrap .merge-bar {
    position: absolute; bottom: 0; left: calc(50% - 135px); width: 270px; height: 2px; background: var(--arrow);
  }

  /* ---- Top-level Start -> Manual/BuildStream selector fork (clickable) ---- */
  .top-fork-wrap { position: relative; padding-top: 18px; width: 100%; }
  .top-fork-wrap::before {
    content: ""; position: absolute; top: 0; left: 50%; width: 2px; height: 18px;
    background: var(--arrow); transform: translateX(-50%);
  }
  .top-fork-bar { position: absolute; top: 18px; left: calc(50% - 120px); width: 240px; height: 2px; background: var(--arrow); }
  .top-fork { display: flex; gap: 40px; justify-content: center; width: 100%; }
  .top-fork-col { width: 200px; display: flex; flex-direction: column; align-items: center; position: relative; padding-top: 18px; }
  .top-fork-col::before {
    content: ""; position: absolute; top: 0; left: 50%; width: 2px; height: 18px;
    background: var(--arrow); transform: translateX(-50%);
  }
  .select-btn {
    width: 100%; padding: 11px 10px; border-radius: 8px; cursor: pointer;
    background: var(--bg); border: 2px solid var(--neutral-stroke); color: var(--neutral-text);
    font-size: 13px; font-weight: 600; text-align: center; transition: background 0.15s, color 0.15s;
  }
  .select-btn:hover:not(.active) { background: var(--neutral-fill); }
  .select-btn.active { background: var(--decision-fill); border-color: var(--decision-stroke); color: #fff; }

  .conn-stem { height: 16px; margin-top: 10px; }
  .merge-row-top { display: flex; justify-content: center; width: 100%; }
  .half-line { width: 120px; }

  .placeholder { font-size: 12px; color: var(--text-secondary); font-style: italic; padding: 10px 0 2px; text-align: center; }

  .branch-body {
    display: flex; flex-direction: column; align-items: center;
    overflow: hidden; max-height: 0; opacity: 0; width: 100%;
    transition: max-height 0.35s ease, opacity 0.25s ease;
  }
  .branch-body.open { max-height: 3000px; opacity: 1; }

  .divider { height: 1px; background: var(--border); width: 100%; max-width: 460px; margin: 22px 0 14px; }
</style>
</head>
<body>
<div class="wrap">
  <h1>Omnia deployment flow</h1>
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
          <div class="select-btn" id="btn-manual" onclick="selectPath('manual')">Manual Deployment</div>
          <div class="conn-stem line-v state-dotted" id="stem-manual"></div>
        </div>
        <div class="top-fork-col">
          <div class="select-btn" id="btn-buildstream" onclick="selectPath('buildstream')">BuildStream</div>
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

<script>
  function setState(el, solid) {
    el.classList.toggle('state-solid', solid);
    el.classList.toggle('state-dotted', !solid);
  }
  function selectPath(choice) {
    document.getElementById('btn-manual').classList.toggle('active', choice === 'manual');
    document.getElementById('btn-buildstream').classList.toggle('active', choice === 'buildstream');
    document.getElementById('branch-manual').classList.toggle('open', choice === 'manual');
    document.getElementById('branch-buildstream').classList.toggle('open', choice === 'buildstream');
    setState(document.getElementById('stem-manual'), choice === 'manual');
    setState(document.getElementById('stem-buildstream'), choice === 'buildstream');
    setState(document.getElementById('half-manual'), choice === 'manual');
    setState(document.getElementById('half-buildstream'), choice === 'buildstream');
    setState(document.getElementById('final-connector'), true);
    document.getElementById('placeholder').style.display = 'none';
  }
</script>
</body>
</html>

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
