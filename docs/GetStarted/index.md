# Get Started

<div class="omnia-flowchart">
<style>
  :root {
    --bg: #ffffff;
    --text: #1a1a1a;
    --text-secondary: #5f5e5a;
    --card-bg: #fafaf8;
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
    :root {
      --bg: #1a1a18;
      --text: #e8e6dd;
      --text-secondary: #b4b2a9;
      --card-bg: #242422;
      --border: #444441;
    }
  }
  .omnia-flowchart { font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 32px 16px 64px; }
  .omnia-flowchart * { box-sizing: border-box; }
  .wrap { max-width: 720px; margin: 0 auto; }
  h1 { font-size: 20px; font-weight: 600; margin: 0 0 4px; }
  .sub { font-size: 13px; color: var(--text-secondary); margin: 0 0 20px; }
  .legend { display: flex; gap: 16px; flex-wrap: wrap; font-size: 12px; color: var(--text-secondary); margin: 0 0 28px; }
  .legend span { display: inline-flex; align-items: center; gap: 6px; }
  .swatch { width: 11px; height: 11px; border-radius: 3px; display: inline-block; }

  .flow { display: flex; flex-direction: column; align-items: center; }

  .node {
    width: 100%;
    max-width: 460px;
    padding: 12px 18px;
    border-radius: 10px;
    text-align: center;
    font-size: 13.5px;
    line-height: 1.4;
  }
  .node.neutral { background: var(--neutral-fill); border: 1px solid var(--neutral-stroke); color: var(--neutral-text); }
  .node.terminal { background: var(--decision-fill); border: 1px solid var(--decision-stroke); color: #fff; font-weight: 600; border-radius: 999px; }
  .node.decision { background: var(--decision-fill); border: 1px solid var(--decision-stroke); color: #fff; font-weight: 500; }
  .node.retry { background: var(--retry-fill); border: 1px solid var(--retry-stroke); color: var(--retry-text); }
  .node code { font-size: 12.5px; opacity: 0.9; }

  .arrow {
    width: 2px;
    height: 22px;
    background: var(--arrow);
    position: relative;
  }
  .arrow::after {
    content: "";
    position: absolute;
    bottom: -1px;
    left: 50%;
    transform: translateX(-50%);
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 7px solid var(--arrow);
  }
  .arrow.fail { background: var(--arrow-fail); }
  .arrow.fail::after { border-top-color: var(--arrow-fail); }

  .row { display: flex; gap: 16px; width: 100%; max-width: 460px; justify-content: center; }
  .row .node { max-width: none; flex: 1; }

  .choice-row { display: flex; gap: 10px; margin: 10px 0 4px; }
  .choice-btn {
    padding: 6px 18px;
    border-radius: 999px;
    border: 1.5px solid var(--neutral-stroke);
    background: var(--bg);
    color: var(--neutral-text);
    font-size: 12.5px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
  }
  .choice-btn.active {
    background: var(--decision-fill);
    border-color: var(--decision-stroke);
    color: #fff;
  }
  .choice-btn:hover:not(.active) { background: var(--neutral-fill); }

  .branch-body {
    display: flex;
    flex-direction: column;
    align-items: center;
    overflow: hidden;
    max-height: 0;
    opacity: 0;
    transition: max-height 0.35s ease, opacity 0.25s ease;
    width: 100%;
  }
  .branch-body.open { max-height: 2200px; opacity: 1; }

  .placeholder {
    font-size: 12.5px;
    color: var(--text-secondary);
    font-style: italic;
    padding: 8px 0 4px;
  }

  details.error-handling {
    width: 100%;
    max-width: 460px;
    margin: 4px 0 2px;
  }
  details.error-handling summary {
    cursor: pointer;
    font-size: 12px;
    color: var(--retry-text);
    padding: 6px 12px;
    border: 1px dashed var(--retry-stroke);
    border-radius: 8px;
    background: var(--retry-fill);
    list-style: none;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  details.error-handling summary::-webkit-details-marker { display: none; }
  details.error-handling summary::after { content: ""; transition: transform 0.15s; }
  details.error-handling[open] summary::after { transform: rotate(180deg); }
  .error-body { display: flex; flex-direction: column; align-items: center; padding-top: 8px; }

  .divider { height: 1px; background: var(--border); width: 100%; max-width: 460px; margin: 24px 0 16px; }
</style>
<div class="wrap">
  <p class="sub">Click Yes or No to expand the corresponding deployment path.</p>
  <div class="legend">
    <span><i class="swatch" style="background:var(--neutral-fill);border:1px solid var(--neutral-stroke)"></i>Process step</span>
    <span><i class="swatch" style="background:var(--decision-fill)"></i>Decision / start / end</span>
    <span><i class="swatch" style="background:var(--retry-fill);border:1px solid var(--retry-stroke)"></i>Error / retry</span>
  </div>

  <div class="flow">
    <div class="node terminal">Start Omnia deployment</div>
    <div class="arrow"></div>
    <div class="node neutral">Build Omnia images from Omnia artifactory repo</div>
    <div class="arrow"></div>
    <div class="node neutral">Run <code>omnia.sh</code> to create the Omnia core container</div>
    <div class="arrow"></div>
    <div class="node neutral">Update required input files in <code>/opt/omnia/input/project_default</code></div>
    <div class="arrow"></div>
    <div class="row">
      <div class="node neutral">Create PXE mapping file manually</div>
      <div class="node neutral">Generate PXE mapping file via OME-based BMC discovery</div>
    </div>
    <div class="arrow"></div>
    <div class="node neutral">Run input validator to validate the input files</div>
    <div class="arrow"></div>

    <div class="node decision">Use BuildStreaM: catalog-driven build automation?</div>
    <div class="choice-row">
      <button class="choice-btn" id="btn-no" onclick="selectStream('no')">No</button>
      <button class="choice-btn" id="btn-yes" onclick="selectStream('yes')">Yes</button>
    </div>
    <div class="placeholder" id="placeholder">Choose Yes or No above to view that path</div>

    <!-- ===== Branch: No (manual) ===== -->
    <div class="branch-body" id="branch-no">
      <div class="arrow"></div>
      <div class="node neutral">Run <code>prepare_oim.yml</code> to deploy containers on OIM</div>
      <div class="arrow"></div>
      <div class="node neutral">Run <code>local_repo.yml</code> to download packages to the Pulp repo</div>
      <div class="arrow"></div>
      <div class="node neutral">Run <code>build_image_x86_64.yml</code> to build x86_64 diskless images</div>
      <div class="arrow"></div>

      <div class="node decision">aarch64 support required?</div>
      <div class="choice-row">
        <button class="choice-btn" id="btn-no-aarch-no" onclick="selectAarch('no', false)">No</button>
        <button class="choice-btn" id="btn-no-aarch-yes" onclick="selectAarch('no', true)">Yes</button>
      </div>

      <div class="branch-body" id="no-aarch-yes">
        <div class="arrow"></div>
        <div class="node neutral">Install RHEL10 diskfull OS on aarch64 node</div>
        <div class="arrow"></div>
        <div class="node neutral">Run <code>build_image_aarch64.yml</code> to build aarch64 diskless images</div>
      </div>

      <div class="arrow"></div>
      <div class="node neutral">Run <code>provision.yml</code></div>
      <div class="arrow"></div>
      <div class="node neutral">PXE boot nodes to load diskless images from OIM</div>
    </div>

    <!-- ===== Branch: Yes (BuildStreaM) ===== -->
    <div class="branch-body" id="branch-yes">
      <div class="arrow"></div>
      <div class="node decision">aarch64 support required?</div>
      <div class="choice-row">
        <button class="choice-btn" id="btn-yes-aarch-no" onclick="selectAarch('yes', false)">No</button>
        <button class="choice-btn" id="btn-yes-aarch-yes" onclick="selectAarch('yes', true)">Yes</button>
      </div>

      <div class="branch-body" id="yes-aarch-yes">
        <div class="arrow"></div>
        <div class="node neutral">Install RHEL10 diskfull OS on aarch64 node</div>
      </div>

      <div class="arrow"></div>
      <div class="node neutral">Run <code>prepare_oim.yml</code> to deploy the BuildStreaM container + others</div>
      <div class="arrow"></div>
      <div class="node neutral">Run <code>gitlab.yml</code> to deploy the BuildStreaM GitLab instance</div>
      <div class="arrow"></div>
      <div class="node neutral">Update the catalog file on the BuildStreaM GitLab instance</div>
      <div class="arrow"></div>
      <div class="node decision">Trigger the build CI/CD pipeline</div>

      <details class="error-handling">
        <summary>If it fails  debug &amp; retry loop</summary>
        <div class="error-body">
          <div class="arrow fail"></div>
          <div class="node retry">Debug logs &amp; fix the config</div>
          <div class="arrow fail"></div>
          <div class="node retry">Resume &amp; retry failed pipeline</div>
          <div class="arrow fail"></div>
          <div class="node decision" style="opacity:0.6"> back to trigger build</div>
        </div>
      </details>

      <div class="arrow"></div>
      <div class="node neutral">Modify PXE mapping file</div>
      <div class="arrow"></div>
      <div class="node decision">Trigger deploy pipeline (PXE boot)</div>

      <details class="error-handling">
        <summary>If it fails  debug &amp; retry loop</summary>
        <div class="error-body">
          <div class="arrow fail"></div>
          <div class="node retry">Debug logs &amp; fix the config</div>
          <div class="arrow fail"></div>
          <div class="node retry">Resume &amp; retry failed pipeline</div>
          <div class="arrow fail"></div>
          <div class="node decision" style="opacity:0.6"> back to trigger deploy</div>
        </div>
      </details>
    </div>

    <div class="divider"></div>

    <div class="node neutral">Run <code>telemetry.yml</code> to enable iDRAC telemetry</div>
    <div class="arrow"></div>
    <div class="node terminal">End of deployment</div>
  </div>
</div>
</div>

<script>
  function selectStream(choice) {
    document.getElementById('btn-no').classList.toggle('active', choice === 'no');
    document.getElementById('btn-yes').classList.toggle('active', choice === 'yes');
    document.getElementById('branch-no').classList.toggle('open', choice === 'no');
    document.getElementById('branch-yes').classList.toggle('open', choice === 'yes');
    document.getElementById('placeholder').style.display = 'none';
  }
  function selectAarch(branch, isYes) {
    document.getElementById('btn-' + branch + '-aarch-no').classList.toggle('active', !isYes);
    document.getElementById('btn-' + branch + '-aarch-yes').classList.toggle('active', isYes);
    document.getElementById(branch + '-aarch-yes').classList.toggle('open', isYes);
  }
</script>

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
