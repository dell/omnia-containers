# Get Started

## Omnia Deployment Flow
<!-- Omnia Deployment Flow -->

<div class="of-wrap">

<div class="of-root" id="ofRoot">

  <div class="of-hdr">
    <div class="of-h2">Select options to see your deployment path</div>
  </div>

  <div class="of-flow" id="ofFlow"></div>

</div>

<style>
.of-root {
  --c-accent: #2563eb;
  --c-accent-l: #dbeafe;
  --c-border: #bfdbfe;
  --c-green: #16a34a;
  --c-green-l: #dcfce7;
  --c-green-b: #86efac;
  --c-line: #cbd5e1;
  --c-card: #ffffff;
  --c-text: #1e293b;
  --c-muted: #94a3b8;
  --c-sub: #a1a1aa;
  --r: 10px;
  font-family: inherit;
  padding: 1rem 0;
}

.of-hdr { text-align: center; margin-bottom: 1.4rem; }
.of-h1 { font-size: 1.3rem; font-weight: 800; color: var(--c-text); }
.of-h2 { font-size: .78rem; color: var(--c-muted); margin-top: 2px; }

.of-flow {
  display: flex; flex-direction: column; align-items: center;
  gap: 0; max-width: 440px; margin: 0 auto;
}

.of-c { width: 2px; height: 22px; background: var(--c-line); position: relative; }
.of-c::after {
  content: ''; position: absolute; bottom: -4px; left: 50%;
  transform: translateX(-50%);
  border-left: 4px solid transparent; border-right: 4px solid transparent;
  border-top: 5px solid var(--c-line);
}
.of-c.na::after { display: none; }
.of-c.sm { height: 12px; }

.of-pill {
  padding: 7px 28px; border-radius: 50px;
  font-size: .8rem; font-weight: 700;
  background: transparent;
}
.of-pill.s { border: 2px solid var(--c-accent); color: var(--c-accent); }
.of-pill.e { border: 2px solid var(--c-green); color: var(--c-green); }

.of-s {
  background: var(--c-card);
  border-radius: var(--r);
  padding: 11px 16px;
  width: 100%; max-width: 380px;
  text-align: center;
  border: 1.5px solid var(--c-border);
  box-shadow: 0 1px 2px rgba(0,0,0,.05), 0 4px 12px rgba(0,0,0,.06);
}
.of-s:hover {
  box-shadow: 0 2px 4px rgba(0,0,0,.07), 0 8px 20px rgba(0,0,0,.09);
}
.of-s .t { font-size: .8rem; font-weight: 600; color: var(--c-text); line-height: 1.35; }
.of-s .d { font-size: .68rem; color: var(--c-sub); margin-top: 2px; line-height: 1.2; opacity: .6; }
.of-s code {
  background: var(--c-accent-l); color: var(--c-accent);
  padding: 0 4px; border-radius: 3px;
  font-size: .68rem; font-weight: 600;
  font-family: 'SFMono-Regular','Fira Code',monospace;
}
.of-s.bsm { border-color: var(--c-green-b); }
.of-s.bsm code { background: var(--c-green-l); color: #166534; }

.of-d {
  background: var(--c-card);
  border-radius: var(--r);
  padding: 10px 16px;
  width: auto; max-width: 380px;
  border: 1.5px solid var(--c-border);
  box-shadow: 0 1px 2px rgba(0,0,0,.05), 0 4px 12px rgba(0,0,0,.06);
  text-align: center;
}
.of-d .of-dl {
  font-size: .78rem; font-weight: 600; color: var(--c-text);
  white-space: nowrap; margin-bottom: 8px;
}
.of-d .of-do { display: flex; gap: 6px; justify-content: center; }

.of-b {
  padding: 4px 18px; border-radius: 50px;
  border: 1.5px solid #e2e8f0; background: #f8fafc;
  color: var(--c-muted); font-size: .7rem; font-weight: 700;
  cursor: pointer; transition: all .2s; white-space: nowrap;
}
.of-b:hover:not(.a) { border-color: var(--c-accent); color: var(--c-accent); background: #fff; }
.of-b.a { border-color: var(--c-accent); background: var(--c-accent); color: #fff; }

.of-m {
  display: flex; gap: 0; border-radius: 50px;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(0,0,0,.05), 0 4px 12px rgba(0,0,0,.06);
  width: 100%; max-width: 300px;
}
.of-m button {
  flex: 1; padding: 10px 6px; border: none; cursor: pointer;
  font-size: .78rem; font-weight: 700;
  background: #f1f5f9; color: var(--c-muted); transition: all .25s;
}
.of-m button:first-child { border-radius: 50px 0 0 50px; }
.of-m button:last-child  { border-radius: 0 50px 50px 0; }
.of-m button:hover:not(.a) { background: #e2e8f0; }
.of-m button.a.st { background: linear-gradient(135deg,#1e40af,#2563eb); color: #fff; }
.of-m button.a.bs { background: linear-gradient(135deg,#166534,#16a34a); color: #fff; }

.of-m.pulse { animation: ofPulse 1.5s ease-in-out infinite; }
@keyframes ofPulse {
  0%, 100% { box-shadow: 0 1px 2px rgba(0,0,0,.05), 0 4px 12px rgba(0,0,0,.06); }
  50% { box-shadow: 0 0 0 5px rgba(37,99,235,.2), 0 0 20px rgba(37,99,235,.1); }
}

.of-hint {
  font-size: .62rem; font-weight: 400; color: var(--c-accent);
  text-align: center; margin-top: 6px;
  animation: ofHintFade 1.5s ease-in-out infinite;
  opacity: .7;
}
@keyframes ofHintFade {
  0%, 100% { opacity: .7; }
  50% { opacity: 1; }
}

.of-dv {
  width: 100%; max-width: 380px;
  display: flex; align-items: center; gap: 10px;
}
.of-dv::before, .of-dv::after { content: ''; flex: 1; height: 1px; background: #e2e8f0; }
.of-dv span {
  font-size: .58rem; font-weight: 700; color: var(--c-muted);
  text-transform: uppercase; letter-spacing: 1px; white-space: nowrap;
}

.of-new {
  width: 100%;
  display: flex;
  justify-content: center;
  animation: ofReveal .5s cubic-bezier(.22,1,.36,1) both;
}

@keyframes ofReveal {
  from { opacity: 0; transform: translateY(-16px) scaleY(.96); max-height: 0; }
  to   { opacity: 1; transform: translateY(0) scaleY(1); max-height: 200px; }
}

/* ── Dark mode: MkDocs Material toggle ── */
[data-md-color-scheme="slate"] .of-root {
  --c-accent: #60a5fa;
  --c-accent-l: rgba(96,165,250,.15);
  --c-border: rgba(96,165,250,.25);
  --c-green: #4ade80;
  --c-green-l: rgba(74,222,128,.15);
  --c-green-b: rgba(74,222,128,.3);
  --c-line: #475569;
  --c-card: #1e293b;
  --c-text: #e2e8f0;
  --c-muted: #64748b;
  --c-sub: #64748b;
}
[data-md-color-scheme="slate"] .of-m button { background: #334155; color: #94a3b8; }
[data-md-color-scheme="slate"] .of-m button:hover:not(.a) { background: #3e4f65; }
[data-md-color-scheme="slate"] .of-m button.a.st { background: linear-gradient(135deg,#1d4ed8,#3b82f6); }
[data-md-color-scheme="slate"] .of-m button.a.bs { background: linear-gradient(135deg,#15803d,#22c55e); }
[data-md-color-scheme="slate"] .of-b { border-color: #334155; background: #1e293b; color: #64748b; }
[data-md-color-scheme="slate"] .of-b:hover:not(.a) { border-color: #60a5fa; color: #60a5fa; background: #263348; }
[data-md-color-scheme="slate"] .of-b.a { border-color: #60a5fa; background: #60a5fa; color: #0f172a; }
[data-md-color-scheme="slate"] .of-pill.s { border-color: #60a5fa; color: #60a5fa; }
[data-md-color-scheme="slate"] .of-pill.e { border-color: #4ade80; color: #4ade80; }
[data-md-color-scheme="slate"] .of-s code { background: rgba(96,165,250,.15); color: #93bbfc; }
[data-md-color-scheme="slate"] .of-s.bsm code { background: rgba(74,222,128,.15); color: #4ade80; }
[data-md-color-scheme="slate"] .of-hint { color: #60a5fa; }
[data-md-color-scheme="slate"] .of-dv::before,
[data-md-color-scheme="slate"] .of-dv::after { background: #334155; }

/* ── Dark mode: browser preference fallback ── */
@media(prefers-color-scheme: dark){
  body:not([data-md-color-scheme="default"]) .of-root {
    --c-accent: #60a5fa;
    --c-accent-l: rgba(96,165,250,.15);
    --c-border: rgba(96,165,250,.25);
    --c-green: #4ade80;
    --c-green-l: rgba(74,222,128,.15);
    --c-green-b: rgba(74,222,128,.3);
    --c-line: #475569;
    --c-card: #1e293b;
    --c-text: #e2e8f0;
    --c-muted: #64748b;
    --c-sub: #64748b;
  }
  body:not([data-md-color-scheme="default"]) .of-m button { background: #334155; color: #94a3b8; }
  body:not([data-md-color-scheme="default"]) .of-m button:hover:not(.a) { background: #3e4f65; }
  body:not([data-md-color-scheme="default"]) .of-m button.a.st { background: linear-gradient(135deg,#1d4ed8,#3b82f6); }
  body:not([data-md-color-scheme="default"]) .of-m button.a.bs { background: linear-gradient(135deg,#15803d,#22c55e); }
  body:not([data-md-color-scheme="default"]) .of-b { border-color: #334155; background: #1e293b; color: #64748b; }
  body:not([data-md-color-scheme="default"]) .of-b:hover:not(.a) { border-color: #60a5fa; color: #60a5fa; background: #263348; }
  body:not([data-md-color-scheme="default"]) .of-b.a { border-color: #60a5fa; background: #60a5fa; color: #0f172a; }
  body:not([data-md-color-scheme="default"]) .of-pill.s { border-color: #60a5fa; color: #60a5fa; }
  body:not([data-md-color-scheme="default"]) .of-pill.e { border-color: #4ade80; color: #4ade80; }
  body:not([data-md-color-scheme="default"]) .of-s code { background: rgba(96,165,250,.15); color: #93bbfc; }
  body:not([data-md-color-scheme="default"]) .of-s.bsm code { background: rgba(74,222,128,.15); color: #4ade80; }
  body:not([data-md-color-scheme="default"]) .of-hint { color: #60a5fa; }
  body:not([data-md-color-scheme="default"]) .of-dv::before,
  body:not([data-md-color-scheme="default"]) .of-dv::after { background: #334155; }
}

</style>

<script>
(function(){
  const S = { mode:'standard', ome:'no', aarch64:'no' };
  let prevKeys = new Set();
  let isFirst = true;
  let modeClicked = false;

  window._ofs = function(k,v){
    if(k==='mode') modeClicked = true;
    S[k]=v;
    R();
  };

  function R(){
    const parts = [];

    function add(key,html){ parts.push({key,html}); }
    function pill(key,t,c){ add(key,`<div class="of-pill ${c}">${t}</div>`); }
    function cn(key,c=''){ add(key,`<div class="of-c ${c}"></div>`); }
    function st(key,t,d,c=''){ add(key,`<div class="of-s ${c}"><div class="t">${t}</div>${d?`<div class="d">${d}</div>`:''}</div>`); }
    function dec(key,l,opts,stateKey){
      const bs=opts.map(o=>{
        const a=S[stateKey]===o.v?'a':'';
        return `<button class="of-b ${a}" onclick="_ofs('${stateKey}','${o.v}')">${o.l}</button>`;
      }).join('');
      add(key,`<div class="of-d"><div class="of-dl">${l}</div><div class="of-do">${bs}</div></div>`);
    }
    function md(key){
      const sc=S.mode==='standard'?'a st':'';
      const bc=S.mode==='buildstream'?'a bs':'';
      const p=!modeClicked?'pulse':'';
      let html=`<div class="of-m ${p}"><button class="${sc}" onclick="_ofs('mode','standard')">Standard</button><button class="${bc}" onclick="_ofs('mode','buildstream')">BuildStream</button></div>`;
      if(!modeClicked) html+=`<div class="of-hint">Click to switch deployment method ↑</div>`;
      add(key,html);
    }
    function dv(key,t){ add(key,`<div class="of-dv"><span>${t}</span></div>`); }

    pill('start','Start','s');
    cn('c0');
    dv('dv-m','Deployment Method');
    cn('c0a','sm na');
    md('mode');
    cn('c0b');

    st('s-build','Build Omnia Images','<code>omnia-artifactory</code> repo');
    cn('c1');
    st('s-create','Create Omnia Core Container','<code>omnia.sh</code>');
    cn('c2');
    st('s-login','Log in to Core Container','<code>ssh omnia_core</code>');
    cn('c3');
    st('s-input','Update Input Files','<code>/opt/omnia/input/project_default</code>');
    cn('c4');

    dec('d-ome','Discover Devices Using OME?',[
      {l:'No',v:'no'},{l:'Yes',v:'yes'}
    ],'ome');
    cn('c5');

    if(S.ome==='yes'){
      st('s-ome-y','Generate PXE Mapping via OME','<code>discovery.yml</code>');
    } else {
      st('s-ome-n','Create PXE Mapping File Manually','');
    }
    cn('c6');

    if(S.mode==='standard'){
      dv('dv-std','Standard Deployment');
      cn('cs0','sm na');
      st('ss-oim','Deploy Containers on OIM','<code>prepare_oim.yml</code>');
      cn('cs1');
      st('ss-pulp','Download Packages to Pulp Repo','<code>local_repo.yml</code>');
      cn('cs2');
      st('ss-img','Build x86_64 Diskless Images','<code>build_image_x86_64.yml</code>');
      cn('cs3');

      dec('d-arch-s','aarch64 Required?',[
        {l:'No',v:'no'},{l:'Yes',v:'yes'}
      ],'aarch64');
      cn('cs4');

      if(S.aarch64==='yes'){
        st('ss-rhel','Install RHEL10 on aarch64 Node','');
        cn('cs5');
        st('ss-abuild','Build aarch64 Diskless Images','<code>build_image_aarch64.yml</code>');
        cn('cs6');
      }

      st('ss-prov','Provision Nodes','<code>provision.yml</code>');
      cn('cs7');
      st('ss-pxe','PXE Boot Nodes','<code>set_pxe_boot.yml</code>');
    }

    if(S.mode==='buildstream'){
      dv('dv-bsm','BuildStream Catalog-Driven');
      cn('cb0','sm na');

      dec('d-arch-b','aarch64 Required?',[
        {l:'No',v:'no'},{l:'Yes',v:'yes'}
      ],'aarch64');
      cn('cb1');

      if(S.aarch64==='yes'){
        st('sb-rhel','Install RHEL10 on aarch64 Node','','bsm');
        cn('cb2');
      }

      st('sb-oim','Deploy BuildStreamM & Containers on OIM','<code>prepare_oim.yml</code>','bsm');
      cn('cb3');
      st('sb-git','Deploy BuildStreamM GitLab','<code>gitlab.yml</code>','bsm');
      cn('cb4');
      st('sb-cat','Update Catalog on GitLab','','bsm');
      cn('cb5');
      st('sb-ci','Triggers Build Pipeline','','bsm');
      cn('cb6');
      st('sb-pxe','Modify PXE Mapping File','','bsm');
      cn('cb7');
      st('sb-dep','Triggers Deploy Pipeline','','bsm');
    }

    cn('cf0');
    dv('dv-fin','ADD-ON');
    cn('cf1','sm na');
    st('s-telem','Enable iDRAC Telemetry','<code>telemetry.yml</code>');
    cn('cf2');
    pill('end','End','e');

    const newKeys = new Set(parts.map(p=>p.key));
    let delay = 0;

    const html = parts.map(p=>{
      const brandNew = !isFirst && !prevKeys.has(p.key);
      if(brandNew){
        const d = delay * 0.06;
        delay++;
        return `<div class="of-new" style="animation-delay:${d}s">${p.html}</div>`;
      }
      return p.html;
    }).join('');

    prevKeys = newKeys;
    isFirst = false;

    document.getElementById('ofFlow').innerHTML = html;
  }

  R();
})();
</script>

</div>

<!-- End of Omnia Deployment Flow -->

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
